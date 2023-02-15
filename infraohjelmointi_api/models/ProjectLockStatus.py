import uuid
from django.db import models
from infraohjelmointi_api.models import Person, Project


class ProjectLockStatus(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    lockType = models.CharField(max_length=15, blank=True, null=True)
    lockedBy = models.ForeignKey(
        Person, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
