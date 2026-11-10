from django.db import migrations


def add_pikku_huopalahti_subdivisions(apps, schema_editor):
    project_district = apps.get_model("infraohjelmointi_api", "ProjectDistrict")
    districts = project_district.objects.using(schema_editor.connection.alias)

    for parent in districts.filter(
        name__in=["Haaga", "Ruskeasuo", "Meilahti"],
        level="division",
    ):
        districts.get_or_create(
            name="Pikku Huopalahti",
            level="subDivision",
            parent=parent,
            path=f"{parent.path}/Pikku Huopalahti",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0127_add_unallocated_major_transport_class"),
    ]

    operations = [
        migrations.RunPython(
            add_pikku_huopalahti_subdivisions,
            migrations.RunPython.noop,
        ),
    ]