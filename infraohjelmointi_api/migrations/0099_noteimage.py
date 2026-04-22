# Generated for IO-812: NoteImage model (phase 1, local FileSystemStorage)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('infraohjelmointi_api', '0098_merge_20260415_1417'),
    ]

    operations = [
        migrations.CreateModel(
            name='NoteImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='note_images/%Y/%m/')),
                ('fileName', models.CharField(max_length=255)),
                ('contentType', models.CharField(max_length=64)),
                ('size', models.PositiveIntegerField(default=0)),
                ('order', models.PositiveIntegerField(default=0)),
                ('createdDate', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='infraohjelmointi_api.note')),
                ('uploadedBy', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='uploaded_note_images', to=settings.AUTH_USER_MODEL, to_field='uuid')),
            ],
            options={
                'ordering': ['order', 'createdDate'],
            },
        ),
    ]
