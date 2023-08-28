from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectRiskSerializer import ProjectRiskSerializer


class ProjectRiskViewSet(BaseViewSet):
    """
    API endpoint that allows project risk assessments to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectRiskSerializer
