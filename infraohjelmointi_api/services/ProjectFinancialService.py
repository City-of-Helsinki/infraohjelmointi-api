from ..models import ProjectFinancial


class ProjectFinancialService:
    @staticmethod
    def get_or_create(year: str, project_id: str) -> ProjectFinancial:
        return ProjectFinancial.objects.get_or_create(year=year, project_id=project_id)

    @staticmethod
    def update_or_create(
        year: str, project_id: str, updatedData: dict
    ) -> ProjectFinancial:
        return ProjectFinancial.objects.update_or_create(
            year=year, project_id=project_id, defaults=updatedData
        )

    @staticmethod
    def find_by_project_id_and_max_year(
        project_id: str, max_year=int
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(project=project_id, year__lt=max_year)

    @staticmethod
    def find_by_project_id_and_year_range(
        project_id: str, year_range: range
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(project=project_id, year__in=year_range)

    @staticmethod
    def find_by_min_value_and_year_range(
        min_value: int, year_range: range
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(value__gt=min_value, year__in=year_range)

    @staticmethod
    def find_by_min_value_and_min_year(
        min_value: int, min_year: int
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(value__gt=min_value, year__gte=min_year)

    @staticmethod
    def find_by_min_value_and_max_year(
        min_value: int, max_year: int
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(value__gt=min_value, year__lte=max_year)

    @staticmethod
    def get_year_to_financial_field_names_mapping(start_year: int):
        return {
            start_year: "budgetProposalCurrentYearPlus0",
            start_year + 1: "budgetProposalCurrentYearPlus1",
            start_year + 2: "budgetProposalCurrentYearPlus2",
            start_year + 3: "preliminaryCurrentYearPlus3",
            start_year + 4: "preliminaryCurrentYearPlus4",
            start_year + 5: "preliminaryCurrentYearPlus5",
            start_year + 6: "preliminaryCurrentYearPlus6",
            start_year + 7: "preliminaryCurrentYearPlus7",
            start_year + 8: "preliminaryCurrentYearPlus8",
            start_year + 9: "preliminaryCurrentYearPlus9",
            start_year + 10: "preliminaryCurrentYearPlus10",
        }

    @staticmethod
    def get_financial_field_to_year_mapping(start_year: int):
        return {
            "budgetProposalCurrentYearPlus0": start_year,
            "budgetProposalCurrentYearPlus1": start_year + 1,
            "budgetProposalCurrentYearPlus2": start_year + 2,
            "preliminaryCurrentYearPlus3": start_year + 3,
            "preliminaryCurrentYearPlus4": start_year + 4,
            "preliminaryCurrentYearPlus5": start_year + 5,
            "preliminaryCurrentYearPlus6": start_year + 6,
            "preliminaryCurrentYearPlus7": start_year + 7,
            "preliminaryCurrentYearPlus8": start_year + 8,
            "preliminaryCurrentYearPlus9": start_year + 9,
            "preliminaryCurrentYearPlus10": start_year + 10,
        }
