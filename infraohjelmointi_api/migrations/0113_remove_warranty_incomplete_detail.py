"""IO-863: remove the warrantyIncomplete phase detail ("Takuuaika/keskeneräinen")
from the warrantyPeriod phase.

Any projects that already have this detail assigned get their phaseDetail cleared.
"""

from django.db import migrations


def remove_warranty_incomplete(apps, schema_editor):
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    detail = ProjectPhaseDetail.objects.filter(value="warrantyIncomplete").first()
    if detail is None:
        return

    Project.objects.filter(phaseDetail=detail).update(phaseDetail=None)
    detail.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0112_merge_20260818_1320"),
    ]

    operations = [
        migrations.RunPython(remove_warranty_incomplete, migrations.RunPython.noop),
    ]
