# Generated by Django 4.1.3 on 2023-10-26 07:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0051_alter_classfinancial_budgetchange_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='favPersons',
            field=models.ManyToManyField(blank=True, related_name='favourite', to='infraohjelmointi_api.person'),
        ),
        migrations.AlterField(
            model_name='project',
            name='hashTags',
            field=models.ManyToManyField(blank=True, related_name='relatedProject', to='infraohjelmointi_api.projecthashtag'),
        ),
    ]
