from django.db import migrations

# Fix for migration 0113_add_service_tunnel_classes: it defined
# COORDINATOR_CLASS_PATH/COORDINATOR_SUB_CLASS_PATH identical to
# CLASS_PATH/SUB_CLASS_PATH (same master class name, same class names), so its
# get_or_create(path=...) calls for the "coordinator" rows just matched the
# already-created programmer-view rows and returned them as-is. No
# forCoordinatorOnly=True rows were ever created, so the coordinator/forced-
# to-frame views and reports (which only read forCoordinatorOnly=True
# classes) never showed the new class, even though it works fine in
# programmer-view selects.
MASTER_CLASS_NAME = "8 10 Suuret liikennehankkeet"

CLASS_NAME = "8 10 05 Keskustan huoltotunnelin jatke"
SUB_CLASS_NAME = "8 10 05 01 Keskustan huoltotunnelin jatke"

CLASS_PATH = f"{MASTER_CLASS_NAME}/{CLASS_NAME}"
SUB_CLASS_PATH = f"{CLASS_PATH}/{SUB_CLASS_NAME}"


def add_missing_coordinator_classes(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    master_class = project_class_model.objects.filter(
        name=MASTER_CLASS_NAME, forCoordinatorOnly=False
    ).first()
    if not master_class:
        return

    # The real coordinator-view master class is a separate row, linked via
    # relatedTo (reverse accessor "coordinatorClass"), typically named the
    # same but with a TA-kohta suffix, e.g. "..., Kylkn käytettäväksi".
    coordinator_master = project_class_model.objects.filter(
        relatedTo=master_class, forCoordinatorOnly=True
    ).first()
    if not coordinator_master:
        return

    new_class = project_class_model.objects.filter(
        path=CLASS_PATH, forCoordinatorOnly=False
    ).first()
    if not new_class:
        return

    sub_class = project_class_model.objects.filter(
        path=SUB_CLASS_PATH, forCoordinatorOnly=False
    ).first()

    if project_class_model.objects.filter(relatedTo=new_class).exists():
        coordinator_class = project_class_model.objects.get(relatedTo=new_class)
    else:
        coordinator_class, _ = project_class_model.objects.get_or_create(
            path=f"{coordinator_master.path}/{CLASS_NAME}",
            forCoordinatorOnly=True,
            defaults={
                "name": CLASS_NAME,
                "parent": coordinator_master,
                "relatedTo": new_class,
                "relatedLocation": None,
                "defaultProgrammer": None,
            },
        )

    if sub_class and not project_class_model.objects.filter(relatedTo=sub_class).exists():
        project_class_model.objects.get_or_create(
            path=f"{coordinator_class.path}/{SUB_CLASS_NAME}",
            forCoordinatorOnly=True,
            defaults={
                "name": SUB_CLASS_NAME,
                "parent": coordinator_class,
                "relatedTo": sub_class,
                "relatedLocation": None,
                "defaultProgrammer": None,
            },
        )


def remove_missing_coordinator_classes(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    project_class_model.objects.filter(
        forCoordinatorOnly=True, name=SUB_CLASS_NAME
    ).delete()
    project_class_model.objects.filter(
        forCoordinatorOnly=True, name=CLASS_NAME
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0115_merge_20260825_1304"),
    ]

    operations = [
        migrations.RunPython(
            add_missing_coordinator_classes,
            remove_missing_coordinator_classes,
        ),
    ]
