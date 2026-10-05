from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "infraohjelmointi_api",
            "0119_noteimage",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="project",
            old_name="projectProgram",
            new_name="additionalInformation",
        ),
    ]