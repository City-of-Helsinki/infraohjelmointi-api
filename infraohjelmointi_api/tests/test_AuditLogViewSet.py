from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from unittest.mock import patch

from infraohjelmointi_api.models import AuditLog, Project, User
from infraohjelmointi_api.views.AuditLogViewSet import AuditLogViewSet
from infraohjelmointi_api.serializers.AuditLogSerializer import AuditLogSerializer

User = get_user_model()


@patch.object(AuditLogViewSet, "authentication_classes", new=[])
@patch.object(AuditLogViewSet, "permission_classes", new=[])
class AuditLogViewSetTestCase(TestCase):
    """Test AuditLogViewSet methods and functionality"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()

        # Create test user
        self.user = User.objects.create(
            first_name='Test',
            last_name='User',
            username='testuser',
            email='test@example.com'
        )

        # Create test project
        self.project = Project.objects.create(
            name="Test Project",
            hkrId=12345,
            description="Test project description"
        )

        # Create test audit log entry
        self.audit_log = AuditLog.objects.create(
            actor=self.user,
            operation="CREATE",
            log_level="INFO",
            origin="infrahankkeiden_ohjelmointi",
            status="SUCCESS",
            project=self.project,
            old_values={"name": "Old Name"},
            new_values={"name": "New Name"},
            endpoint="/api/projects/"
        )

    def test_get_queryset_returns_audit_logs(self):
        """Test that get_queryset returns audit logs"""
        viewset = AuditLogViewSet()
        queryset = viewset.get_queryset()

        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.audit_log, queryset)

    def test_serializer_includes_related_fields(self):
        """Test that serializer includes related field data"""
        serializer = AuditLogSerializer(self.audit_log)
        data = serializer.data

        # Check that related fields are included
        self.assertEqual(data['actor_username'], 'testuser')
        self.assertEqual(data['actor_first_name'], 'Test')
        self.assertEqual(data['actor_last_name'], 'User')
        self.assertEqual(data['project_name'], 'Test Project')
        self.assertEqual(data['project_hkr_id'], '12345')

    def test_list_action_returns_paginated_results(self):
        """Test that list action returns paginated results"""
        request = self.factory.get('/audit-logs/')
        view = AuditLogViewSet.as_view({'get': 'list'})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_action_returns_single_audit_log(self):
        """Test that retrieve action returns single audit log"""
        request = self.factory.get(f'/audit-logs/{self.audit_log.id}/')
        view = AuditLogViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=self.audit_log.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], str(self.audit_log.id))
        self.assertEqual(response.data['operation'], 'CREATE')
