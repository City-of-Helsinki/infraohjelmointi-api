# Generated manually for performance optimization
# Phase 1: Add database indexes for frequently queried fields

from django.db import migrations, connection


def add_index_if_not_exists(apps, schema_editor):
    """Add indexes only if they don't already exist"""
    # Get models to access field information
    ProjectClass = apps.get_model('infraohjelmointi_api', 'ProjectClass')
    ClassFinancial = apps.get_model('infraohjelmointi_api', 'ClassFinancial')
    Project = apps.get_model('infraohjelmointi_api', 'Project')
    ProjectFinancial = apps.get_model('infraohjelmointi_api', 'ProjectFinancial')
    ProjectLocation = apps.get_model('infraohjelmointi_api', 'ProjectLocation')

    with connection.cursor() as cursor:
        # List of indexes to create: (table_name, index_name, model, field_names)
        indexes = [
            ('infraohjelmointi_api_projectclass', 'idx_projectclass_parent', ProjectClass, ['parent']),
            ('infraohjelmointi_api_projectclass', 'idx_projectclass_programmer', ProjectClass, ['defaultProgrammer']),
            ('infraohjelmointi_api_projectclass', 'idx_projectclass_path', ProjectClass, ['path']),
            ('infraohjelmointi_api_projectclass', 'idx_projectclass_coordinator', ProjectClass, ['forCoordinatorOnly']),
            ('infraohjelmointi_api_classfinancial', 'idx_classfinancial_year', ClassFinancial, ['year']),
            ('infraohjelmointi_api_classfinancial', 'idx_classfinancial_frameview', ClassFinancial, ['forFrameView']),
            ('infraohjelmointi_api_classfinancial', 'idx_classfinancial_class', ClassFinancial, ['classRelation']),
            ('infraohjelmointi_api_classfinancial', 'idx_classfinancial_composite', ClassFinancial, ['classRelation', 'year', 'forFrameView']),
            ('infraohjelmointi_api_project', 'idx_project_programmed', Project, ['programmed']),
            ('infraohjelmointi_api_project', 'idx_project_class', Project, ['projectClass']),
            ('infraohjelmointi_api_projectfinancial', 'idx_projectfinancial_year', ProjectFinancial, ['year']),
            ('infraohjelmointi_api_projectfinancial', 'idx_projectfinancial_frameview', ProjectFinancial, ['forFrameView']),
            ('infraohjelmointi_api_projectlocation', 'idx_projectlocation_parent', ProjectLocation, ['parent']),
            ('infraohjelmointi_api_projectlocation', 'idx_projloc_parentclass', ProjectLocation, ['parentClass']),
        ]

        for table_name, index_name, model, field_names in indexes:
            # Check if index already exists
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = %s AND indexname = %s
            """, [table_name, index_name])

            if cursor.fetchone():
                print(f"Index {index_name} already exists, skipping...")
                continue

            # Get actual database column names from model fields
            db_columns = []
            for field_name in field_names:
                field = model._meta.get_field(field_name)
                # For ForeignKey fields, get the actual database column name
                db_column = field.db_column or field.get_attname()
                db_columns.append(db_column)

            # Create index with actual database column names
            fields_str = ', '.join(f'"{col}"' for col in db_columns)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS "{index_name}" 
                ON "{table_name}" ({fields_str})
            """)


def reverse_add_indexes(apps, schema_editor):
    """Remove indexes if they exist"""
    with connection.cursor() as cursor:
        indexes = [
            'idx_projectclass_parent',
            'idx_projectclass_programmer',
            'idx_projectclass_path',
            'idx_projectclass_coordinator',
            'idx_classfinancial_year',
            'idx_classfinancial_frameview',
            'idx_classfinancial_class',
            'idx_classfinancial_composite',
            'idx_project_programmed',
            'idx_project_class',
            'idx_projectfinancial_year',
            'idx_projectfinancial_frameview',
            'idx_projectlocation_parent',
            'idx_projloc_parentclass',
        ]

        for index_name in indexes:
            cursor.execute(f'DROP INDEX IF EXISTS "{index_name}"')


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0074_alter_projectprogrammer_unique_together'),
    ]

    operations = [
        migrations.RunPython(add_index_if_not_exists, reverse_add_indexes),
    ]

