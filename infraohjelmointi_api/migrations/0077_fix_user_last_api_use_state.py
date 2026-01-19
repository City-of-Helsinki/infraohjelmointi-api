# Ensure last_api_use field exists in both migration state and database
# Django's migration state expects this field to exist, so we ensure the database column matches

from django.db import migrations, models, connection


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s 
                AND column_name = %s
            );
        """, [table_name, column_name])
        return cursor.fetchone()[0]


class AddFieldIfNotExists(migrations.operations.fields.AddField):
    """AddField that skips database operation if column already exists"""
    
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        table_name = f"{app_label}_{self.model_name.lower()}"
        column_name = self.name
        
        if column_exists(table_name, column_name):
            # Column already exists, skip DB operation
            # State is updated by parent's state_forwards which is called automatically
            return
        
        # Column doesn't exist, create it
        # State is updated by parent's state_forwards which is called automatically
        super().database_forwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0076_talpaassetclass_talpaprojectnumberrange_and_more'),
    ]

    operations = [
        # Ensure field exists in state (no-op if already exists) and database (if column doesn't exist)
        AddFieldIfNotExists(
            model_name='user',
            name='last_api_use',
            field=models.DateField(blank=True, null=True, verbose_name='Latest API token usage date'),
        ),
    ]

