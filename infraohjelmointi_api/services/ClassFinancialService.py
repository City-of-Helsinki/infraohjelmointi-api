from ..models import ClassFinancial, ProjectClass


class ClassFinancialService:
    @staticmethod
    def get_or_create(year: str, class_id: str) -> ClassFinancial:
        return ClassFinancial.objects.get_or_create(
            year=year, classRelation_id=class_id
        )

    @staticmethod
    def update_or_create(year: str, class_id: str, updatedData: dict) -> ClassFinancial:
        return ClassFinancial.objects.update_or_create(
            year=year, classRelation_id=class_id, defaults=updatedData
        )

    @staticmethod
    def get(class_id: str, year: str) -> ClassFinancial:
        return ClassFinancial.objects.get(classRelation_id=class_id, year=year)

    @staticmethod
    def get_request_field_to_year_mapping(start_year: int):
        return {
            "year0": start_year,
            "year1": start_year + 1,
            "year2": start_year + 2,
            "year3": start_year + 3,
            "year4": start_year + 4,
            "year5": start_year + 5,
            "year6": start_year + 6,
            "year7": start_year + 7,
            "year8": start_year + 8,
            "year9": start_year + 9,
            "year10": start_year + 10,
        }
