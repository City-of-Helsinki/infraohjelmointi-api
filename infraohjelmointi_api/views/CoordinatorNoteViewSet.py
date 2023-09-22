from django.shortcuts import get_object_or_404
from infraohjelmointi_api.models import CoordinatorNote
from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.CoordinatorNoteSerializer import CoordinatorNoteSerializer
from rest_framework.decorators import action
import uuid
from rest_framework.response import Response
from rest_framework import status

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
          #  note_object = get_object_or_404(CoordinatorNote, **queryFilter)
            return Response(CoordinatorNoteSerializer(context={"planningClassId": queryFilter}).data)

        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )
