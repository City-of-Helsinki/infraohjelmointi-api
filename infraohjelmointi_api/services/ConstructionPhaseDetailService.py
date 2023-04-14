from ..models import ConstructionPhaseDetail


class ConstructionPhaseDetailService:
    @staticmethod
    def list_all() -> list[ConstructionPhaseDetail]:
        return ConstructionPhaseDetail.objects.all()
