from django.db import models
from .SapBaseModel import SapBaseModel

class SapCurrentYear(SapBaseModel):
    # If you have specific methods or Meta class attributes for SapCurrentYear, define them here
    year = models.IntegerField(null=None)
    pass