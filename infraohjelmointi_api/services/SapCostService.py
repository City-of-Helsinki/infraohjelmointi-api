from ..models import SapCost


class SapCostService:
    @staticmethod
    def list_all() -> list[SapCost]:
        return SapCost.objects.all()

    @staticmethod
    def get_by_id(id: str) -> SapCost:
        return SapCost.objects.get(id=id)

    @staticmethod
    def get_by_project_id(project_id: str) -> SapCost:
        return SapCost.objects.filter(project__id=project_id)

    @staticmethod
    def get_by_project_group_id(group_id: str) -> SapCost:
        return SapCost.objects.filter(project_group__id=group_id)

    @staticmethod
    def get_by_sap_id(sap_id: str) -> list[SapCost]:
        return SapCost.objects.filter(sap_id=sap_id)

    @staticmethod
    def get_by_year(year: int) -> list[SapCost]:
        return SapCost.objects.filter(year=year)

    @staticmethod
    def get_or_create(project_id: str, group_id: str, year: int) -> SapCost:
        return SapCost.objects.get_or_create(
            project_id=project_id, project_group_id=group_id, year=year
        )
