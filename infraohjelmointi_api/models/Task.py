import uuid
from django.db import models
from .TaskStatus import TaskStatus


class Task(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projectId = models.ForeignKey("Project", on_delete=models.DO_NOTHING)
    hkrId = models.PositiveBigIntegerField(blank=True, null=True)
    taskType = models.CharField(max_length=50, blank=False, null=False)
    status = models.ForeignKey(
        TaskStatus, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    startDate = models.DateField(auto_now=True, blank=True)
    endDate = models.DateField(auto_now=True, blank=True)
    person = models.ForeignKey(
        "Person", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    realizedCost = models.DecimalField(max_digits=20, decimal_places=2)
    plannedCost = models.DecimalField(max_digits=20, decimal_places=2)
    # TaskAccomplishment
    riskAssess = models.CharField(max_length=200, blank=False, null=False)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
