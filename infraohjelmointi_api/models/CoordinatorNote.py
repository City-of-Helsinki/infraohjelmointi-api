import uuid
from django.db import models

class CoordinatorNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    coordinatorNote = models.TextField(blank=True, null=False, default="")
    year = models.CharField(max_length=4)
    planningClass = models.CharField(max_length=150)
    planningClassId = models.ForeignKey("ProjectClass", on_delete=models.DO_NOTHING)

    updatedById = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=False, blank=False)
    updatedByFirstName = models.CharField(max_length=50)
    updatedByLastName = models.CharField(max_length=50)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    