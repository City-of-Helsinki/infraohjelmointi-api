from django.db import migrations


MASTER_CLASS_NAME = "8 10 Suuret liikennehankkeet"
CLASS_NAME = "8 10 06 Suuret liikennehankkeet, kohdentamattomat"


def add_unallocated_major_transport_class(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    master_class = project_class_model.objects.filter(
        name=MASTER_CLASS_NAME, forCoordinatorOnly=False
    ).first()
    if not master_class or not master_class.path:
        return

    coordinator_master = project_class_model.objects.filter(
        relatedTo=master_class, forCoordinatorOnly=True
    ).first()
    if not coordinator_master or not coordinator_master.path:
        return

    project_path = f"{master_class.path}/{CLASS_NAME}"
    project_class, _ = project_class_model.objects.get_or_create(
        path=project_path,
        defaults={
            "name": CLASS_NAME,
            "parent": master_class,
            "forCoordinatorOnly": False,
            "relatedTo": None,
            "relatedLocation": None,
            "defaultProgrammer": None,
        },
    )

    coordinator_path = f"{coordinator_master.path}/{CLASS_NAME}"
    project_class_model.objects.get_or_create(
        path=coordinator_path,
        defaults={
            "name": CLASS_NAME,
            "parent": coordinator_master,
            "forCoordinatorOnly": True,
            "relatedTo": project_class,
            "relatedLocation": None,
            "defaultProgrammer": None,
        },
    )


def remove_unallocated_major_transport_class(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    project_class = project_class_model.objects.filter(
        name=CLASS_NAME,
        parent__name=MASTER_CLASS_NAME,
        forCoordinatorOnly=False,
    ).first()
    if project_class is None:
        return

    project_class_model.objects.filter(
        relatedTo=project_class,
        forCoordinatorOnly=True,
    ).delete()
    project_class.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0126_fix_itakeskus_coordinator_paths"),
    ]

    operations = [
        migrations.RunPython(
            add_unallocated_major_transport_class,
            remove_unallocated_major_transport_class,
        ),
    ]
