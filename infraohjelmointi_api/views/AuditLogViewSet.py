from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from infraohjelmointi_api.models import AuditLog
from infraohjelmointi_api.serializers.AuditLogSerializer import AuditLogSerializer
from infraohjelmointi_api.paginations import StandardResultsSetPagination
from infraohjelmointi_api.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated


class AuditLogFilter(django_filters.FilterSet):
    """
    Filter for AuditLog entries
    """
    operation = django_filters.ChoiceFilter(choices=AuditLog.OPERATION_CHOICES)
    log_level = django_filters.ChoiceFilter(choices=AuditLog.LOG_LEVEL_CHOICES)
    status = django_filters.ChoiceFilter(choices=AuditLog.STATUS_CHOICES)
    origin = django_filters.CharFilter(lookup_expr='icontains')
    endpoint = django_filters.CharFilter(lookup_expr='icontains')
    created_date_from = django_filters.DateTimeFilter(field_name='createdDate', lookup_expr='gte')
    created_date_to = django_filters.DateTimeFilter(field_name='createdDate', lookup_expr='lte')
    project_id = django_filters.UUIDFilter(field_name='project__id')
    actor_id = django_filters.UUIDFilter(field_name='actor__id')

    class Meta:
        model = AuditLog
        fields = [
            'operation', 'log_level', 'status', 'origin', 'endpoint',
            'created_date_from', 'created_date_to', 'project_id', 'actor_id'
        ]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows audit log entries to be viewed.
    Read-only access for admin users to view system audit logs.
    """

    permission_classes = [
        IsAuthenticated & IsAdmin
    ]

    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = AuditLogFilter
    serializer_class = AuditLogSerializer
    ordering_fields = ['createdDate', 'updatedDate', 'operation', 'log_level', 'status']
    ordering = ['-createdDate']  # Most recent first by default
    search_fields = ['endpoint', 'origin', 'actor__username', 'project__name']

    def get_queryset(self):
        """
        Return audit log entries ordered by creation date (newest first)
        """
        return AuditLog.objects.select_related(
            'actor', 'project', 'project_group', 'project_class'
        ).all()
