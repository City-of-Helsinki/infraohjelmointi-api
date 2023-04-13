# Generated by Django 4.1.3 on 2023-03-29 10:38

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import infraohjelmointi_api.models.ProjectFinancial
import uuid


class Migration(migrations.Migration):

    dependencies = [
        (
            "infraohjelmointi_api",
            "0031_project_budgetproposalcurrentyearplus0_and_description_alter",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="budgetProposalCurrentYearPlus0",
        ),
        migrations.RemoveField(
            model_name="project",
            name="budgetProposalCurrentYearPlus1",
        ),
        migrations.RemoveField(
            model_name="project",
            name="budgetProposalCurrentYearPlus2",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus10",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus3",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus4",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus5",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus6",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus7",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus8",
        ),
        migrations.RemoveField(
            model_name="project",
            name="preliminaryCurrentYearPlus9",
        ),
        migrations.CreateModel(
            name="ProjectFinancial",
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
                (
                    "year",
                    models.PositiveIntegerField(
                        default=infraohjelmointi_api.models.ProjectFinancial.currentYear,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(3000),
                        ],
                    ),
                ),
                (
                    "budgetProposalCurrentYearPlus0",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "budgetProposalCurrentYearPlus1",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "budgetProposalCurrentYearPlus2",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus3",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus4",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus5",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus6",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus7",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus8",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus9",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                (
                    "preliminaryCurrentYearPlus10",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0.0,
                        max_digits=20,
                        null=True,
                    ),
                ),
                ("createdDate", models.DateTimeField(auto_now_add=True)),
                ("updatedDate", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="finances",
                        to="infraohjelmointi_api.project",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="projectfinancial",
            constraint=models.UniqueConstraint(
                fields=("project", "year"),
                name="Unique together Constraint Project Financial",
            ),
        ),
    ]
