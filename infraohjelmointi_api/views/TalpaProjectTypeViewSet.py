from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from overrides import override
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from helusers.oidc import ApiTokenAuthentication

from infraohjelmointi_api.models import TalpaProjectType
from infraohjelmointi_api.serializers.TalpaProjectOpeningSerializer import (
    TalpaProjectTypeSerializer,
)
from infraohjelmointi_api.views.BaseViewSet import BaseViewSet


class TalpaProjectTypeFilter(django_filters.FilterSet):
    """Filter for TalpaProjectType"""
    category = django_filters.CharFilter(field_name="category", lookup_expr="icontains")
    isActive = django_filters.BooleanFilter(field_name="isActive")
    code = django_filters.CharFilter(field_name="code", lookup_expr="icontains")

    class Meta:
        model = TalpaProjectType
        fields = ["category", "isActive", "code"]


class TalpaProjectTypeViewSet(BaseViewSet):
    """
    API endpoint for Talpa project types (dropdown data)
    """

    serializer_class = TalpaProjectTypeSerializer
    http_method_names = ["get"]  # Read-only
    filter_backends = [DjangoFilterBackend]
    filterset_class = TalpaProjectTypeFilter
    authentication_classes = [ApiTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self):
        """Filter to active only by default"""
        queryset = TalpaProjectType.objects.all()
        # Filter by isActive if not explicitly requested
        is_active = self.request.query_params.get("isActive", None)
        if is_active is None:
            queryset = queryset.filter(isActive=True)
        return queryset.order_by("code")

