import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0115_merge_20260825_1304'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectprogrammelink',
            name='contentType',
            field=models.ForeignKey(
                help_text='References to any type of a section (basic info, design criteria, etc.)',
                on_delete=django.db.models.deletion.CASCADE,
                to='contenttypes.contenttype',
            ),
        ),
        migrations.AlterField(
            model_name='projectprogrammelink',
            name='value',
            field=models.URLField(help_text='link URL-address', max_length=500),
        ),
    ]
