# Generated by Django 4.1.3 on 2023-06-30 08:33

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0037_migrate_old_financials_to_new_structure"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="projectfinancial",
            name="budgetProposalCurrentYearPlus0",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="budgetProposalCurrentYearPlus1",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="budgetProposalCurrentYearPlus2",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus10",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus3",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus4",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus5",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus6",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus7",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus8",
        ),
        migrations.RemoveField(
            model_name="projectfinancial",
            name="preliminaryCurrentYearPlus9",
        ),
    ]