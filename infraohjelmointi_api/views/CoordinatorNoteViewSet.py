from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.CoordinatorNoteSerializer import CoordinatorNoteSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from infraohjelmointi_api.services.CoordinatorNoteService import (
    CoordinatorNoteService,
)

class CoordinatorNoteViewSet(BaseViewSet):
    """
    API endpoint that allows coordinator notes to be viewed.
    """

    serializer_class = CoordinatorNoteSerializer

    @action(
        methods=["get"], 
        detail=False, 
        url_path=r"(?P<projectId>[-\w]+)",
    )
    def get_coordinator_notes_by_project(self, request, projectId):
        """
        Custom action to get coordinator notes of a project
            URL Parameters
            ----------

            project_id : UUID string

            Usage
            ----------

            coordinator-notes/<project_id>

            Returns
            -------

            JSON
                List of coordinator notes of  a project
        """
        try:
            print(projectId)
            queryFilter = {"projectId": projectId}
            return Response(CoordinatorNoteSerializer(context={"planningClassId": queryFilter}).data)

        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["post"], 
        detail=False, 
        url_path=r"$",
    )
    def set_coordinator_note_by_project(self, request):
        """
        Custom action to add a coordinator note to a project
            URL Parameters
            ----------

            request

            Usage
            ----------

            coordinator-notes/<request>
        """
        try:
           return CoordinatorNoteService.create(request)
        except ValueError:
            return Response(
                data={"message": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST
            )
