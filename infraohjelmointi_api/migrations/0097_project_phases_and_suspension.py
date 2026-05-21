"""IO-389: ProjectPhaseDetail, suspension fields, new phases and details."""

from django.db import migrations, models
from django.db.models import Max
import django.db.models.deletion


def populate_phases_and_details(apps, schema_editor):
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    construction_phase = ProjectPhase.objects.filter(value="construction").first()
    if construction_phase:
        ProjectPhaseDetail.objects.filter(projectPhase__isnull=True).update(
            projectPhase=construction_phase
        )
        Project.objects.exclude(phase=construction_phase).filter(
            phaseDetail__isnull=False
        ).update(phaseDetail=None)

    for phase in ProjectPhase.objects.all():
        if phase.order is not None and phase.order != phase.index:
            phase.index = phase.order
            phase.save(update_fields=["index"])

    construction_phase_obj = ProjectPhase.objects.filter(value="construction").first()
    if construction_phase_obj and construction_phase_obj.order is not None:
        insert_order = construction_phase_obj.order
        ProjectPhase.objects.filter(order__gte=insert_order).update(
            order=models.F("order") + 1,
            index=models.F("index") + 1,
        )
        ProjectPhase.objects.get_or_create(
            value="constructionPreparation",
            defaults={"order": insert_order, "index": insert_order},
        )
    else:
        max_order = ProjectPhase.objects.aggregate(Max("order"))["order__max"] or -1
        ProjectPhase.objects.get_or_create(
            value="constructionPreparation",
            defaults={"order": max_order + 1, "index": max_order + 1},
        )

    max_order = ProjectPhase.objects.aggregate(Max("order"))["order__max"] or -1
    ProjectPhase.objects.get_or_create(
        value="suspended",
        defaults={"order": max_order + 1, "index": max_order + 1},
    )

    phase_details_to_create = {
        "programming": [
            "waitingProjectManager",
            "waitingPlanningStart",
        ],
        "draftInitiation": [
            "streetParkPlanDraft",
        ],
        "draftApproval": [
            "streetParkPlanApproval",
        ],
        "constructionPlan": [
            "constructionDesign",
        ],
        "constructionWait": [
            "waitingFunding",
        ],
        "constructionPreparation": [
            "movedToConstruction",
            "contractPreparation",
        ],
    }

    for phase_value, detail_values in phase_details_to_create.items():
        phase = ProjectPhase.objects.filter(value=phase_value).first()
        if not phase:
            continue
        for detail_value in detail_values:
            ProjectPhaseDetail.objects.get_or_create(
                value=detail_value,
                projectPhase=phase,
            )


def reverse_populate(apps, schema_editor):
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    new_detail_values = [
        "waitingProjectManager", "waitingPlanningStart",
        "streetParkPlanDraft", "streetParkPlanApproval",
        "constructionDesign", "waitingFunding",
        "movedToConstruction", "contractPreparation",
    ]
    # Clear phaseDetail FK on projects before deleting the detail rows (DO_NOTHING won't cascade)
    Project.objects.filter(phaseDetail__value__in=new_detail_values).update(phaseDetail=None)
    ProjectPhaseDetail.objects.filter(value__in=new_detail_values).delete()

    phases_to_delete = ["constructionPreparation", "suspended"]
    # Move projects off phases that are about to be deleted
    fallback_phase = ProjectPhase.objects.filter(value="proposal").first()
    if fallback_phase:
        Project.objects.filter(phase__value__in=phases_to_delete).update(
            phase=fallback_phase
        )
    # Clear suspendedFromPhase references
    Project.objects.filter(suspendedFromPhase__value__in=phases_to_delete).update(
        suspendedFromPhase=None
    )
    ProjectPhase.objects.filter(value__in=phases_to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0096_alter_budgetoverrunreason_options_and_more"),
    ]

    operations = [
        # 1. Rename model
        migrations.RenameModel(
            old_name="ConstructionPhaseDetail",
            new_name="ProjectPhaseDetail",
        ),
        # 2. Increase value max_length
        migrations.AlterField(
            model_name="projectphasedetail",
            name="value",
            field=models.CharField(max_length=100),
        ),
        # 3. Add projectPhase FK (nullable initially for data migration)
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
        # 4. Rename FK on Project
        migrations.RenameField(
            model_name="project",
            old_name="constructionPhaseDetail",
            new_name="phaseDetail",
        ),
        # 5. Add suspension fields on Project
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
        # 6. Data migration
        migrations.RunPython(populate_phases_and_details, reverse_populate),
        # 7. Make projectPhase required
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
