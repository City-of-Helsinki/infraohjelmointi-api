# Generated by Django 4.2 on 2025-01-10 12:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0061_alter_auditlog_actor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='project',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='infraohjelmointi_api.project'),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='project_class',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='infraohjelmointi_api.projectclass'),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='project_group',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='infraohjelmointi_api.projectgroup'),
        ),
    ]
