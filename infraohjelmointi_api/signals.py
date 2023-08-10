import logging
from django.db.models.signals import post_save, m2m_changed
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectGroup,
    ProjectLocation,
    ClassFinancial,
)
from infraohjelmointi_api.serializers import (
    ProjectClassSerializer,
    ProjectGetSerializer,
    ProjectGroupSerializer,
    ProjectLocationSerializer,
)
from .models import ProjectFinancial
from django.dispatch import receiver
from django_eventstream import send_event

logger = logging.getLogger("infraohjelmointi_api")


def on_transaction_commit(func):
    def inner(*args, **kwargs):
        transaction.on_commit(lambda: func(*args, **kwargs))

    return inner


def get_project_class_location_group_relations(project: Project) -> tuple:
    """
    get all levels of class/location and group relations linked to the provided project

    :arg Project | None project: project instance to get related information from
    """

    projectMasterClass = (
        (
            project.projectClass
            if project.projectClass.parent is None
            else project.projectClass.parent
            if project.projectClass.parent.parent is None
            and project.projectClass.parent is not None
            else project.projectClass.parent.parent
            if project.projectClass.parent.parent is not None
            and project.projectClass.parent is not None
            else None
        )
        if project.projectClass is not None
        else None
    )
    projectClass = (
        (
            project.projectClass
            if project.projectClass.parent is not None
            and project.projectClass.parent.parent is None
            else project.projectClass.parent
            if project.projectClass.parent is not None
            and project.projectClass.parent.parent is not None
            else None
        )
        if project.projectClass is not None
        else None
    )
    projectSubClass = (
        (
            project.projectClass
            if project.projectClass.parent is not None
            and project.projectClass.parent.parent is not None
            else None
        )
        if project.projectClass is not None
        else None
    )
    projectDistrict = (
        (
            project.projectLocation
            if project.projectLocation.parent is None
            else project.projectLocation.parent
            if project.projectLocation.parent.parent is None
            and project.projectLocation.parent is not None
            else project.projectLocation.parent.parent
            if project.projectLocation.parent.parent is not None
            and project.projectLocation.parent is not None
            else None
        )
        if project.projectLocation is not None
        else None
    )

    projectGroup = project.projectGroup if project.projectGroup is not None else None

    return (
        projectMasterClass,
        projectClass,
        projectSubClass,
        projectDistrict,
        projectGroup,
    )


def get_coordinator_class_and_related_class_sums(instance: ClassFinancial):
    """
    get sums for coordination class and the related planning class
    """
    coordinatorClassInstance: ProjectClass = instance.classRelation
    relatedPlanningClassInstance: ProjectClass | None = instance.classRelation.relatedTo

    coordinatorClassIdentification = {
        "masterClass": coordinatorClassInstance.parent == None,
        "class": (
            coordinatorClassInstance.parent != None
            and coordinatorClassInstance.parent.parent == None
        ),
        "subClass": (
            coordinatorClassInstance.parent != None
            and coordinatorClassInstance.parent.parent != None
            and coordinatorClassInstance.parent.parent.parent == None
        ),
    }

    planningClassIdentification = {
        "masterClass": (
            relatedPlanningClassInstance != None
            and relatedPlanningClassInstance.parent == None
        ),
        "class": (
            relatedPlanningClassInstance != None
            and relatedPlanningClassInstance.parent != None
            and relatedPlanningClassInstance.parent.parent == None
        ),
        "subClass": (
            relatedPlanningClassInstance != None
            and relatedPlanningClassInstance.parent != None
            and relatedPlanningClassInstance.parent.parent != None
            and relatedPlanningClassInstance.parent.parent.parent == None
        ),
    }

    return {
        "coordination": {
            classType: ProjectClassSerializer(
                coordinatorClassInstance, context={"for_coordinator": True}
            ).data
            for classType, isInstanceOfClassType in coordinatorClassIdentification.items()
            if isInstanceOfClassType == True
        },
        "planning": {
            classType: ProjectClassSerializer(
                relatedPlanningClassInstance, context={"for_coordinator": False}
            ).data
            for classType, isInstanceOfClassType in planningClassIdentification.items()
            if isInstanceOfClassType == True
        },
    }


def get_financial_sums(
    _type: str,
    instance: ClassFinancial | ProjectFinancial,
):
    """
    Get class/location financial sums for both coordinator and planning
    """

    sums = {
        "coordination": {
            "masterClass": None,
            "class": None,
            "subClass": None,
            "district": None,
        },
        "planning": {
            "masterClass": None,
            "class": None,
            "subClass": None,
            "district": None,
            "group": None,
        },
    }
    if _type == "ProjectFinancial":
        project = instance.project
        (
            pMasterClass,
            pClass,
            pSubClass,
            pDistrict,
            pGroup,
        ) = get_project_class_location_group_relations(project=project)

        if pMasterClass:
            sums["planning"]["masterClass"] = ProjectClassSerializer(pMasterClass).data
            sums["coordination"]["masterClass"] = (
                ProjectClassSerializer(
                    pMasterClass.coordinatorClass, context={"for_coordinator": True}
                ).data
                if hasattr(pMasterClass, "coordinatorClass")
                else None
            )

        if pClass:
            sums["planning"]["class"] = ProjectClassSerializer(pClass).data
            sums["coordination"]["class"] = (
                ProjectClassSerializer(
                    pClass.coordinatorClass, context={"for_coordinator": True}
                ).data
                if hasattr(pClass, "coordinatorClass")
                else None
            )
        if pSubClass:
            sums["planning"]["subClass"] = ProjectClassSerializer(pSubClass).data
            sums["coordination"]["subClass"] = (
                ProjectClassSerializer(
                    pSubClass.coordinatorClass, context={"for_coordinator": True}
                ).data
                if hasattr(pSubClass, "coordinatorClass")
                else None
            )
        if pGroup:
            sums["planning"]["group"] = ProjectGroupSerializer(pGroup).data
        if pDistrict:
            sums["planning"]["district"] = ProjectLocationSerializer(pDistrict).data
            sums["coordination"]["district"] = (
                ProjectClassSerializer(
                    pDistrict.coordinatorLocation, context={"for_coordinator": True}
                ).data
                if hasattr(pDistrict, "coordinatorLocation")
                else None
            )

    if _type == "ClassFinancial":
        classSums = get_coordinator_class_and_related_class_sums(instance=instance)
        for sumType, sumValues in classSums.items():
            for classType, classSum in sumValues.items():
                sums[sumType][classType] = classSum

    return sums


@receiver(post_save, sender=ProjectFinancial)
@receiver(post_save, sender=ClassFinancial)
def get_notified_financial_sums(sender, instance, created, **kwargs):
    _type = instance._meta.model.__name__
    if created:
        logger.debug("Signal Triggered: {} Object was created".format(_type))
    logger.debug("Signal Triggered: {} Object was updated".format(_type))

    send_event(
        "finance",
        "finance-update",
        get_financial_sums(instance=instance, _type=_type),
    )


@receiver(post_save, sender=Project)
# Using this decorator below to make sure the function is only fired when the transaction has commited.
# This causes the project instance to have the updated many-to-many fields as the update happens after .save() is called on the Project model
@on_transaction_commit
def get_notified_project(sender, instance, created, update_fields, **kwargs):
    if created:
        logger.debug("Signal Triggered: Project was created")
    else:
        send_event(
            "project",
            "project-update",
            {
                "project": ProjectGetSerializer(
                    instance, context={"get_pw_link": True}
                ).data,
            },
        )
        logger.debug("Signal Triggered: Project was updated")


# @receiver(post_save, sender=ClassFinancial)
# def get_notified_class_financial(sender, instance, created, update_fields, **kwargs):
#     if created:
#         logger.debug("Signal Triggered: Class Financial instance was created")

#     logger.debug("Signal Triggered: Class Financial instance was updated")
#     send_event(
#         "finance", "class-finance-update", get_class_financials(instance=instance)
#     )
