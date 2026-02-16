# Project phases and suspension: rename ConstructionPhaseDetail to ProjectPhaseDetail,
# add phaseDetail + suspension fields to Project, new phases (constructionPreparation, suspended).

from django.db import migrations, models
import django.db.models.deletion


def sanitize_and_populate(apps, schema_editor):
    Project = apps.get_model("infraohjelmointi_api", "Project")
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")

    construction_phase = ProjectPhase.objects.filter(value="construction").first()
    if construction_phase:
        Project.objects.exclude(phase=construction_phase).filter(
            phaseDetail__isnull=False
        ).update(phaseDetail=None)
        ProjectPhaseDetail.objects.filter(projectPhase__isnull=True).update(
            projectPhase=construction_phase
        )

    max_index = ProjectPhase.objects.count()
    construction_prep_phase, _ = ProjectPhase.objects.get_or_create(
        value="constructionPreparation",
        defaults={"index": max_index}
    )
    ProjectPhase.objects.get_or_create(
        value="suspended",
        defaults={"index": max_index + 1}
    )

    for detail_value in ["Siirretty rakentamiseen", "Urakan valmistelu"]:
        ProjectPhaseDetail.objects.get_or_create(
            value=detail_value,
            projectPhase=construction_prep_phase,
        )


def reverse_sanitize(apps, schema_editor):
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")
    ProjectPhaseDetail.objects.filter(
        projectPhase__value__in=["constructionPreparation", "suspended"]
    ).delete()
    ProjectPhase.objects.filter(
        value__in=["constructionPreparation", "suspended"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0091_project_priority_default"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ConstructionPhaseDetail",
            new_name="ProjectPhaseDetail",
        ),
        migrations.AlterField(
            model_name="projectphasedetail",
            name="value",
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name="projectphasedetail",
            name="projectPhase",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="phaseDetails",
                to="infraohjelmointi_api.projectphase",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="suspendedDate",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="suspendedFromPhase",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="suspended_projects",
                to="infraohjelmointi_api.projectphase",
            ),
        ),
        migrations.RenameField(
            model_name="project",
            old_name="constructionPhaseDetail",
            new_name="phaseDetail",
        ),
        migrations.RunPython(sanitize_and_populate, reverse_sanitize),
        migrations.AlterField(
            model_name="projectphasedetail",
            name="projectPhase",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="phaseDetails",
                to="infraohjelmointi_api.projectphase",
            ),
        ),
    ]
