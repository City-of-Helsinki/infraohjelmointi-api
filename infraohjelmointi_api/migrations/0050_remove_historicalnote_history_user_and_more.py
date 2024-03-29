# Generated by Django 4.1.3 on 2023-10-20 05:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0049_auto_20230922_0857"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="historicalnote",
            name="history_user",
        ),
        migrations.AddField(
            model_name="historicalnote",
            name="history_user_id",
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AlterField(
            model_name="historicalnote",
            name="updatedBy",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                to_field="uuid",
            ),
        ),
        migrations.AlterField(
            model_name="note",
            name="updatedBy",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to=settings.AUTH_USER_MODEL,
                to_field="uuid",
            ),
        ),
    ]
