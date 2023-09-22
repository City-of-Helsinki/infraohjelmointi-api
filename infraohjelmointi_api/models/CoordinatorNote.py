import uuid
from django.db import models
from .Person import Person
from .Project import Project

class CoordinatorNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    coordinatorNote = models.TextField(blank=True, null=False, default="")

    planningClass = models.CharField(max_length=150)
    planningClassId = models.ForeignKey("Project", on_delete=models.DO_NOTHING)

    updatedById = models.ForeignKey("Person", on_delete=models.DO_NOTHING, null=False, blank=False)
    updatedByFirstName = models.CharField(max_length=50)
    updatedByLastName = models.CharField(max_length=50)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
