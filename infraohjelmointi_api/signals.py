from datetime import date
import logging
from django.db.models.signals import post_save
from django.db import transaction
from infraohjelmointi_api.models import Project, ClassFinancial, LocationFinancial, ProjectClass, ProjectLocation, TalpaProjectOpening, SapCost, SapCurrentYear
from infraohjelmointi_api.serializers import (
    ProjectClassSerializer,
    ProjectGetSerializer,
    ProjectGroupSerializer,
    ProjectLocationSerializer,
)
from .services import ClassFinancialService, ProjectService, LocationFinancialService
from .services.CacheService import CacheService
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save
from django_eventstream import send_event
from .models import ProjectFinancial, ProjectCategory, ProjectPhase

logger = logging.getLogger("infraohjelmointi_api")



def on_transaction_commit(func):
    def inner(*args, **kwargs):
        transaction.on_commit(lambda: func(*args, **kwargs))

    return inner


def get_financial_sums(
    _type: str,
    instance: ClassFinancial | ProjectFinancial | LocationFinancial,
    finance_year: int,
):
    """
    Returns a dictionary of coordination and planning class instances with financial sum values.
    Related class instances are fetched from the provided financial instance.

        Parameters
        ----------
        instance : ClassFinancial | ProjectFinancial
            Updated Financial instance used to get related classes and calculate financial sums

        finance_year : int
            Start year for the 10 year financial sums

        Returns
        -------
        dict
            {
            "coordination": {
                "masterClass": <ProjectClass instance with sums>,
                "class": <ProjectClass instance with sums>,
                "subClass": <ProjectClass instance with sums>,
                "otherClassification": <ProjectClass instance with sums>,
                "collectiveSubLevel": <ProjectClass instance with sums>,
                "district": <ProjectLocation instance with sums>,
                "subLevelDistrict": <ProjectLocation instance with sums>,
                "group": <ProjectGroup instance with sums>
                },
            "planning": {
                "masterClass": <ProjectClass instance with sums>,
                "class": <ProjectClass instance with sums>,
                "subClass": <ProjectClass instance with sums>,
                "district": <ProjectLocation instance with sums>,
                "group": <ProjectGroup instance with sums>,
                },
            },
            "forcedToFrame": {
                "masterClass": <ProjectClass instance with sums>,
                "class": <ProjectClass instance with sums>,
                "subClass": <ProjectClass instance with sums>,
                "collectiveSubLevel": <ProjectClass instance with sums>,
                "district": <ProjectLocation instance with sums>,
                }
    """

    sums = {
        "coordination": {
            "masterClass": None,
            "class": None,
            "subClass": None,
            "collectiveSubLevel": None,
            "otherClassification": None,
            "district": None,
            "group": None,
        },
        "planning": {
            "masterClass": None,
            "class": None,
            "subClass": None,
            "district": None,
            "group": None,
        },
        "forcedToFrame": {
            "masterClass": None,
            "class": None,
            "subClass": None,
            "collectiveSubLevel": None,
            "otherClassification": None,
            "district": None,
            "group": None,
        },
    }
    if _type == "ProjectFinancial":
        project = instance.project
        forFrameView = instance.forFrameView
        projectRelations = ProjectService.get_project_class_location_group_relations(
            project=project
        )

        for viewType, instances in projectRelations.items():
            if viewType == "planning" and forFrameView == True:
                continue
            for instanceType, instance in instances.items():
                if instance == None:
                    continue
                if instanceType == "group":
                    sums[viewType if forFrameView != True else "forcedToFrame"][
                        instanceType
                    ] = ProjectGroupSerializer(
                        instance,
                        context={
                            "for_coordinator": viewType == "coordination"
                            or forFrameView,
                            "forcedToFrame": forFrameView,
                            "finance_year": finance_year,
                        },
                    ).data

                elif instanceType in ["district"]:
                    sums[viewType if forFrameView != True else "forcedToFrame"][
                        instanceType
                    ] = ProjectLocationSerializer(
                        instance,
                        context={
                            "for_coordinator": viewType == "coordination"
                            or forFrameView,
                            "forcedToFrame": forFrameView,
                            "finance_year": finance_year,
                        },
                    ).data
                else:
                    sums[viewType if forFrameView != True else "forcedToFrame"][
                        instanceType
                    ] = ProjectClassSerializer(
                        instance,
                        context={
                            "for_coordinator": viewType == "coordination"
                            or forFrameView,
                            "forcedToFrame": forFrameView,
                            "finance_year": finance_year,
                        },
                    ).data

    if _type == "ClassFinancial":
        classRelations = ClassFinancialService.get_coordinator_class_and_related_class(
            instance=instance
        )
        forFrameView = instance.forFrameView

        for viewType, classValues in classRelations.items():
            for classType, classInstance in classValues.items():
                if classInstance != None:
                    sums[viewType if forFrameView != True else "forcedToFrame"][classType] = ProjectClassSerializer(
                        classInstance,
                        context={
                            "for_coordinator": viewType == "coordination" or forFrameView,
                            "forcedToFrame": forFrameView,
                            "finance_year": finance_year,
                        },
                    ).data

    if _type == "LocationFinancial":
        locationFinancialRelations = (
            LocationFinancialService.get_coordinator_location_and_related_classes(
                instance=instance
            )
        )
        forFrameView = instance.forFrameView

        for viewType, instances in locationFinancialRelations.items():
            for instanceType, instance in instances.items():
                if instance != None:
                    if instanceType in ["district"]:
                        sums[viewType if forFrameView != True else "forcedToFrame"][instanceType] = ProjectLocationSerializer(
                            instance,
                            context={
                                "for_coordinator": viewType == "coordination" or forFrameView,
                                "forcedToFrame": forFrameView,
                                "finance_year": finance_year,
                            },
                        ).data
                    else:
                        sums[viewType if forFrameView != True else "forcedToFrame"][instanceType] = ProjectClassSerializer(
                            instance,
                            context={
                                "for_coordinator": viewType == "coordination" or forFrameView,
                                "forcedToFrame": forFrameView,
                                "finance_year": finance_year,
                            },
                        ).data

    return sums


