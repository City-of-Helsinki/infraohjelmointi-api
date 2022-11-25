# Generated by Django 4.1.3 on 2022-11-24 14:04

from django.db import migrations


def rename_area_data(apps, schema_editor):
    ProjectArea = apps.get_model("infraohjelmointi_api", "ProjectArea")
    areaNames = [
        "honkasuo",
        "kalasatama",
        "kruunuvuorenranta",
        "kuninkaantammi",
        "lansisatama",
        "malminLentokenttaalue",
        "pasila",
        "ostersundom",
    ]
    projectList = ProjectArea.objects.filter(location="Helsinki")
    for obj, area in zip(projectList, areaNames):
        obj.value = area
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0014_rename_areaname_projectarea_value"),
    ]

    operations = [migrations.RunPython(rename_area_data)]
