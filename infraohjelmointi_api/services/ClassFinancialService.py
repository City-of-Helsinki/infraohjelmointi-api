from .ProjectClassService import ProjectClassService
from ..models import ClassFinancial, ProjectClass


class ClassFinancialService:
    @staticmethod
    def get_or_create(year: str, class_id: str, for_frame_view: bool) -> ClassFinancial:
        return ClassFinancial.objects.get_or_create(
            year=year, classRelation_id=class_id, forFrameView=for_frame_view
        )

    @staticmethod
    def update_or_create(year: str, class_id: str, for_frame_view: bool, updatedData: dict) -> ClassFinancial:
        return ClassFinancial.objects.update_or_create(
            year=year, classRelation_id=class_id, forFrameView=for_frame_view, defaults=updatedData
        )

    @staticmethod
    def get(class_id: str, year: str, for_frame_view: bool) -> ClassFinancial:
        return ClassFinancial.objects.get(classRelation_id=class_id, year=year, forFrameView=for_frame_view)

    @staticmethod
    def get_request_field_to_year_mapping(start_year: int):
        return {"year{}".format(index): start_year + index for index in range(0, 11)}

    @staticmethod
    def get_coordinator_class_and_related_class(instance: ClassFinancial) -> dict:
        """
        Returns the class instances for coordinator class linked to the ClassFinancial object and the related planning class linked to the coordinator Class.

            Parameters
            ----------
            instance : ClassFinancial
                instance of ClassFinancial to get relations

            Returns
            -------
            dict
                {
                "coordination": {
                    "<type_of_class>": <ProjectClass instance>,
                    },
                "planning": {
                    "<type_of_class>": <ProjectClass instance>,
                    },
                }
        """
        classInstances = {"coordination": {}, "planning": {}}

        coordinatorClassInstance: ProjectClass = instance.classRelation

        classInstances["coordination"][
            ProjectClassService.identify_class_type(
                classInstance=coordinatorClassInstance
            )
        ] = coordinatorClassInstance

        classInstances["planning"][
            ProjectClassService.identify_class_type(
                classInstance=coordinatorClassInstance.relatedTo
            )
        ] = coordinatorClassInstance.relatedTo

        # Traverse backwards from current Coordination Class to get parent classes
        # Get related planning classes along the way
        currCoordinationClass = coordinatorClassInstance.parent
        while currCoordinationClass != None:
            classInstances["coordination"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationClass
                )
            ] = currCoordinationClass

            classInstances["planning"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationClass.relatedTo
                )
            ] = currCoordinationClass.relatedTo

            currCoordinationClass = currCoordinationClass.parent

        return classInstances