@receiver(post_save, sender=ProjectFinancial)
@receiver(post_save, sender=ClassFinancial)
@receiver(post_save, sender=LocationFinancial)
@on_transaction_commit
def get_notified_financial_sums(sender, instance, created, **kwargs):
    """
    Sends a django event stream event with all financial sums effected by a save on ProjectFinancial, ClassFinancial or LocationFinancial table.

        Parameters
        ----------
        sender
            name of the sender table.

        instance : ProjectFinancial | ClassFinancial | LocationFinancial
            instance of the object which triggered the signal

        created : bool
            True if the save was caused by a new row creation, else False
    """
    _type = instance._meta.model.__name__
    if created:
        logger.debug("Signal Triggered: {} Object was created".format(_type))
    logger.debug("Signal Triggered: {} Object was updated".format(_type))
    year = getattr(instance, "finance_year", date.today().year)
    send_event(
        "finance",
        "finance-update",
        get_financial_sums(instance=instance, _type=_type, finance_year=year),
    )


@receiver(post_save, sender=Project)
# Using this decorator below to make sure the function is only fired when the transaction has commited.
# This causes the project instance to have the updated many-to-many fields as the update happens after .save() is called on the Project model
@on_transaction_commit
def get_notified_project(sender, instance, created, update_fields, **kwargs):
    if created:
        logger.debug("Signal Triggered: Project was created")
    else:
        # This comes from partial_update action which is overriden in project view set
        # It gets added to the project instance before .save() is called
        forcedToFrame = getattr(instance, "forcedToFrame", False)
        year = getattr(instance, "finance_year", date.today().year)
        send_event(
            "project",
            "project-update",
            {
                "project": ProjectGetSerializer(
                    instance,
                    context={
                        "get_pw_link": True,
                        "forcedToFrame": forcedToFrame,
                        "for_coordinator": forcedToFrame == True,
                        "finance_year": year,
                    },
                ).data,
            },
        )
        logger.debug("Signal Triggered: Project was updated")


