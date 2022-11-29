# Generated by Django 4.1.3 on 2022-11-29 10:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0004_note_historicalnote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='note',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='infraohjelmointi_api.project'),
        ),
        migrations.AlterField(
            model_name='note',
            name='updatedBy',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='infraohjelmointi_api.person'),
        ),
    ]
