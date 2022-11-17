# Generated by Django 4.1.3 on 2022-11-17 10:10

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0007_alter_person_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='updated_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
