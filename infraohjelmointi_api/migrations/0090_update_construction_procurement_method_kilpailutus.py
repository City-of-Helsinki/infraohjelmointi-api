from django.db import migrations


def update_construction_procurement_method_value(apps, schema_editor):
    ConstructionProcurementMethod = apps.get_model(
        "infraohjelmointi_api", "ConstructionProcurementMethod"
    )
    ConstructionProcurementMethod.objects.filter(value="Kilpailutettu").update(
        value="Kilpailutus"
    )


def reverse_update_construction_procurement_method_value(apps, schema_editor):
    ConstructionProcurementMethod = apps.get_model(
        "infraohjelmointi_api", "ConstructionProcurementMethod"
    )
    ConstructionProcurementMethod.objects.filter(value="Kilpailutus").update(
        value="Kilpailutettu"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0089_alter_talpaprojectnumberrange_budgetaccount_and_more"),
    ]

    operations = [
        migrations.RunPython(
            update_construction_procurement_method_value,
            reverse_update_construction_procurement_method_value,
        ),
    ]
