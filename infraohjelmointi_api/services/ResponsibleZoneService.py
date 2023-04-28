from ..models import ResponsibleZone


class ResponsibleZoneService:
    @staticmethod
    def list_all() -> list[ResponsibleZone]:
        return ResponsibleZone.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ResponsibleZone:
        return ResponsibleZone.objects.get(id=id)