@receiver(post_save, sender=ProjectFinancial)
@receiver(post_delete, sender=ProjectFinancial)
def invalidate_project_financial_cache(sender, instance, **kwargs):
    """
    Invalidate cache when ProjectFinancial is saved or deleted

    This ensures that financial calculations are refreshed when data changes.
    """
    try:
        project = instance.project

        # Invalidate caches for all related entities
        if project.projectClass:
            CacheService.invalidate_financial_sum(
                instance_id=project.projectClass.id,
                instance_type='ProjectClass'
            )
            # Also invalidate parent classes
            parent = project.projectClass.parent
            while parent:
                CacheService.invalidate_financial_sum(
                    instance_id=parent.id,
                    instance_type='ProjectClass'
                )
                parent = parent.parent

        if project.projectLocation:
            CacheService.invalidate_financial_sum(
                instance_id=project.projectLocation.id,
                instance_type='ProjectLocation'
            )
            # Also invalidate parent locations
            parent = project.projectLocation.parent
            while parent:
                CacheService.invalidate_financial_sum(
                    instance_id=parent.id,
                    instance_type='ProjectLocation'
                )
                parent = parent.parent

        if project.projectGroup:
            CacheService.invalidate_financial_sum(
                instance_id=project.projectGroup.id,
                instance_type='ProjectGroup'
            )

    except Exception as e:
        logger.error(f"Error invalidating cache for ProjectFinancial: {e}")


@receiver(post_save, sender=ClassFinancial)
@receiver(post_delete, sender=ClassFinancial)
def invalidate_class_financial_cache(sender, instance, **kwargs):
    """
    Invalidate cache when ClassFinancial is saved or deleted
    """
    try:
        class_relation = instance.classRelation

        # Invalidate cache for this class
        CacheService.invalidate_financial_sum(
            instance_id=class_relation.id,
            instance_type='ProjectClass'
        )

        # Invalidate parent classes
        parent = class_relation.parent
        while parent:
            CacheService.invalidate_financial_sum(
                instance_id=parent.id,
                instance_type='ProjectClass'
            )
            parent = parent.parent

        if class_relation.forCoordinatorOnly:
            planning_classes = ProjectClass.objects.filter(relatedTo=class_relation)
            for planning_class in planning_classes:
                CacheService.invalidate_financial_sum(
                    instance_id=planning_class.id,
                    instance_type='ProjectClass'
                )

        for year_offset in range(-10, 1):
            affected_year = instance.year + year_offset
            if affected_year >= 2000:
                CacheService.invalidate_frame_budgets(year=affected_year)
    except Exception as e:
        logger.error(f"Error invalidating cache for ClassFinancial: {e}")


@receiver(post_save, sender=LocationFinancial)
@receiver(post_delete, sender=LocationFinancial)
def invalidate_location_financial_cache(sender, instance, **kwargs):
    """
    Invalidate cache when LocationFinancial is saved or deleted
    """
    try:
        location_relation = instance.locationRelation

        # Invalidate cache for this location
        CacheService.invalidate_financial_sum(
            instance_id=location_relation.id,
            instance_type='ProjectLocation'
        )

        # Invalidate parent locations
        parent = location_relation.parent
        while parent:
            CacheService.invalidate_financial_sum(
                instance_id=parent.id,
                instance_type='ProjectLocation'
            )
            parent = parent.parent

        if location_relation.forCoordinatorOnly:
            planning_locations = ProjectLocation.objects.filter(relatedTo=location_relation)
            for planning_location in planning_locations:
                CacheService.invalidate_financial_sum(
                    instance_id=planning_location.id,
                    instance_type='ProjectLocation'
                )

        for year_offset in range(-10, 1):
            affected_year = instance.year + year_offset
            if affected_year >= 2000:
                CacheService.invalidate_frame_budgets(year=affected_year)
    except Exception as e:
        logger.error(f"Error invalidating cache for LocationFinancial: {e}")


