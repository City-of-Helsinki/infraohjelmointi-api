from ..models import ConstructionPhaseDetail


class ConstructionPhaseDetailService:
    @staticmethod
    def list_all() -> list[ConstructionPhaseDetail]:
        return ConstructionPhaseDetail.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ConstructionPhaseDetail:
        return ConstructionPhaseDetail.objects.get(id=id)
