from ..models import SapCurrentYear


class SapCurrentYearService:
    @staticmethod
    def list_all() -> list[SapCurrentYear]:
        return SapCurrentYear.objects.all()

    @staticmethod
    def get_by_id(id: str) -> SapCurrentYear:
        return SapCurrentYear.objects.get(id=id)

    @staticmethod
    def get_by_project_id(project_id: str) -> SapCurrentYear:
        return SapCurrentYear.objects.filter(project__id=project_id)

    @staticmethod
    def get_by_project_group_id(group_id: str) -> SapCurrentYear:
        return SapCurrentYear.objects.filter(project_group__id=group_id)

    @staticmethod
    def get_by_sap_id(sap_id: str) -> list[SapCurrentYear]:
        return SapCurrentYear.objects.filter(sap_id=sap_id)

    @staticmethod
    def get_by_year(year: int) -> list[SapCurrentYear]:
        return SapCurrentYear.objects.filter(year=year)

    @staticmethod
    def get_or_create(project_id: str|None, group_id: str|None, year: int) -> SapCurrentYear:
        return SapCurrentYear.objects.get_or_create(
            project_id=project_id, project_group_id=group_id, year=year
        )