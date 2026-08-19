from django.db import migrations


MASTER_CLASS_NAME = "8 10 Suuret liikennehankkeet"
MASTER_CLASS_PATH_ROOT = "8 10"

CLASS_NAME = "8 10 05 Keskustan huoltotunnelin jatke"
CLASS_PATH = f"{MASTER_CLASS_NAME}/{CLASS_NAME}"

SUB_CLASS_NAME = "8 10 05 01 Keskustan huoltotunnelin jatke"
SUB_CLASS_PATH = f"{CLASS_PATH}/{SUB_CLASS_NAME}"

ALL_PATHS = [CLASS_PATH, SUB_CLASS_PATH]


def _get_parent(project_class_model, parent_name):
    # Some test/partial environments may not contain the full base ProjectClass tree.
    # Missing parents are handled by skipping dependent inserts in this migration.
    return project_class_model.objects.filter(
        name=parent_name,
        path__startswith=MASTER_CLASS_PATH_ROOT,
    ).first()


def add_service_tunnel_classes(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    master_class = _get_parent(project_class_model, MASTER_CLASS_NAME)
    if not master_class:
        return

    new_class, _ = project_class_model.objects.get_or_create(
        path=CLASS_PATH,
        defaults={
            "name": CLASS_NAME,
            "parent": master_class,
            "forCoordinatorOnly": False,
            "relatedTo": None,
            "relatedLocation": None,
            "defaultProgrammer": None,
        },
    )

    project_class_model.objects.get_or_create(
        path=SUB_CLASS_PATH,
        defaults={
            "name": SUB_CLASS_NAME,
            "parent": new_class,
            "forCoordinatorOnly": False,
            "relatedTo": None,
            "relatedLocation": None,
            "defaultProgrammer": None,
        },
    )


def remove_service_tunnel_classes(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")
    project_class_model.objects.filter(path__in=ALL_PATHS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0112_merge_20260818_1320"),
    ]

    operations = [
        migrations.RunPython(
            add_service_tunnel_classes,
            remove_service_tunnel_classes,
        ),
    ]