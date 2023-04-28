from django.db.models.signals import post_save
from .models import ProjectFinancial
from django.dispatch import receiver
from django_eventstream import send_event


@receiver(post_save, sender=ProjectFinancial)
def get_notified(sender, instance, created, **kwargs):
    project = instance.project
    projectMasterClass = (
        project.projectClass.id
        if project.projectClass.parent is None
        else project.projectClass.parent.id
        if project.projectClass.parent.parent is None
        and project.projectClass.parent is not None
        else project.projectClass.parent.parent.id
        if project.projectClass.parent.parent is not None
        and project.projectClass.parent is not None
        else None
    )
    projectClass = (
        project.projectClass.id
        if project.projectClass.parent is not None
        and project.projectClass.parent.parent is None
        else project.projectClass.parent.id
        if project.projectClass.parent is not None
        and project.projectClass.parent.parent is not None
        else None
    )
    projectSubClass = (
        project.projectClass.id
        if project.projectClass.parent is not None
        and project.projectClass.parent.parent is not None
        else None
    )
    projectDistrict = (
        project.projectLocation.id
        if project.projectLocation.parent is None
        else project.projectLocation.parent.id
        if project.projectLocation.parent.parent is None
        and project.projectLocation.parent is not None
        else project.projectLocation.parent.parent.id
        if project.projectLocation.parent.parent is not None
        and project.projectLocation.parent is not None
        else None
    )

    projectGroup = project.projectGroup.id if project.projectGroup is not None else None

    if created:
        print("Signal Triggered: ProjectFinance Object was created")
    else:
        send_event(
            "finance",
            "finance_update",
            {
                "project": instance.project.id,
                "masterClass": projectMasterClass,
                "class": projectClass,
                "subClass": projectSubClass,
                "district": projectDistrict,
                "group": projectGroup,
            },
        )
        print("Signal Triggered: ProjectFinance Object was updated")
