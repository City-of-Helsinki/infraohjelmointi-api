from django.db.models.signals import post_save

from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectGroup,
    ProjectLocation,
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


def get_sums(
    projectMasterClass: ProjectClass,
    projectClass: ProjectClass,
    projectSubClass: ProjectClass,
    projectDistrict: ProjectLocation,
    projectGroup: ProjectGroup,
):
    sums = {
        "masterClass": None,
        "class": None,
        "subClass": None,
        "district": None,
        "group": None,
    }
    if projectMasterClass:
        sums["masterClass"] = ProjectClassSerializer(projectMasterClass).data
    if projectClass:
        sums["class"] = ProjectClassSerializer(projectClass).data
    if projectSubClass:
        sums["subClass"] = ProjectClassSerializer(projectSubClass).data
    if projectGroup:
        sums["group"] = ProjectGroupSerializer(projectGroup).data
    if projectDistrict:
        sums["district"] = ProjectLocationSerializer(projectDistrict).data

    return sums


@receiver(post_save, sender=ProjectFinancial)
def get_notified_project_financial(sender, instance, created, **kwargs):
    project = instance.project

    if created:
        print("Signal Triggered: ProjectFinance Object was created")
    else:
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

        projectGroup = (
            project.projectGroup if project.projectGroup is not None else None
        )
        send_event(
            "finance",
            "finance-update",
            {
                "project": instance.project.id,
                **get_sums(
                    projectMasterClass=projectMasterClass,
                    projectClass=projectClass,
                    projectSubClass=projectSubClass,
                    projectDistrict=projectDistrict,
                    projectGroup=projectGroup,
                ),
            },
        )
        print("Signal Triggered: ProjectFinance Object was updated")


@receiver(post_save, sender=Project)
def get_notified_project(sender, instance, created, **kwargs):
    if created:
        print("Signal Triggered: Project was created")
    else:
        send_event(
            "project",
            "project-update",
            {
                "project": ProjectGetSerializer(instance).data,
            },
        )
        print("Signal Triggered: Project was updated")
