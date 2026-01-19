from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0081_alter_talpaprojecttype_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="postalCode",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="city",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
