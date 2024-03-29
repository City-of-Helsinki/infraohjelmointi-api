# Generated by Django 4.1.3 on 2023-01-18 10:59

from django.db import migrations, models
import uuid


def populateProjectHashTags(apps, schema_editor):
    ProjectHashTag = apps.get_model("infraohjelmointi_api", "ProjectHashTag")
    # Predefined hashtags
    projectHashtags = [
        "leikkipaikka",
        "leikkipuisto",
        "hulevesi",
        "aukio/tori",
        "raidejokeri",
        "viima-ratiotie",
        "väylävirasto",
        "ELY",
        "pyörätie",
        "erillisrahoitus",
        "arakohde",
        "osbu",
        "erikoistasonesteettömyys",
        "liito-orava",
        "luonnosuojelukohde",
        "arvoympäristö",
        "ylläpidoninvestointi",
        "kokoojakatu",
        "asuinkatu",
        "HSL",
        "solmuhanke",
        "joukkoliikenekatu",
        "baana",
    ]
    for hashtag in projectHashtags:
        ProjectHashTag.objects.create(value=hashtag)


class Migration(migrations.Migration):

    dependencies = [
        (
            "infraohjelmointi_api",
            "0023_project_bridgenumber_project_masterplanareanumber_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectHashTag",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("value", models.CharField(max_length=100)),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("updatedDate", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="project",
            name="hashTags",
        ),
        migrations.AddField(
            model_name="project",
            name="hashTags",
            field=models.ManyToManyField(
                blank=True,
                null=True,
                related_name="relatedProject",
                to="infraohjelmointi_api.projecthashtag",
            ),
        ),
        migrations.RunPython(populateProjectHashTags),
    ]
