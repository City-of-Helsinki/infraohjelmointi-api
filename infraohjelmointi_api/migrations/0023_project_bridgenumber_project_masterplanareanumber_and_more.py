# Generated by Django 4.1.3 on 2023-01-11 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0022_responsiblezone_project_projectprogram_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='bridgeNumber',
            field=models.TextField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='masterPlanAreaNumber',
            field=models.TextField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='trafficPlanNumber',
            field=models.TextField(blank=True, max_length=20, null=True),
        ),
    ]