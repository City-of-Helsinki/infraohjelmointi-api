import uuid
from django.db import models

from infraohjelmointi_api.models import Project, ProjectClass, ProjectGroup, User

class AuditLog(models.Model):
    LOG_LEVEL_CHOICES = [
        ("INFO", "INFO"),
        ("WARNING", "WARNING"),
        ("ERROR", "ERROR"),
        ("CRITICAL", "CRITICAL"),
    ]
    OPERATION_CHOICES = [
        ("CREATE", "CREATE"),
        ("UPDATE", "UPDATE"),
        ("DELETE", "DELETE"),
    ]
    STATUS_CHOICES = [
        ("SUCCESS", "SUCCESS"),
        ("FAILURE", "FAILURE"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, null=False, blank=False, editable=False
    )
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES, blank=False, null=False, editable=False) # what was done e.g. update or delete
    log_level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, blank=False, null=False, editable=False) # INFO / ERROR
    origin = models.CharField(max_length=100, blank=False, null=False, editable=False) # only infrahankkeiden_ohjelmointi for now
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=False, null=False, editable=False)  # SUCCESS / FAILURE
    project = models.ForeignKey(
        Project, on_delete=models.DO_NOTHING, null=True, blank=True, editable=False
    )
    project_group = models.ForeignKey(
        ProjectGroup, on_delete=models.DO_NOTHING, null=True, blank=True, editable=False
    )
    project_class = models.ForeignKey(
        ProjectClass, on_delete=models.DO_NOTHING, null=True, blank=True, editable=False
    )
    old_values = models.JSONField(null=True, blank=True, editable=False)
    new_values = models.JSONField(null=True, blank=True, editable=False)
    endpoint = models.CharField(max_length=200, blank=False, null=False, editable=False) #endpoint that was called to do the operation
    createdDate = models.DateTimeField(auto_now_add=True, blank=True, editable=False)
    updatedDate = models.DateTimeField(auto_now=True, blank=True, editable=False)