@receiver(post_save, sender=Project)
def invalidate_project_cache(sender, instance, created, **kwargs):
    """
    Invalidate cache when Project is saved (programmed status or relationships change)
    """
    try:
        # Only invalidate if relevant fields changed
        if created or instance.programmed:
            if instance.projectClass:
                CacheService.invalidate_financial_sum(
                    instance_id=instance.projectClass.id,
                    instance_type='ProjectClass'
                )

            if instance.projectLocation:
                CacheService.invalidate_financial_sum(
                    instance_id=instance.projectLocation.id,
                    instance_type='ProjectLocation'
                )

            if instance.projectGroup:
                CacheService.invalidate_financial_sum(
                    instance_id=instance.projectGroup.id,
                    instance_type='ProjectGroup'
                )

    except Exception as e:
        logger.error(f"Error invalidating cache for Project: {e}")




@receiver(post_save, sender=Project)
@on_transaction_commit
def update_talpa_status_on_sap_project(sender, instance, created, update_fields, **kwargs):
    """
    Automatically update TalpaProjectOpening status to "project_number_opened"
    when sapProject is set on a Project.

    Only updates if:
    1. sapProject actually changed (was None/empty, now has value)
    2. TalpaProjectOpening exists for this project
    3. Current status is "sent_to_talpa" (locked)
    """
    # Only process if sapProject was updated
    if update_fields and "sapProject" not in update_fields:
        return

    # Only process if sapProject is set (not None/empty)
    if not instance.sapProject:
        return

    try:
        talpa_opening = TalpaProjectOpening.objects.get(project=instance)
    except TalpaProjectOpening.DoesNotExist:
        # No Talpa opening for this project, nothing to do
        return

    # Only update if status is "sent_to_talpa" (locked)
    if talpa_opening.status != "sent_to_talpa":
        return

    # Check if sapProject actually changed (was None/empty before)
    # We can't easily check the old value here, so we'll update if status allows it
    # The status check above ensures we only update locked forms

    # Update status to "project_number_opened"
    # Use update() to avoid triggering signals and validation
    TalpaProjectOpening.objects.filter(pk=talpa_opening.pk).update(
        status="project_number_opened"
    )
    logger.info(
        f"TalpaProjectOpening status updated to 'project_number_opened' for project {instance.id} "
        f"(sapProject: {instance.sapProject})"
    )

@receiver(pre_save, sender=Project)
def on_project_phase_change(sender, instance, **kwargs):
    """K1 on construction; suspension fields when entering/leaving suspended."""
    if not instance.phase:
        return

    old_phase_value = None
    if instance.pk:
        try:
            old_instance = Project.objects.get(pk=instance.pk)
            old_phase_value = old_instance.phase.value if old_instance.phase else None
        except Project.DoesNotExist:
            pass

    new_phase_value = instance.phase.value

    if old_phase_value == new_phase_value:
        return

    if new_phase_value == "construction":
        try:
            instance.category = ProjectCategory.objects.get(value="K1")
        except ProjectCategory.DoesNotExist:
            logger.error("ProjectCategory 'K1' does not exist, cannot set category on construction phase change")

    if new_phase_value == "suspended":
        instance.suspendedDate = date.today()
        if old_phase_value:
            instance.suspendedFromPhase = ProjectPhase.objects.filter(
                value=old_phase_value
            ).first()
    elif old_phase_value == "suspended":
        instance.suspendedDate = None
        instance.suspendedFromPhase = None


def _is_valid_sap_project(value: str | None) -> bool:
    """
    Check if a sapProject value is valid (not empty, null, or "0").
    
    IO-777: Users may set sapProject to "0" as a workaround when they can't delete it.
    We treat "0" as an invalid/empty value.
    """
    if value is None:
        return False
    if value.strip() == "":
        return False
    if value.strip() == "0":
        return False
    return True


def _all_subclasses(cls):
    """Yield every (transitive) subclass of ``cls``. Used to discover all
    CachedLookupViewSet subclasses regardless of inheritance depth."""
    for sub in cls.__subclasses__():
        yield sub
        yield from _all_subclasses(sub)


def _invalidate_cached_lookup(sender, **kwargs):
    """Drop the cached list response for ``sender`` after the surrounding
    transaction commits. Deferring to ``on_commit`` avoids a race where a
    concurrent request reads the cache between INVALIDATE and COMMIT and
    re-populates it with the (still-uncommitted, soon-to-be-stale) value.
    """
    transaction.on_commit(lambda: CacheService.invalidate_lookup(sender.__name__))


def _connect_cached_lookup_invalidation():
    """Wire post_save/post_delete on every CachedLookupViewSet model so that
    direct ORM mutations (Django shell, admin, management commands, bulk
    imports) also invalidate the lookup cache.

    Without this, only ViewSet-driven mutations refresh the cache and
    out-of-band edits stay invisible until the 12 h TTL expires.
    Caveat: queryset-level ``.update()`` / ``.delete()`` bypass these signals
    by design — those callsites must invalidate explicitly.
    """
    # Force-import the views package so every CachedLookupViewSet subclass is
    # registered before we walk subclasses.
    from infraohjelmointi_api import views  # noqa: F401
    from infraohjelmointi_api.views.CachedLookupViewSet import CachedLookupViewSet

    seen_models = set()
    for viewset_cls in _all_subclasses(CachedLookupViewSet):
        try:
            model = viewset_cls.serializer_class.Meta.model
        except AttributeError:
            continue
        if model in seen_models:
            continue
        seen_models.add(model)
        post_save.connect(
            _invalidate_cached_lookup,
            sender=model,
            dispatch_uid=f"cached_lookup_invalidate_save_{model.__name__}",
            weak=False,
        )
        post_delete.connect(
            _invalidate_cached_lookup,
            sender=model,
            dispatch_uid=f"cached_lookup_invalidate_delete_{model.__name__}",
            weak=False,
        )


_connect_cached_lookup_invalidation()


@receiver(pre_save, sender=Project)
def capture_old_sap_project(sender, instance, **kwargs):
    """
    Capture the old sapProject value before save so we can detect changes.
    
    IO-777: This is needed to clean up SAP cost records when sapProject changes.
    """
    if instance.pk:
        try:
            old_instance = Project.objects.get(pk=instance.pk)
            instance._old_sap_project = old_instance.sapProject
        except Project.DoesNotExist:
            instance._old_sap_project = None
    else:
        instance._old_sap_project = None


@receiver(post_save, sender=Project)
def cleanup_sap_costs_on_sap_project_change(sender, instance, created, **kwargs):
    """
    Delete SapCost and SapCurrentYear records when sapProject is changed or removed.
    
    IO-777: When a project's sapProject number is changed, the old SAP cost records
    become stale (they contain data from the old SAP project number) and should be
    deleted. New records will be created on the next SAP sync if the new sapProject
    is valid.
    
    Scenarios handled:
    - sapProject changed from valid value to null/empty/"0" -> delete records
    - sapProject changed from one valid value to another -> delete records
    - sapProject unchanged -> do nothing
    - sapProject set from null to valid value -> do nothing (no records to delete)
    """
    if created:
        # New project, no old records to clean up
        return
    
    old_sap_project = getattr(instance, '_old_sap_project', None)
    new_sap_project = instance.sapProject
    
    # Check if sapProject actually changed
    old_valid = _is_valid_sap_project(old_sap_project)
    new_valid = _is_valid_sap_project(new_sap_project)
    
    # If old value was valid and either:
    # 1. New value is invalid (removed/cleared)
    # 2. New value is different (changed to another project number)
    # Then we should delete the old SAP cost records
    if old_valid and (not new_valid or old_sap_project != new_sap_project):
        deleted_sap_cost = SapCost.objects.filter(project=instance).delete()
        deleted_sap_current_year = SapCurrentYear.objects.filter(project=instance).delete()
        
        logger.info(
            f"Cleaned up SAP cost records for project {instance.id} due to sapProject change "
            f"from '{old_sap_project}' to '{new_sap_project}': "
            f"deleted {deleted_sap_cost[0]} SapCost records, "
            f"{deleted_sap_current_year[0]} SapCurrentYear records"
        )
