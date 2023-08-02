from ..models import ClassFinancial, ProjectClass


class ClassFinancialService:
    @staticmethod
    def get_or_create(year: str, class_id: str) -> ClassFinancial:
        return ClassFinancial.objects.get_or_create(
            year=year, classRelation__id=class_id
        )

    @staticmethod
    def update_or_create(year: str, class_id: str, updatedData: dict) -> ClassFinancial:
        return ClassFinancial.objects.update_or_create(
            year=year, classRelation__id=class_id, defaults=updatedData
        )

    @staticmethod
    def get(class_id: str, year: str) -> ClassFinancial:
        return ClassFinancial.objects.get(classRelation__id=class_id, year=year)
