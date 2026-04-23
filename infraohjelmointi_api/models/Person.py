import uuid
from django.db import models

from .OrderedLookupModel import OrderedLookupModel


class Person(OrderedLookupModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
