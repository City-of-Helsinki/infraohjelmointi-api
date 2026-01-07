from ..models import ConstructionProcurementMethod


class ConstructionProcurementMethodService:
    @staticmethod
    def list_all() -> list[ConstructionProcurementMethod]:
        return ConstructionProcurementMethod.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ConstructionProcurementMethod:
        return ConstructionProcurementMethod.objects.get(id=id)

    @staticmethod
    def find_by_value(value: str) -> ConstructionProcurementMethod:
        return ConstructionProcurementMethod.objects.filter(value=value).first()


