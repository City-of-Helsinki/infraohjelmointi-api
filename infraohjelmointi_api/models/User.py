from helusers.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending helusers AbstractUser.
    
    The last_api_use field exists in the database but is not used.
    It was originally added thinking it was part of django-helusers,
    but it's not. We keep it as a nullable field to avoid ORM issues.
    """
    last_api_use = models.DateField(
        null=True,
        blank=True,
        editable=False,
        verbose_name='Latest API token usage date',
        help_text='Unused field - kept for database compatibility'
    )
    
    class Meta:
        pass
