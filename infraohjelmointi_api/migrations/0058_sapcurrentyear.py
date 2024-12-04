# Generated by Django 4.2 on 2024-12-03 06:29

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0057_appstatevalue_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SapCurrentYear',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('year', models.IntegerField(null=None)),
                ('sap_id', models.CharField(max_length=30, null=None)),
                ('project_task_costs', models.DecimalField(decimal_places=3, default=0.0, max_digits=20, null=None)),
                ('project_task_commitments', models.DecimalField(decimal_places=3, default=0.0, max_digits=20, null=None)),
                ('production_task_costs', models.DecimalField(decimal_places=3, default=0.0, max_digits=20, null=None)),
                ('production_task_commitments', models.DecimalField(decimal_places=3, default=0.0, max_digits=20, null=None)),
                ('group_combined_commitments', models.DecimalField(decimal_places=3, default=0.0, max_digits=20, null=None)),
                ('group_combined_costs', models.DecimalField(decimal_places=3, default=0.0, max_digits=20, null=None)),
                ('createdDate', models.DateTimeField(auto_now_add=True)),
                ('updatedDate', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='infraohjelmointi_api.project')),
                ('project_group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='infraohjelmointi_api.projectgroup')),
            ],
        ),
    ]