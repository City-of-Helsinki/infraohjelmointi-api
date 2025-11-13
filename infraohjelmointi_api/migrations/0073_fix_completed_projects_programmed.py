# Generated manually for IO-755
# This migration fixes the programmed field for existing completed projects
# based on whether they have budget for the current year

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0072_update_project_location'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- IO-755: Fix programmed field for completed projects based on current year budget
                UPDATE infraohjelmointi_api_project p
                SET programmed = (
                    EXISTS (
                        SELECT 1
                        FROM infraohjelmointi_api_projectfinancial pf
                        WHERE pf.project_id = p.id
                          AND pf.year = EXTRACT(YEAR FROM CURRENT_DATE)
                          AND pf."forFrameView" = false
                          AND pf.value IS NOT NULL
                          AND pf.value != 0
                    )
                )
                WHERE p.phase_id = (
                    SELECT id FROM infraohjelmointi_api_projectphase WHERE value = 'completed'
                );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

