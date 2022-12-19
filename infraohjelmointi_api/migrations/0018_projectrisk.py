# Generated by Django 4.1.3 on 2022-12-19 09:42

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0017_project_gravel_project_louhi'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectRisk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('value', models.CharField(max_length=200)),
                ('createdDate', models.DateTimeField(auto_now_add=True)),
                ('updatedDate', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
