from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from overrides import override
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from helusers.oidc import ApiTokenAuthentication

from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.models import TalpaProjectNumberRange
from infraohjelmointi_api.serializers.TalpaProjectOpeningSerializer import (
    TalpaProjectNumberRangeSerializer,
)

class TalpaProjectNumberRangeFilter(django_filters.FilterSet):
    """Filter for TalpaProjectNumberRange"""
    projectTypePrefix = django_filters.CharFilter(field_name="projectTypePrefix")
    budgetAccount = django_filters.CharFilter(field_name="budgetAccount", lookup_expr="icontains")
    majorDistrict = django_filters.CharFilter(field_name="majorDistrict")
    area = django_filters.CharFilter(field_name="area", lookup_expr="icontains")
    unit = django_filters.CharFilter(field_name="unit")
    isActive = django_filters.BooleanFilter(field_name="isActive")

    class Meta:
        model = TalpaProjectNumberRange
        fields = ["projectTypePrefix", "budgetAccount", "majorDistrict", "area", "unit", "isActive"]


class TalpaProjectNumberRangeViewSet(BaseViewSet):
    """
    API endpoint for Talpa project number ranges (dropdown data)
    """

    serializer_class = TalpaProjectNumberRangeSerializer
    http_method_names = ["get"]  # Read-only
    filter_backends = [DjangoFilterBackend]
    filterset_class = TalpaProjectNumberRangeFilter
    authentication_classes = [ApiTokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self):
        """Filter to active only by default"""
        queryset = TalpaProjectNumberRange.objects.all()
        # Filter by isActive if not explicitly requested
        is_active = self.request.query_params.get("isActive", None)
        if is_active is None:
            queryset = queryset.filter(isActive=True)
        return queryset.order_by("projectTypePrefix", "budgetAccount", "rangeStart")

