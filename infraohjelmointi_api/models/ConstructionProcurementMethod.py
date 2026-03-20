import uuid
from django.db import models
from .OrderedLookupModel import OrderedLookupModel


class ConstructionProcurementMethod(OrderedLookupModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=30)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)


