from django.db.models.signals import post_save
from .models import ProjectFinancial
from django.dispatch import receiver


@receiver(post_save, sender=ProjectFinancial)
def get_notified(sender, instance, created, **kwargs):
    print("signal is triggered from Project Financial")
