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
from .services import ProjectClassService, ClassFinancialService, ProjectService
from .models import ProjectFinancial
from django.dispatch import receiver
from django_eventstream import send_event

logger = logging.getLogger("infraohjelmointi_api")


def on_transaction_commit(func):
    def inner(*args, **kwargs):
        transaction.on_commit(lambda: func(*args, **kwargs))

    return inner


def get_financial_sums(
    _type: str,
    instance: ClassFinancial | ProjectFinancial,
):
    """
    Returns a dictionary of coordination and planning class instances with financial sum values.
    Related class instances are fetched from the provided financial instance.

        Parameters
        ----------
        instance : ClassFinancial | ProjectFinancial
            Updated Financial instance used to get related classes and calculate financial sums

        Returns
        -------
        dict
            {
            "coordination": {
                "masterClass": <ProjectClass instance with sums>,
                "class": <ProjectClass instance with sums>,
                "subClass": <ProjectClass instance with sums>,
                "collectiveSubLevel": <ProjectClass instance with sums>,
                "district": <ProjectLocation instance with sums>,
                },
            "planning": {
                "masterClass": <ProjectClass instance with sums>,
                "class": <ProjectClass instance with sums>,
                "subClass": <ProjectClass instance with sums>,
                "district": <ProjectLocation instance with sums>,
                "group": <ProjectGroup instance with sums>,
                },
            }
    """

    sums = {
        "coordination": {
            "masterClass": None,
            "class": None,
            "subClass": None,
            "collectiveSubLevel": None,
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
        projectRelations = ProjectService.get_project_class_location_group_relations(
            project=project
        )

        if projectRelations["planning"]["subClass"]:
            sums["planning"]["subClass"] = ProjectClassSerializer(
                projectRelations["planning"]["subClass"]
            ).data

        if projectRelations["planning"]["class"]:
            sums["planning"]["class"] = ProjectClassSerializer(
                projectRelations["planning"]["class"]
            ).data

        if projectRelations["planning"]["masterClass"]:
            sums["planning"]["masterClass"] = ProjectClassSerializer(
                projectRelations["planning"]["masterClass"]
            ).data

        if projectRelations["planning"]["group"]:
            sums["planning"]["group"] = ProjectGroupSerializer(
                projectRelations["planning"]["group"]
            ).data

        if projectRelations["planning"]["district"]:
            sums["planning"]["district"] = ProjectLocationSerializer(
                projectRelations["planning"]["district"]
            ).data

        if projectRelations["coordination"]["district"]:
            sums["coordination"]["district"] = ProjectLocationSerializer(
                projectRelations["coordination"]["district"],
                context={"for_coordinator": True},
            ).data

        if projectRelations["coordination"]["masterClass"]:
            sums["coordination"]["masterClass"] = ProjectClassSerializer(
                projectRelations["coordination"]["masterClass"],
                context={"for_coordinator": True},
            ).data

        if projectRelations["coordination"]["class"]:
            sums["coordination"]["class"] = ProjectClassSerializer(
                projectRelations["coordination"]["class"],
                context={"for_coordinator": True},
            ).data

        if projectRelations["coordination"]["subClass"]:
            sums["coordination"]["subClass"] = ProjectClassSerializer(
                projectRelations["coordination"]["subClass"],
                context={"for_coordinator": True},
            ).data

        if projectRelations["coordination"]["collectiveSubLevel"]:
            sums["coordination"]["collectiveSubLevel"] = ProjectClassSerializer(
                projectRelations["coordination"]["collectiveSubLevel"],
                context={"for_coordinator": True},
            ).data

    if _type == "ClassFinancial":
        classSums = ClassFinancialService.get_coordinator_class_and_related_class_sums(
            instance=instance
        )
        for sumType, sumValues in classSums.items():
            for classType, classSum in sumValues.items():
                sums[sumType][classType] = classSum

    return sums


@receiver(post_save, sender=ProjectFinancial)
@receiver(post_save, sender=ClassFinancial)
def get_notified_financial_sums(sender, instance, created, **kwargs):
    """
    Sends a django event stream event with all financial sums effected by a save on ProjectFinancial or ClassFinancial table.

        Parameters
        ----------
        sender
            name of the sender table.

        instance : ProjectFinancial | ClassFinancial
            instance of the object which triggered the signal

        created : bool
            True if the save was caused by a new row creation, else False
    """
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
