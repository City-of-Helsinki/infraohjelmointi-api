from infraohjelmointi_api.serializers.PlanningPhaseSerializer import PlanningPhaseSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class PlanningPhaseViewSet(CachedLookupViewSet):
    """API endpoint for planning phases (cached)."""

    serializer_class = PlanningPhaseSerializer
