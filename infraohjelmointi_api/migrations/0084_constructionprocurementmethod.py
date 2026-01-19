from django.db import migrations, models
import uuid


def populate_construction_procurement_method_data(apps, schema_editor):
    ConstructionProcurementMethod = apps.get_model(
        "infraohjelmointi_api", "ConstructionProcurementMethod"
    )
    methods = ["Stara", "Puitesopimus", "Kilpailutettu", "Yhteistoiminnalliset"]
    for method in methods:
        ConstructionProcurementMethod.objects.create(value=method)


class Migration(migrations.Migration):

    dependencies = [
        (
            "infraohjelmointi_api",
            "0083_project_postalcode_city_not_null",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="ConstructionProcurementMethod",
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
        migrations.AddField(
            model_name="project",
            name="constructionProcurementMethod",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.DO_NOTHING,
                to="infraohjelmointi_api.constructionprocurementmethod",
            ),
        ),
        migrations.RunPython(populate_construction_procurement_method_data),
    ]


