from django.db import migrations


PLANNING_ROWS = [
    {
        "name": "Itäkeskus",
        "parentName": "Esirakentaminen",
        "path": "8 08 Projektialueiden infrarakentaminen/Esirakentaminen/Itäkeskus",
        "forCoordinatorOnly": False,
        "key": "esirakentaminen",
    },
    {
        "name": "Itäkeskus",
        "path": "8 08 Projektialueiden infrarakentaminen/Kadut/Itäkeskus",
        "parentName": "Kadut",
        "forCoordinatorOnly": False,
        "key": "kadut",
    },
    {
        "name": "Itäkeskus",
        "path": "8 08 Projektialueiden infrarakentaminen/Puistot ja liikunta-alueet/Itäkeskus",
        "parentName": "Puistot ja liikunta-alueet",
        "forCoordinatorOnly": False,
        "key": "puistot",
    },
]

COORDINATOR_ROWS = [
    {
        "name": "8 08 01 12 Itäkeskus",
        "path": "8 08 Projektialueiden infrarakentaminen/8 08 01 Esirakentaminen/8 08 01 12 Itäkeskus",
        "parentName": "8 08 01 Esirakentaminen",
        "forCoordinatorOnly": True,
        "planning_key": "esirakentaminen",
    },
    {
        "name": "8 08 02 12 Itäkeskus",
        "path": "8 08 Projektialueiden infrarakentaminen/8 08 02 Kadut/8 08 02 12 Itäkeskus",
        "parentName": "8 08 02 Kadut",
        "forCoordinatorOnly": True,
        "planning_key": "kadut",
    },
    {
        "name": "8 08 03 12 Itäkeskus",
        "path": "8 08 Projektialueiden infrarakentaminen/8 08 03 Puistot ja liikunta-alueet/8 08 03 12 Itäkeskus",
        "parentName": "8 08 03 Puistot ja liikunta-alueet",
        "forCoordinatorOnly": True,
        "planning_key": "puistot",
    },
]

ALL_PATHS = [row["path"] for row in PLANNING_ROWS + COORDINATOR_ROWS]


def _get_parent(project_class_model, parent_name):
    # Some test/partial environments may not contain the full base ProjectClass tree.
    # Missing parents are handled by skipping dependent inserts in this migration.
    path_root_digits = "8 08"
    parent = project_class_model.objects.filter(
        name=parent_name,
        path__startswith=f"{path_root_digits}",
    ).first()
    return parent


def add_itakeskus_project_classes(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    planning_by_key = {}

    for row in PLANNING_ROWS:
        parent = _get_parent(project_class_model, row["parentName"])
        if not parent:
            continue

        planning_row, _ = project_class_model.objects.get_or_create(
            path=row["path"],
            defaults={
                "name": row["name"],
                "parent": parent,
                "forCoordinatorOnly": row["forCoordinatorOnly"],
                "relatedTo": None,
                "relatedLocation": None,
                "defaultProgrammer": None,
            },
        )
        planning_by_key[row["key"]] = planning_row

    for row in COORDINATOR_ROWS:
        parent = _get_parent(project_class_model, row["parentName"])
        if not parent:
            continue

        related_to = planning_by_key.get(row["planning_key"])
        if not related_to:
            continue

        existing_relation = project_class_model.objects.filter(relatedTo=related_to)
        existing_relation = existing_relation.exclude(path=row["path"])
        if existing_relation.exists():
            raise RuntimeError(
                f"ProjectClass relatedTo already used for path {related_to.path}"
            )

        project_class_model.objects.get_or_create(
            path=row["path"],
            defaults={
                "name": row["name"],
                "parent": parent,
                "forCoordinatorOnly": row["forCoordinatorOnly"],
                "relatedTo": related_to,
                "relatedLocation": None,
                "defaultProgrammer": None,
            },
        )


def remove_itakeskus_project_classes(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")
    project_class_model.objects.filter(path__in=ALL_PATHS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0091_project_priority_default"),
    ]

    operations = [
        migrations.RunPython(
            add_itakeskus_project_classes,
            remove_itakeskus_project_classes,
        ),
    ]
