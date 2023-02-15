# Generated by Django 4.1.3 on 2023-02-15 12:11

from django.db import migrations, models
import django.db.models.deletion
import uuid


def lock_existing_construction_projects(apps, schema_editor):
    Project = apps.get_model("infraohjelmointi_api", "Project")
    for project in Project.objects.filter(phase__value="construction"):
        project.lock.create(lockType="status_construction", lockedBy=None)


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0029_project_otherpersons"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="locked",
        ),
        migrations.CreateModel(
            name="ProjectLock",
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
                ("lockType", models.CharField(blank=False, max_length=50, null=False)),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("updatedDate", models.DateTimeField(auto_now=True)),
                (
                    "lockedBy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="infraohjelmointi_api.person",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="lock",
                        to="infraohjelmointi_api.project",
                    ),
                ),
            ],
        ),
        migrations.RunPython(lock_existing_construction_projects),
    ]
