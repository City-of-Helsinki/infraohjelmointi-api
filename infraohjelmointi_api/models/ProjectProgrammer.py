import uuid
from django.db import models

class ProjectProgrammer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    person = models.ForeignKey(
        "Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="personProgramming"
    )

    def is_empty_programmer(self):
        """Check if this is the special empty programmer entity"""
        return self.firstName == "Ei" and self.lastName == "Valintaa"
