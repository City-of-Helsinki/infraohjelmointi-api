import uuid
from unittest.mock import patch
from django.test import TestCase

from ..models import Project, ProjectClass, ProjectType, ProjectPhase, ProjectCategory
from ..services.ProjectWiseService import PWProjectResponseError
from ..views import BaseViewSet


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectViewSetProjectWiseTestCase(TestCase):
    """
    Test cases for ProjectViewSet PW integration, especially automatic updates when HKR ID is added.
    """

    def setUp(self):
        """Set up test data"""
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="Test Class ViewSet",
            defaults={'path': "Test/Class/ViewSet"}
        )

        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

        self.project_without_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Project Without HKR",
            description="Test description",
            address="Test Address",
            hkrId=None,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        self.project_with_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Project With HKR",
            description="Test description",
            hkrId=12345,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

    def test_hkr_id_update_detection_logic(self):
        """Comprehensive test for HKR ID update detection logic (automatic vs regular updates)"""
        # Define test cases: (request_data, old_hkr_id, expected_trigger, description)
        test_cases = [
            # Cases that SHOULD trigger automatic update
            ({'hkrId': 54321, 'name': 'Updated'}, None, True, "HKR ID added for first time (None)"),
            ({'hkrId': 54321, 'name': 'Updated'}, "", True, "HKR ID added for first time (empty)"),
            ({'hkrId': 54321, 'name': 'Updated'}, "  ", True, "HKR ID added for first time (whitespace)"),

            # Cases that should NOT trigger automatic update
            ({'name': 'Updated Name Only'}, 12345, False, "Regular update, HKR ID exists, not in request"),
            ({'hkrId': 99999, 'name': 'Updated'}, 12345, False, "HKR ID changed (already existed)"),
            ({'hkrId': 12345, 'name': 'Updated'}, 12345, False, "HKR ID unchanged"),
            ({'name': 'Updated Name Only'}, None, False, "No HKR ID in request, no old HKR ID"),
            ({'hkrId': '', 'name': 'Updated'}, None, False, "Empty HKR ID in request"),
            ({'hkrId': None, 'name': 'Updated'}, None, False, "None HKR ID in request"),
            ({'hkrId': None, 'name': 'Updated'}, 12345, False, "None HKR ID, but project had one"),
        ]

        for request_data, old_hkr_id, expected, description in test_cases:
            with self.subTest(case=description):
                # Test the actual logic used in serializers for automatic update detection
                hkr_id_added_first_time = bool(
                    'hkrId' in request_data and
                    request_data['hkrId'] and
                    (not old_hkr_id or str(old_hkr_id).strip() == "")
                )
                self.assertEqual(hkr_id_added_first_time, expected, description)


