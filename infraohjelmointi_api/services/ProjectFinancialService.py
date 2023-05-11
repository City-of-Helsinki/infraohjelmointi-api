from ..models import ProjectFinancial


class ProjectFinancialService:
    @staticmethod
    def get_or_create(year: str, project_id: str) -> ProjectFinancial:
        return ProjectFinancial.objects.get_or_create(year=year, project_id=project_id)

    @staticmethod
    def findByProjectAndMaxYear(
        project_id: str, max_year=int
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(project=project_id, year__lt=max_year)
