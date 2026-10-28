from infraohjelmointi_api.models import ProjectPhase
from infraohjelmointi_api.serializers.ProjectPhaseDetailSerializer import ProjectPhaseDetailSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectPhaseDetailViewSet(CachedLookupViewSet):
    """API endpoint for project phase details (cached)."""

    serializer_class = ProjectPhaseDetailSerializer
    project_field = 'phaseDetail'
    # Each detail nests its projectPhase.
    cache_depends_on = (ProjectPhase,)
