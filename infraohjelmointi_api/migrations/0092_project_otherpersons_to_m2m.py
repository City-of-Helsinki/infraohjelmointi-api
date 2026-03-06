from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0091_project_priority_default"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="otherPersons",
        ),
        migrations.AddField(
            model_name="project",
            name="otherPersons",
            field=models.ManyToManyField(blank=True, related_name="other", to="infraohjelmointi_api.person"),
        ),
    ]