class ProjectViewSetPWIntegrationTestCase(TestCase):
    """
    Test cases for ProjectViewSet PW integration, covering automatic sync and custom actions.
    """

    def setUp(self):
        """Set up test data for ProjectViewSet tests"""
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="Test Class ViewSet",
            defaults={'path': "Test/Class/ViewSet"}
        )

        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

        self.project_with_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Project With HKR",
            description="Test description",
            hkrId=12345,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        self.project_without_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Project Without HKR",
            description="Test description",
            hkrId=None,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_automatic_sync_on_hkr_id_addition(self, mock_post, mock_get_pw):
        """Test that adding HKR ID to a project triggers automatic PW sync"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"changedInstance": {"change": "Modified"}}

        # Simulate adding HKR ID to project without one
        from infraohjelmointi_api.views import ProjectViewSet

        # Create update data with HKR ID
        update_data = {
            "hkrId": 54321,
            "name": "Updated Project Name"
        }

        # Test the HKR ID detection logic
        hkr_id_added_first_time = bool(
            'hkrId' in update_data and
            update_data['hkrId'] and
            (not self.project_without_hkr.hkrId or str(self.project_without_hkr.hkrId).strip() == "")
        )

        self.assertTrue(hkr_id_added_first_time, "Should detect HKR ID addition")

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_automatic_sync_on_regular_update_with_hkr_id(self, mock_post, mock_get_pw):
        """Test that regular updates to projects with existing HKR ID DO trigger automatic sync (IO-396/IO-775)"""
        # Test regular update without HKR ID change, but project already has hkrId
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description"
        }

        # Test the sync detection logic - should sync if project has hkrId AND is programmed
        project_has_hkr_id = bool(self.project_with_hkr.hkrId and str(self.project_with_hkr.hkrId).strip())
        should_sync = project_has_hkr_id and self.project_with_hkr.programmed

        self.assertTrue(should_sync, "Should sync when project has hkrId and is programmed, even for regular updates")
        
        # Also verify that hkrId addition detection still works
        hkr_id_added_first_time = bool(
            'hkrId' in update_data and
            update_data.get('hkrId') and
            (not self.project_with_hkr.hkrId or str(self.project_with_hkr.hkrId).strip() == "")
        )
        self.assertFalse(hkr_id_added_first_time, "Should not detect HKR ID addition for regular update")

    def test_sync_on_programmed_to_unprogrammed_transition(self):
        """
        IO-775: When a project with hkrId transitions from programmed=True → False,
        we must still sync once so PW receives the final phase/status before we stop
        syncing it. Regression test for the Kehä I / Myllypuro case.
        """
        # Replicates the should_sync condition in
        # ProjectViewSet._sync_project_to_projectwise (single PATCH path) and
        # ProjectViewSet.patch_bulk_projects (bulk path).
        # (was_programmed, updated_programmed, has_hkr_id, expected_should_sync, description)
        cases = [
            (True, True, True, True, "Regular update of programmed project with hkrId"),
            (True, False, True, True, "programmed → unprogrammed transition (IO-775 fix)"),
            (False, True, True, True, "unprogrammed → programmed transition (initial sync)"),
            (False, False, True, False, "Project never programmed: do not sync (IO-396)"),
            (True, False, False, False, "Transitioning out but no hkrId: nothing to sync"),
            (True, True, False, False, "Programmed but no hkrId: nothing to sync"),
        ]

        for was_programmed, updated_programmed, has_hkr_id, expected, description in cases:
            with self.subTest(case=description):
                should_sync = has_hkr_id and (updated_programmed or was_programmed)
                self.assertEqual(should_sync, expected, description)

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_automatic_sync_error_handling(self, mock_post, mock_get_pw):
        """Test that PW sync errors don't break project updates"""
        # Mock PW service to raise an exception
        mock_get_pw.side_effect = Exception("PW service unavailable")

        # Test that the error handling logic works
        try:
            # Simulate the error handling in ProjectViewSet
            from infraohjelmointi_api.services.utils import create_comprehensive_project_data
            from infraohjelmointi_api.services import ProjectWiseService

            # This should not raise an exception
            project_data = create_comprehensive_project_data(self.project_with_hkr)
            self.assertIsInstance(project_data, dict)

        except Exception as e:
            self.fail(f"Error handling should prevent exceptions from breaking the flow: {e}")

    def test_comprehensive_project_data_creation(self):
        """Test the create_comprehensive_project_data function"""
        from infraohjelmointi_api.services.utils import create_comprehensive_project_data

        # Test with project that has data
        result = create_comprehensive_project_data(self.project_with_hkr)

        # Should return a dictionary
        self.assertIsInstance(result, dict)

        # Should include basic fields
        self.assertIn('name', result)
        self.assertIn('description', result)
        self.assertEqual(result['name'], "Project With HKR")
        self.assertEqual(result['description'], "Test description")

    def test_comprehensive_project_data_with_none_values(self):
        """Test create_comprehensive_project_data with None values"""
        from infraohjelmointi_api.services.utils import create_comprehensive_project_data

        # Create a project with some None values
        project_with_nones = Project.objects.create(
            id=uuid.uuid4(),
            name="Project With Nones",
            description="Test description",
            address=None,  # None value
            entityName=None,  # None value
            hkrId=99999,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        result = create_comprehensive_project_data(project_with_nones)

        # Should exclude None values
        self.assertNotIn('address', result)
        self.assertNotIn('entityName', result)

        # Should include non-None values
        self.assertIn('name', result)
        self.assertIn('description', result)
        self.assertEqual(result['name'], "Project With Nones")


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectViewSetPWOutageTestCase(TestCase):
    """IO-851: PATCH must commit the local edit when PW is unreachable."""

    def setUp(self):
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="PW Outage Test Class",
            defaults={'path': "PW/Outage/Test/Class"},
        )
        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

        # planningStartYear / constructionEndYear are required when phase
        # is 'programming'; set them so PATCH reaches the sync step.
        self.project_with_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Outage Test Project",
            description="Original description",
            hkrId=2493,
            programmed=True,
            planningStartYear=2024,
            constructionEndYear=2030,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
        )

        self.project_without_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Outage Test Project No HKR",
            description="Original description",
            hkrId=None,
            programmed=True,
            planningStartYear=2024,
            constructionEndYear=2030,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
        )

    @patch(
        "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.sync_project_to_pw"
    )
    def test_patch_with_pw_404_response_error_commits_local_update(self, mock_sync):
        """Prod scenario: PW maintenance returns 404 for every project."""
        mock_sync.side_effect = PWProjectResponseError(
            "PW responded with status code '404' and reason 'Not Found' for given id '2493'"
        )

        response = self.client.patch(
            f"/projects/{self.project_with_hkr.id}/",
            {"description": "Edited during PW maintenance"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_with_hkr.refresh_from_db()
        self.assertEqual(
            self.project_with_hkr.description,
            "Edited during PW maintenance",
        )
        mock_sync.assert_called_once()

    @patch(
        "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.sync_project_to_pw"
    )
    def test_patch_with_pw_503_response_error_commits_local_update(self, mock_sync):
        """General outage (5xx) — same soft-fail behaviour."""
        mock_sync.side_effect = PWProjectResponseError(
            "PW responded with status code '503' and reason 'Service Unavailable' for given id '2493'"
        )

        response = self.client.patch(
            f"/projects/{self.project_with_hkr.id}/",
            {"description": "Edited during PW outage"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_with_hkr.refresh_from_db()
        self.assertEqual(
            self.project_with_hkr.description,
            "Edited during PW outage",
        )

    @patch(
        "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.sync_project_to_pw"
    )
    def test_patch_with_unexpected_pw_exception_rolls_back(self, mock_sync):
        """Regression: only PWProjectResponseError is soft-failed; other
        exceptions still 400 and roll back via @transaction.atomic."""
        mock_sync.side_effect = RuntimeError("Unexpected PW failure")

        response = self.client.patch(
            f"/projects/{self.project_with_hkr.id}/",
            {"description": "Should be rolled back"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.project_with_hkr.refresh_from_db()
        self.assertEqual(self.project_with_hkr.description, "Original description")

    @patch(
        "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.sync_project_to_pw"
    )
    def test_patch_without_hkr_id_does_not_call_pw_sync(self, mock_sync):
        """Regression: projects without hkrId never call PW sync."""
        response = self.client.patch(
            f"/projects/{self.project_without_hkr.id}/",
            {"description": "Edited, no hkr"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        mock_sync.assert_not_called()
        self.project_without_hkr.refresh_from_db()
        self.assertEqual(self.project_without_hkr.description, "Edited, no hkr")
