# Generated by Django 4.1.3 on 2022-12-02 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0006_alter_project_sapproject_hkrid"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="address",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
