# Generated by Django 4.1.3 on 2023-01-10 14:18

from django.db import migrations, models
import django.db.models.deletion
import uuid


def populate_ResponsibleZone_data(apps, schema_editor):
    ResponsibleZone = apps.get_model("infraohjelmointi_api", "ResponsibleZone")
    responsibleZones = [
        "east",
        "west",
        "north",
    ]
    for zone in responsibleZones:
        ResponsibleZone.objects.create(value=zone)


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0021_historicalnote_deleted_note_deleted"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResponsibleZone",
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
                ("value", models.CharField(max_length=200)),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("updatedDate", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="project",
            name="projectProgram",
            field=models.TextField(blank=True, max_length=15000, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="responsibleZone",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="infraohjelmointi_api.responsiblezone",
            ),
        ),
        migrations.RunPython(populate_ResponsibleZone_data),
    ]
