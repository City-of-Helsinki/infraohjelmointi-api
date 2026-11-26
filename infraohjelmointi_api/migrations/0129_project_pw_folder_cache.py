from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0128_add_pikku_huopalahti_subdivisions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectWiseFolder",
            fields=[
                ("hkrId", models.PositiveBigIntegerField(primary_key=True, serialize=False)),
                ("instanceId", models.CharField(max_length=256)),
            ],
        ),
    ]