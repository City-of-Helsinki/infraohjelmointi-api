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
        return {"year{}".format(index): start_year + index for index in range(0, 11)}
