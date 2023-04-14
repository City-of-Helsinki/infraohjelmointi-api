# Generated by Django 4.1.3 on 2022-12-19 10:12

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        (
            "infraohjelmointi_api",
            "0012_rename_estdesignenddate_project_estconstructionend_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="ConstructionPhaseDetail",
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
                ("value", models.CharField(max_length=30)),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("updatedDate", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ProjectCategory",
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
                ("value", models.CharField(max_length=7)),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("updatedDate", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="ProjectRisk",
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
            name="gravel",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="louhi",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="category_temp",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="infraohjelmointi_api.projectcategory",
            ),
        ),
        migrations.RemoveField(
            model_name="project",
            name="constructionPhaseDetail",
        ),
        migrations.AddField(
            model_name="project",
            name="constructionPhaseDetail",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="infraohjelmointi_api.constructionphasedetail",
            ),
        ),
        migrations.RemoveField(
            model_name="project",
            name="riskAssess",
        ),
        migrations.AddField(
            model_name="project",
            name="riskAssess",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="infraohjelmointi_api.projectrisk",
            ),
        ),
    ]
