from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectHashtagSerializer import (
    ProjectHashtagSerializer,
)
from overrides import override
from django.db.models import Count
from rest_framework.response import Response


class ProjectHashtagViewSet(BaseViewSet):
    """
    API endpoint that allows Project Hashtags to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectHashtagSerializer

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action to get custom response for a GET request to hashtags endpoint

            Usage
            ----------

            project-hashtags/

            Returns
            -------

            List of ProjectHashtag and top 15 most used hash tags

            JSON
                { "hashTags": [ProjectHashTag], "popularHashTags": [ProjectHashTag] }
        """
        qs = self.get_queryset().prefetch_related("relatedProject")
        popularQs = (
            qs.annotate(usage_count=Count("relatedProject"))
            .filter(usage_count__gt=0)
            .order_by("-usage_count")[:15]
        )

        serializer = self.get_serializer(qs, many=True)
        popularSerializer = self.get_serializer(popularQs, many=True)
        return Response(
            {"hashTags": serializer.data, "popularHashTags": popularSerializer.data}
        )
