from ..models import ClassFinancial, ProjectClass
from ..serializers import ProjectClassSerializer
from .ProjectClassService import ProjectClassService


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

    @staticmethod
    def get_coordinator_class_and_related_class_sums(instance: ClassFinancial) -> dict:
        """
        Returns the financial sums for coordinator class linked to the ClassFinancial object and the related planning class linked to the coordinator Class.

            Parameters
            ----------
            instance : ClassFinancial
                instance of ClassFinancial to get relations and calculate sums

            Returns
            -------
            dict
                {
                "coordination": {
                    "<type_of_class>": <ProjectClass instance with sums>,
                    },
                "planning": {
                    "<type_of_class>": <ProjectClass instance with sums>,
                    },
                }
        """
        coordinatorClassInstance: ProjectClass = instance.classRelation
        relatedPlanningClassInstance: ProjectClass | None = (
            instance.classRelation.relatedTo
        )

        coordinatorClassIdentification = ProjectClassService.identify_class_type(
            classInstance=coordinatorClassInstance
        )

        planningClassIdentification = ProjectClassService.identify_class_type(
            classInstance=relatedPlanningClassInstance
        )

        return {
            "coordination": {
                coordinatorClassIdentification: ProjectClassSerializer(
                    coordinatorClassInstance,
                    context={"for_coordinator": True},
                ).data
            },
            "planning": {
                planningClassIdentification: ProjectClassSerializer(
                    relatedPlanningClassInstance,
                    context={"for_coordinator": False},
                ).data
            },
        }
