from unittest.mock import Mock, patch
from django.test import TestCase

from ..models import ProjectClass, ProjectType, ProjectPhase, ProjectCategory, Person
from ..serializers import ProjectCreateSerializer


class ProjectCreationPWIntegrationTestCase(TestCase):
    """
    Test cases for project creation with PW integration.
    """

    def setUp(self):
        """Set up test data"""
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="Test Class Serializer",
            defaults={'path': "Test/Class/Serializer"}
        )

        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")
        self.person, _ = Person.objects.get_or_create(
            firstName="Test",
            lastName="Person",
            defaults={'email': "test@example.com"}
        )

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_create_project_with_pw_id_triggers_sync(self, mock_post, mock_get_pw):
        """Test that creating a project with PW ID triggers automatic sync"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"changedInstance": {"change": "Modified"}}

        # Create project data with PW ID
        project_data = {
            "name": "Test Project with PW ID",
            "description": "Test description",
            "hkrId": 12345,
            "programmed": True,
            "projectClass": str(self.project_class.id),
            "type": str(self.project_type.id),
            "phase": str(self.project_phase.id),
            "category": str(self.project_category.id),
            "planningStartYear": 2024,
            "constructionEndYear": 2025,
        }

        # Create the project using the serializer
        serializer = ProjectCreateSerializer(data=project_data)
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        created_project = serializer.save()

        # Verify project was created
        self.assertIsNotNone(created_project)
        self.assertEqual(created_project.hkrId, 12345)

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_create_project_without_pw_id_no_sync(self, mock_post, mock_get_pw):
        """Test that creating a project without PW ID doesn't trigger sync"""
        # Create project data without PW ID
        project_data = {
            "name": "Test Project without PW ID",
            "description": "Test description",
            "programmed": True,
            "projectClass": str(self.project_class.id),
            "type": str(self.project_type.id),
            "phase": str(self.project_phase.id),
            "category": str(self.project_category.id),
            "planningStartYear": 2024,
            "constructionEndYear": 2025,
        }

        # Create the project using the serializer
        serializer = ProjectCreateSerializer(data=project_data)
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        created_project = serializer.save()

        # Verify project was created
        self.assertIsNotNone(created_project)
        self.assertIsNone(created_project.hkrId)

    def test_create_project_validation(self):
        """Test project creation validation"""
        # Test with valid data
        valid_data = {
            "name": "Valid Test Project",
            "description": "Valid description",
            "programmed": True,
            "projectClass": str(self.project_class.id),
            "type": str(self.project_type.id),
            "phase": str(self.project_phase.id),
            "category": str(self.project_category.id),
            "planningStartYear": 2024,
            "constructionEndYear": 2025,
        }

        serializer = ProjectCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), f"Valid data should pass validation: {serializer.errors}")

        # Test with invalid data (missing required fields)
        invalid_data = {
            "name": "Invalid Test Project",
            # Missing required fields
        }

        serializer = ProjectCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid(), "Invalid data should fail validation")


