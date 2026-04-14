from ..models import StaraProcurementReason


class StaraProcurementReasonService:
    @staticmethod
    def list_all() -> list[StaraProcurementReason]:
        return StaraProcurementReason.objects.all()

    @staticmethod
    def get_by_id(id: str) -> StaraProcurementReason:
        return StaraProcurementReason.objects.get(id=id)

    @staticmethod
    def find_by_value(value: str) -> StaraProcurementReason:
        return StaraProcurementReason.objects.filter(value=value).first()


