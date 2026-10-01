from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "infraohjelmointi_api",
            "0118_historicalprojectprogrammetrafficplanningcriteria_cartraffic_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="projectProgram",
            new_name="additionalInformation",
        ),
    ]