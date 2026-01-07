import uuid
from django.db import migrations


NEW_TYPES = [
    "newConstruction",
    "basicImprovement",
]


def reset_project_types(apps, schema_editor):
    Project = apps.get_model("infraohjelmointi_api", "Project")
    ProjectType = apps.get_model("infraohjelmointi_api", "ProjectType")

    # Avoid FK issues: detach existing references before deleting old types
    Project.objects.update(type=None)
    ProjectType.objects.all().delete()

    ProjectType.objects.bulk_create(
        [ProjectType(id=uuid.uuid4(), value=value) for value in NEW_TYPES]
    )


def invalidate_project_type_cache(apps, schema_editor):
    from infraohjelmointi_api.services.CacheService import CacheService

    CacheService.invalidate_lookup("ProjectType")


def remove_new_project_types(apps, schema_editor):
    ProjectType = apps.get_model("infraohjelmointi_api", "ProjectType")
    ProjectType.objects.filter(value__in=NEW_TYPES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0085_add_project_type_qualifiers"),
    ]

    operations = [
        migrations.RunPython(reset_project_types, remove_new_project_types),
        migrations.RunPython(invalidate_project_type_cache, migrations.RunPython.noop),
    ]
