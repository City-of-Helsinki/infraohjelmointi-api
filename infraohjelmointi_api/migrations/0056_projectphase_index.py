# Generated by Django 4.1.3 on 2024-06-14 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0055_coordinatornote'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectphase',
            name='index',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
