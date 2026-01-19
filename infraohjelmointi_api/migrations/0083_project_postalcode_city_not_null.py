from django.db import migrations, models


def set_postal_city_empty_strings(apps, schema_editor):
    Project = apps.get_model("infraohjelmointi_api", "Project")
    Project.objects.filter(postalCode__isnull=True).update(postalCode="")
    Project.objects.filter(city__isnull=True).update(city="")


def revert_postal_city_nulls(apps, schema_editor):
    Project = apps.get_model("infraohjelmointi_api", "Project")
    Project.objects.filter(postalCode="").update(postalCode=None)
    Project.objects.filter(city="").update(city=None)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("infraohjelmointi_api", "0082_project_postalcode_city"),
    ]

    operations = [
        migrations.RunPython(
            set_postal_city_empty_strings, revert_postal_city_nulls
        ),
        migrations.AlterField(
            model_name="project",
            name="postalCode",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name="project",
            name="city",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
