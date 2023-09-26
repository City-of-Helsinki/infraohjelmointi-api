import uuid
from django.db import models


class BudgetItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budgetMain = models.IntegerField(blank=True, null=True)
    budgetPlan = models.IntegerField(blank=True, null=True)
    site = models.CharField(max_length=200, blank=True, null=True)
    siteName = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=200, blank=True, null=True)
    need = models.DecimalField(max_digits=20, decimal_places=2)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    # one field left from budget item
