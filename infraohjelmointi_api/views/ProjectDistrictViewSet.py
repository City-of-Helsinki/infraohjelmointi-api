from infraohjelmointi_api.serializers.ProjectDistrictSerializer import ProjectDistrictSerializer
from .BaseViewSet import BaseViewSet

from rest_framework.decorators import action


class ProjectDistrictViewSet(BaseViewSet):
    """
    API endpoint that allows Project Districts to be viewed or edited
    """

    serializer_class = ProjectDistrictSerializer

       
