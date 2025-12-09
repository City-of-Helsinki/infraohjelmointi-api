from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.TalpaProjectOpeningSerializer import TalpaAssetClassSerializer
from infraohjelmointi_api.models import TalpaAssetClass
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from overrides import override
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication


class TalpaAssetClassFilter(django_filters.FilterSet):
    """Filter for TalpaAssetClass"""
    category = django_filters.CharFilter(field_name="category", lookup_expr="icontains")
    isActive = django_filters.BooleanFilter(field_name="isActive")

    class Meta:
        model = TalpaAssetClass
        fields = ["category", "isActive"]


class TalpaAssetClassViewSet(BaseViewSet):
    """
    API endpoint for Talpa asset classes (dropdown data)
    """

    serializer_class = TalpaAssetClassSerializer
    http_method_names = ["get"]  # Read-only
    filter_backends = [DjangoFilterBackend]
    filterset_class = TalpaAssetClassFilter
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @override
    def get_queryset(self):
        """Filter to active only by default"""
        queryset = TalpaAssetClass.objects.all()
        # Filter by isActive if not explicitly requested
        is_active = self.request.query_params.get("isActive", None)
        if is_active is None:
            queryset = queryset.filter(isActive=True)
        return queryset.order_by("componentClass")

