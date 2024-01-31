from ..models import MaintenanceMode

from django.db.models.signals import post_save

class MaintenanceModeService:
    @staticmethod
    def update_or_create(value: bool) -> MaintenanceMode:
        obj, created = MaintenanceMode.objects.update_or_create(
            defaults={'value': value},
        )
        return obj