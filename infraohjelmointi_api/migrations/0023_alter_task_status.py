# Generated by Django 4.1.3 on 2022-11-21 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0022_alter_task_person'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('past', 'Past'), ('upcoming', 'Upcoming')], default='upcoming', max_length=8),
        ),
    ]