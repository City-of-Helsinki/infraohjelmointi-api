from django.db import migrations
import uuid


def add_project_type_qualifiers(apps, schema_editor):
    ProjectTypeQualifier = apps.get_model("infraohjelmointi_api", "ProjectTypeQualifier")
    values = [
        "street",
        "park",
        "preConstruction",
        "sports",
        "spesialtyStructures",
    ]
    existing = set(
        ProjectTypeQualifier.objects.filter(value__in=values).values_list("value", flat=True)
    )
    objs = []
    for value in values:
        if value in existing:
            continue
        objs.append(
            ProjectTypeQualifier(id=uuid.uuid4(), value=value)
        )
    if objs:
        ProjectTypeQualifier.objects.bulk_create(objs)


def remove_project_type_qualifiers(apps, schema_editor):
    ProjectTypeQualifier = apps.get_model("infraohjelmointi_api", "ProjectTypeQualifier")
    ProjectTypeQualifier.objects.filter(
        value__in=[
            "street",
            "park",
            "preConstruction",
            "sports",
            "spesialtyStructures",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0084_type_qualifier"),
    ]

    operations = [
        migrations.RunPython(add_project_type_qualifiers, remove_project_type_qualifiers),
    ]