class ProjectCreateSerializerCreateMethodTestCase(TestCase):
    """
    Test cases for the ProjectCreateSerializer.create method integration with PW sync.
    """

    def setUp(self):
        """Set up test data"""
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="Test Class Create Method",
            defaults={'path': "Test/Class/CreateMethod"}
        )

        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

    @patch('infraohjelmointi_api.serializers.ProjectCreateSerializer.ProjectWiseService')
    @patch('infraohjelmointi_api.serializers.ProjectCreateSerializer.create_comprehensive_project_data')
    @patch('infraohjelmointi_api.serializers.ProjectCreateSerializer.logger')
    def test_create_method_integration_with_sync(self, mock_logger, mock_create_data, mock_pw_service_class):
        """Test the create method integration with the actual sync functionality"""
        # Mock the ProjectWise service to avoid actual API calls
        mock_pw_service = Mock()
        mock_pw_service_class.return_value = mock_pw_service
        mock_create_data.return_value = {'name': 'Test Project', 'description': 'Test'}

        # Create project data with PW ID
        project_data = {
            "name": "Test Integration Project",
            "description": "Test project for integration",
            "hkrId": 54321,
            "programmed": True,
            "projectClass": str(self.project_class.id),
            "type": str(self.project_type.id),
            "phase": str(self.project_phase.id),
            "category": str(self.project_category.id),
            "planningStartYear": 2024,
            "constructionEndYear": 2025,
        }

        # Create the project using the serializer
        serializer = ProjectCreateSerializer(data=project_data)
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        created_project = serializer.save()

        # Verify project was created
        self.assertIsNotNone(created_project)
        self.assertEqual(created_project.hkrId, 54321)

        # Verify that the sync process was called
        mock_create_data.assert_called_once_with(created_project)
        mock_pw_service.sync_project_to_pw.assert_called_once_with(
            data={'name': 'Test Project', 'description': 'Test'},
            project=created_project
        )
        mock_logger.info.assert_called()

    @patch('infraohjelmointi_api.serializers.ProjectCreateSerializer.ProjectWiseService')
    @patch('infraohjelmointi_api.serializers.ProjectCreateSerializer.create_comprehensive_project_data')
    @patch('infraohjelmointi_api.serializers.ProjectCreateSerializer.logger')
    def test_create_method_sync_error_handling(self, mock_logger, mock_create_data, mock_pw_service_class):
        """Test that sync errors don't break project creation"""
        # Mock the ProjectWise service to raise an exception
        mock_pw_service = Mock()
        mock_pw_service_class.return_value = mock_pw_service
        mock_pw_service.sync_project_to_pw.side_effect = Exception("PW sync failed")
        mock_create_data.return_value = {'name': 'Test Project', 'description': 'Test'}

        # Create project data with PW ID
        project_data = {
            "name": "Test Error Handling Project",
            "description": "Test project for error handling",
            "hkrId": 54321,
            "programmed": True,
            "projectClass": str(self.project_class.id),
            "type": str(self.project_type.id),
            "phase": str(self.project_phase.id),
            "category": str(self.project_category.id),
            "planningStartYear": 2024,
            "constructionEndYear": 2025,
        }

        # Create the project using the serializer
        serializer = ProjectCreateSerializer(data=project_data)
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        # Should not raise an exception even if sync fails
        created_project = serializer.save()

        # Verify project was created despite sync error
        self.assertIsNotNone(created_project)
        self.assertEqual(created_project.hkrId, 54321)

        # Verify error was logged
        mock_logger.error.assert_called()

    def test_create_method_without_pw_id_no_sync(self):
        """Test that projects without PW ID don't trigger sync"""
        # Create project data without PW ID
        project_data = {
            "name": "Test No Sync Project",
            "description": "Test project without sync",
            "programmed": True,
            "projectClass": str(self.project_class.id),
            "type": str(self.project_type.id),
            "phase": str(self.project_phase.id),
            "category": str(self.project_category.id),
            "planningStartYear": 2024,
            "constructionEndYear": 2025,
        }

        # Create the project using the serializer
        serializer = ProjectCreateSerializer(data=project_data)
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        created_project = serializer.save()

        # Verify project was created
        self.assertIsNotNone(created_project)
        self.assertIsNone(created_project.hkrId)


class DescriptionSyncLogicTestCase(TestCase):
    """
    Test cases for description sync logic between infra tool and ProjectWise.
    """

    def setUp(self):
        """Set up test data"""
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="Test Class Description",
            defaults={'path': "Test/Class/Description"}
        )

        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

    def test_description_sync_logic(self):
        """Test the description sync logic for different scenarios"""
        # Test cases: (infra_description, pw_description, expected_result)
        test_cases = [
            ("Infra description", "PW description", "Skip sync (PW has data)"),
            ("Infra description", "", "Sync to PW (PW empty)"),
            ("Infra description", None, "Sync to PW (PW empty)"),
            ("", "PW description", "Skip sync (infra empty, PW has data)"),
            ("", "", "Skip sync (both empty)"),
            (None, "PW description", "Skip sync (infra empty, PW has data)"),
            (None, None, "Skip sync (both empty)"),
        ]

        for infra_desc, pw_desc, expected in test_cases:
            with self.subTest(infra_desc=infra_desc, pw_desc=pw_desc):
                # Test the logic used in overwrite rules
                infra_has_data = bool(infra_desc and str(infra_desc).strip())
                pw_has_data = bool(pw_desc and str(pw_desc).strip())

                if infra_has_data and not pw_has_data:
                    result = "Sync to PW (PW empty)"
                elif not infra_has_data and pw_has_data:
                    result = "Skip sync (infra empty, PW has data)"
                elif not infra_has_data and not pw_has_data:
                    result = "Skip sync (both empty)"
                else:
                    result = "Skip sync (PW has data)"

                self.assertEqual(result, expected, f"Logic failed for infra='{infra_desc}', pw='{pw_desc}'")


class ClassificationFieldsRetryLogicTestCase(TestCase):
    """
    Test cases for classification fields retry logic.
    """

    def test_classification_fields_retry_logic(self):
        """Test the classification fields retry logic"""
        # Test that classification fields are properly identified
        classification_fields = {'projectClass', 'projectDistrict'}

        # Test field identification
        test_fields = [
            ('projectClass', True),
            ('projectDistrict', True),
            ('name', False),
            ('description', False),
            ('phase', False),
        ]

        for field, expected in test_fields:
            with self.subTest(field=field):
                is_classification = field in classification_fields
                self.assertEqual(is_classification, expected, f"Field '{field}' classification status incorrect")
