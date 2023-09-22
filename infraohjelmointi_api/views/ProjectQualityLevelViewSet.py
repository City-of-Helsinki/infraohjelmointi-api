from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectQualityLevelSerializer import (
    ProjectQualityLevelSerializer,
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class ProjectQualityLevelViewSet(BaseViewSet):
    """
    API endpoint that allows Project quality levels to be viewed or edited.
    """

    serializer_class = ProjectQualityLevelSerializer

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
