from datetime import date
import logging
from django.db.models.signals import post_save
from django.db import transaction
from infraohjelmointi_api.models import Project, ClassFinancial, LocationFinancial, ProjectClass, ProjectLocation, TalpaProjectOpening
from infraohjelmointi_api.serializers import (
    ProjectClassSerializer,
    ProjectGetSerializer,
    ProjectGroupSerializer,
    ProjectLocationSerializer,
)
from .services import ClassFinancialService, ProjectService, LocationFinancialService
from .services.CacheService import CacheService
from .models import ProjectFinancial
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django_eventstream import send_event

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

        for viewType, classValues in classRelations.items():
            for classType, classInstance in classValues.items():
                if classInstance != None:
                    sums[viewType][classType] = ProjectClassSerializer(
                        classInstance,
                        context={
                            "for_coordinator": viewType == "coordination",
                            "finance_year": finance_year,
                        },
                    ).data

    if _type == "LocationFinancial":
        locationFinancialRelations = (
            LocationFinancialService.get_coordinator_location_and_related_classes(
                instance=instance
            )
        )

        for viewType, instances in locationFinancialRelations.items():
            for instanceType, instance in instances.items():
                if instance != None:
                    if instanceType in ["district"]:
                        sums[viewType][instanceType] = ProjectLocationSerializer(
                            instance,
                            context={
                                "for_coordinator": viewType == "coordination",
                                "finance_year": finance_year,
                            },
                        ).data
                    else:
                        sums[viewType][instanceType] = ProjectClassSerializer(
                            instance,
                            context={
                                "for_coordinator": viewType == "coordination",
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
