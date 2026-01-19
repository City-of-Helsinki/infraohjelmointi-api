import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0083_project_postalcode_city_not_null"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectTypeQualifier",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("value", models.CharField(max_length=30)),
                ("createdDate", models.DateTimeField(auto_now_add=True, blank=True)),
                ("updatedDate", models.DateTimeField(auto_now=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name="project",
            name="typeQualifier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="infraohjelmointi_api.projecttypequalifier",
            ),
        ),
    ]
