from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0110_projectprogramme_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectprogrammebasicinfo",
            name="estimatedCosts",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="historicalprojectprogrammebasicinfo",
            name="estimatedCosts",
            field=models.TextField(blank=True),
        ),
    ]