from django.db import migrations

def create_empty_programmer(apps, schema_editor):
    """Ensure there is exactly one 'Ei Valintaa' programmer entity."""
    ProjectProgrammer = apps.get_model("infraohjelmointi_api", "ProjectProgrammer")

    # Delete any existing 'Ei Valintaa' programmers to ensure uniqueness
    ProjectProgrammer.objects.filter(firstName="Ei", lastName="Valintaa").delete()

    # Create the single 'Ei Valintaa' programmer
    ProjectProgrammer.objects.create(
        firstName="Ei",
        lastName="Valintaa",
        person=None
    )

def remove_empty_programmer(apps, schema_editor):
    """Remove the 'Ei Valintaa' programmer entity."""
    ProjectProgrammer = apps.get_model("infraohjelmointi_api", "ProjectProgrammer")
    ProjectProgrammer.objects.filter(firstName="Ei", lastName="Valintaa").delete()

class Migration(migrations.Migration):
    dependencies = [
        ('infraohjelmointi_api', '0068_projectprogrammer_projectclass_defaultprogrammer_and_more'),
    ]

    operations = [
        migrations.RunPython(
            create_empty_programmer,
            reverse_code=remove_empty_programmer
        ),
    ]

