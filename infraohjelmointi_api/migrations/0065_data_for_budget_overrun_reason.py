from django.db import migrations


def populate_budget_overrun_reason(apps, schema_editor):
    budget_overrun_reason = apps.get_model("infraohjelmointi_api", "BudgetOverrunReason")
    reasons = [
        "consultancyPlanningDelay",
        "permitProcessingDelay",
        "complaintsDelay",
        "personnelResourcesDelay",
        "budgetDeficitDelay",
        "earlierSchedule",
        "totalCostsClarification",
        "projectCoordinationScheduleChange",
        "weatherConditionsChange",
        "contractorScheduleChange",
        "cityPlanScheduleChange",
        "otherReason",
    ]
    for reason in reasons:
        budget_overrun_reason.objects.create(value=reason)


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0064_budgetoverrunreason'),
    ]

    operations = [
        migrations.RunPython(populate_budget_overrun_reason),
    ]