from ..models import ProjectFinancial


class ProjectFinancialService:
    @staticmethod
    def get_or_create(
        year: str, project_id: str, forFrameView: bool = False
    ) -> ProjectFinancial:
        return ProjectFinancial.objects.get_or_create(
            year=year, project_id=project_id, forFrameView=forFrameView
        )

    @staticmethod
    def create(
        year: str, project_id: str, forFrameView: bool = False, value: int = 0
    ) -> ProjectFinancial:
        return ProjectFinancial.objects.create(
            year=year, project_id=project_id, forFrameView=forFrameView, value=value
        )

    @staticmethod
    def update_or_create(
        year: str,
        project_id: str,
        updatedData: dict,
        forFrameView: bool = False,
    ) -> ProjectFinancial:
        return ProjectFinancial.objects.update_or_create(
            year=year,
            project_id=project_id,
            forFrameView=forFrameView,
            defaults=updatedData,
        )

    @staticmethod
    def update_or_create_bulk(
        project_financials: list[ProjectFinancial],
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.bulk_create(
            project_financials,
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["year", "project_id", "forFrameView"],
        )

    @staticmethod
    def find_by_project_id_and_max_year(
        project_id: str, max_year: int, forFrameView: bool = False
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(
            project=project_id, year__lt=max_year, forFrameView=forFrameView
        )

    @staticmethod
    def find_by_project_id_and_year_range(
        project_id: str, year_range: range, forFrameView: bool = False
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(
            project=project_id, year__in=year_range, forFrameView=forFrameView
        )

    @staticmethod
    def find_by_min_value_and_year_range(
        min_value: int, year_range: range, forFrameView: bool = False
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(
            value__gt=min_value, year__in=year_range, forFrameView=forFrameView
        )

    @staticmethod
    def find_by_min_value_and_min_year(
        min_value: int, min_year: int, forFrameView: bool = False
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(
            value__gt=min_value, year__gte=min_year, forFrameView=forFrameView
        )

    @staticmethod
    def find_by_min_value_and_max_year(
        min_value: int, max_year: int, forFrameView: bool = False
    ) -> list[ProjectFinancial]:
        return ProjectFinancial.objects.filter(
            value__gt=min_value, year__lte=max_year, forFrameView=forFrameView
        )

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
    def convert_financial_field_to_year(field_name: str, start_year: int):
        number = None
        if field_name.startswith("budgetProposalCurrentYearPlus"):
            number = int(field_name.replace("budgetProposalCurrentYearPlus", ""))
        elif field_name.startswith("preliminaryCurrentYearPlus"):
            number = int(field_name.replace("preliminaryCurrentYearPlus", ""))
        return start_year + number

    @staticmethod
    def instance_exists(project_id: str, year: int, forFrameView: bool = False) -> bool:
        """Check if instance exists in DB"""
        return ProjectFinancial.objects.filter(
            project_id=project_id, year=year, forFrameView=forFrameView
        ).exists()
