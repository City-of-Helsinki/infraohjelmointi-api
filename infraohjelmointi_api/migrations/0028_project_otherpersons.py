# Generated by Django 4.1.3 on 2023-01-31 08:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0027_alter_project_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="otherPersons",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
