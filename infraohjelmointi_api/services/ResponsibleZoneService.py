from ..models import ResponsibleZone


class ResponsibleZoneService:
    @staticmethod
    def list_all() -> list[ResponsibleZone]:
        return ResponsibleZone.objects.all()
