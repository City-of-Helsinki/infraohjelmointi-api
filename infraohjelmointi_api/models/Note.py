import uuid
from django.db import models
from django.utils.timezone import now


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField(blank=True, null=False, default="")
    updatedBy = models.ForeignKey("Person", on_delete=models.DO_NOTHING, null=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
