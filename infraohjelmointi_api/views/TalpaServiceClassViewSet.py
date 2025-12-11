from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from overrides import override
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from helusers.oidc import ApiTokenAuthentication

from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.models import TalpaServiceClass
from infraohjelmointi_api.serializers.TalpaProjectOpeningSerializer import (
    TalpaServiceClassSerializer,
)


class TalpaServiceClassFilter(django_filters.FilterSet):
    """Filter for TalpaServiceClass"""
    projectTypePrefix = django_filters.CharFilter(field_name="projectTypePrefix")
    isActive = django_filters.BooleanFilter(field_name="isActive")

    class Meta:
        model = TalpaServiceClass
        fields = ["projectTypePrefix", "isActive"]


class TalpaServiceClassViewSet(BaseViewSet):
    """
    API endpoint for Talpa service classes (dropdown data)
    """

    serializer_class = TalpaServiceClassSerializer
    http_method_names = ["get"]  # Read-only
    filter_backends = [DjangoFilterBackend]
    filterset_class = TalpaServiceClassFilter
    authentication_classes = [ApiTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self):
        """Filter to active only by default"""
        queryset = TalpaServiceClass.objects.all()
        # Filter by isActive if not explicitly requested
        is_active = self.request.query_params.get("isActive", None)
        if is_active is None:
            queryset = queryset.filter(isActive=True)
        return queryset.order_by("code")

