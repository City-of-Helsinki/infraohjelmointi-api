# Generated manually for IO-712
from django.db import migrations


def add_additional_budget_overrun_reasons(apps, schema_editor):
    """Add 2 new budget overrun reasons as requested in IO-712."""
    budget_overrun_reason = apps.get_model("infraohjelmointi_api", "BudgetOverrunReason")
    
    # New reasons to add for IO-712
    new_reasons = [
        "annualCostDistributionClarification",
        "planningCostsOrScheduleClarification",
    ]
    
    for reason in new_reasons:
        budget_overrun_reason.objects.get_or_create(value=reason)


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0070_project_onschedule'),
    ]

    operations = [
        migrations.RunPython(add_additional_budget_overrun_reasons),
    ]
