from ..models import ProjectFinancial


class ProjectFinancialService:
    @staticmethod
    def get_or_create(year: str, project_id: str) -> ProjectFinancial:
        return ProjectFinancial.objects.get_or_create(year=year, project_id=project_id)

    @staticmethod
    def filter(**kwargs):
        return ProjectFinancial.objects.filter(**kwargs)
