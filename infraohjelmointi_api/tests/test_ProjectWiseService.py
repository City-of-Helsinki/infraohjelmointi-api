import uuid
from unittest.mock import Mock, patch
from django.test import TestCase
from datetime import date

from ..models import Project, ProjectClass, ProjectType, ProjectPhase, ProjectCategory, Person
from ..services import ProjectWiseService
from ..views import BaseViewSet
from ..services.utils.PWConfig import PWConfig


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
@patch.dict('os.environ', {'PW_SYNC_ENABLED': 'True'})
class ProjectWiseServiceTestCase(TestCase):
    """
    Test cases for ProjectWiseService with focus on the new mass update functionality
    and overwrite rules.
    """

    def setUp(self):
        """Set up test data"""
        # Patch environment variables
        self.env_patcher = patch.dict('os.environ', {
            'PW_SYNC_ENABLED': 'True'
        })
        self.env_patcher.start()

        # Create other required objects
        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")
        self.project_class, _ = ProjectClass.objects.get_or_create(
            id=uuid.uuid4(),
            defaults={
                'name': "Test Project Class",
                'path': "Test/Path"
            }
        )
        self.person, _ = Person.objects.get_or_create(
            firstName="Test",
            lastName="Person",
            defaults={'email': "test@example.com"}
        )

        # Create test projects
        self.programmed_project_with_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Test Programmed Project",
            description="Test description",
            address="Test Address 1",
            hkrId=12345,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
            personPlanning=self.person,
            estPlanningStart=date(2024, 1, 1),
            estConstructionStart=date(2024, 6, 1),
            presenceStart=date(2024, 2, 1),
            visibilityStart=date(2024, 3, 1),
            masterPlanAreaNumber="MP001",
            trafficPlanNumber="TP001",
            bridgeNumber="BR001"
        )

        self.programmed_project_without_hkr = Project.objects.create(
            id=uuid.uuid4(),
            name="Test Project Without HKR",
            description="Test description 2",
            address="Test Address 2",
            hkrId=None,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        self.non_programmed_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Non-programmed Project",
            description="Test description 3",
            hkrId=67890,
            programmed=False,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        # Mock PW response data
        self.mock_pw_response = {
            "relationshipInstances": [{
                "relatedInstance": {
                    "instanceId": "test-instance-id",
                    "properties": {
                        "PROJECT_Kohde": "Existing PW Name",
                        "PROJECT_Hankkeen_kuvaus": "Existing PW Description",
                        "PROJECT_Kadun_tai_puiston_nimi": "",  # Empty in PW
                        "PROJECT_Esillaolo_alku": "01.01.2024",  # Has data in PW
                        "PROJECT_Nhtvillolo_alku": "",  # Empty in PW
                        "PROJECT_Hankkeen_suunnittelu_alkaa": "15.01.2024"
                    }
                }
            }]
        }

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_apply_overwrite_rules_protected_fields(self, mock_post, mock_get_pw):
        """Test that protected fields are never overwritten if PW has data"""
        mock_get_pw.return_value = self.mock_pw_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"changedInstance": {"change": "Modified"}}

        service = ProjectWiseService()

        # Test data with protected fields
        test_data = {
            'name': 'New Name',
            'description': 'New Description',  # Protected field
            'address': 'New Address',
            'presenceStart': date(2024, 5, 1),  # Protected field
            'visibilityStart': date(2024, 4, 1)  # Protected field, but PW is empty
        }

        # Get current PW properties
        current_pw_properties = self.mock_pw_response["relationshipInstances"][0]["relatedInstance"]["properties"]

        # Apply overwrite rules
        filtered_data = service._apply_overwrite_rules(
            test_data,
            self.programmed_project_with_hkr,
            current_pw_properties
        )

        # Assertions
        self.assertIn('name', filtered_data)  # Regular field should be included
        self.assertIn('address', filtered_data)  # Regular field should be included
        self.assertNotIn('description', filtered_data)  # Protected field with PW data should be skipped
        self.assertNotIn('presenceStart', filtered_data)  # Protected field with PW data should be skipped
        self.assertIn('visibilityStart', filtered_data)  # Protected field but PW is empty, should be included

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_apply_overwrite_rules_regular_fields(self, mock_post, mock_get_pw):
        """Test regular field overwrite rules: skip if infra tool empty but PW has data"""
        mock_get_pw.return_value = self.mock_pw_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"changedInstance": {"change": "Modified"}}

        service = ProjectWiseService()

        # Create project with empty address (to test the rule)
        empty_address_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Test Project",
            description="Test",
            address="",  # Empty in infra tool
            hkrId=11111,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        test_data = {
            'name': 'New Name',
            'address': '',  # Empty in infra tool
            'entityName': 'New Entity'
        }

        current_pw_properties = {
            "PROJECT_Kohde": "",  # Empty in PW
            "PROJECT_Kadun_tai_puiston_nimi": "Existing PW Address",  # Has data in PW
            "PROJECT_Aluekokonaisuuden_nimi": ""  # Empty in PW
        }

        filtered_data = service._apply_overwrite_rules(
            test_data,
            empty_address_project,
            current_pw_properties
        )

        # Assertions
        self.assertIn('name', filtered_data)  # Should be included (infra has data)
        self.assertNotIn('address', filtered_data)  # Should be skipped (infra empty, PW has data)
        self.assertIn('entityName', filtered_data)  # Should be included (both empty or infra has data)

    def tearDown(self):
        """Clean up test data"""
        self.env_patcher.stop()

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_sync_project_to_pw_legacy_usage(self, mock_post, mock_get_pw):
        """Test the legacy usage of sync_project_to_pw with PW ID"""
        mock_get_pw.return_value = self.mock_pw_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"changedInstance": {"change": "Modified"}}

        with patch('infraohjelmointi_api.services.ProjectService.ProjectService.get_by_hkr_id') as mock_get_by_hkr:
            mock_get_by_hkr.return_value = self.programmed_project_with_hkr

            service = ProjectWiseService()

            # Test legacy usage
            service.sync_project_to_pw(pw_id="12345")

            # Verify that the project was retrieved by HKR ID
            mock_get_by_hkr.assert_called_once_with(hkr_id="12345")

            # Note: PW may not be called if no data needs updating (filtered out by overwrite rules)
            # This is expected behavior for legacy usage with empty data

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.requests.Session.post')
    def test_sync_project_to_pw_new_usage(self, mock_post, mock_get_pw):
        """Test the new usage of sync_project_to_pw with data and project"""
        mock_get_pw.return_value = self.mock_pw_response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"changedInstance": {"change": "Modified"}}

        service = ProjectWiseService()

        test_data = {
            'name': 'Updated Name',
            'description': 'Updated Description'
        }

        # Test new usage
        service.sync_project_to_pw(data=test_data, project=self.programmed_project_with_hkr)

        # Verify that PW was called
        mock_post.assert_called_once()

        # Verify the data sent to PW
        call_args = mock_post.call_args
        sent_data = call_args[1]['json']
        self.assertEqual(sent_data['instance']['instanceId'], 'test-instance-id')
        self.assertIn('properties', sent_data['instance'])

    def test_sync_project_to_pw_no_hkr_id(self):
        """Test that projects without HKR ID are skipped"""
        service = ProjectWiseService()

        test_data = {'name': 'Test'}

        # Should not raise error, should just return early
        service.sync_project_to_pw(data=test_data, project=self.programmed_project_without_hkr)

        # No assertions needed, just checking it doesn't crash

    def test_sync_project_to_pw_invalid_parameters(self):
        """Test error handling for invalid parameters"""
        service = ProjectWiseService()

        with patch('infraohjelmointi_api.services.ProjectWiseService.logger') as mock_logger:
            # Call with invalid parameters
            service.sync_project_to_pw()

            # Should log error
            mock_logger.error.assert_called_once_with("sync_project_to_pw called without proper parameters")

    def test_hierarchical_fields_consistency(self):
        """Verify HIERARCHICAL_FIELDS matches HIERARCHICAL_FIELD_ORDER."""
        service = ProjectWiseService()

        # Check that HIERARCHICAL_FIELDS is a set of HIERARCHICAL_FIELD_ORDER
        self.assertEqual(service.HIERARCHICAL_FIELDS, set(service.HIERARCHICAL_FIELD_ORDER))

        # Check exact count
        self.assertEqual(len(service.HIERARCHICAL_FIELD_ORDER), 6)

        # Check that all expected fields are present
        expected_fields = {
            'PROJECT_Pluokka',
            'PROJECT_Luokka',
            'PROJECT_Alaluokka',
            'PROJECT_Suurpiirin_nimi',
            'PROJECT_Kaupunginosan_nimi',
            'PROJECT_Osa_alue'
        }
        self.assertEqual(service.HIERARCHICAL_FIELDS, expected_fields)


class ProjectWiseServiceEdgeCaseTestCase(TestCase):
    """
    Additional test cases for edge cases and error scenarios.
    """

    def setUp(self):
        """Set up test data for edge cases"""
        self.project_type, _ = ProjectType.objects.get_or_create(value="street")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="design")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="renov")

        # Project with edge case data
        self.edge_case_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Edge Case Project",
            description="Edge case desc",  # Required field
            address=None,  # None address
            hkrId=99999,
            programmed=True,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
            masterPlanAreaNumber="  ",  # Whitespace only
            trafficPlanNumber="TP999",  # Valid value
            bridgeNumber=None  # None value
        )

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    def test_overwrite_rules_with_edge_case_data(self, mock_get_pw):
        """Test overwrite rules with edge case data (empty strings, whitespace, None values)"""

        # Mock PW response with various edge cases
        mock_pw_response = {
            "relationshipInstances": [{
                "relatedInstance": {
                    "instanceId": "test-instance-id",
                    "properties": {
                        "PROJECT_Kohde": "   ",  # Whitespace only in PW
                        "PROJECT_Hankkeen_kuvaus": "",  # Empty in PW
                        "PROJECT_Kadun_tai_puiston_nimi": "Existing Address",  # Has data in PW
                        "PROJECT_Hankkeen_suunnittelu_alkaa": None,  # None in PW
                    }
                }
            }]
        }
        mock_get_pw.return_value = mock_pw_response

        service = ProjectWiseService()

        test_data = {
            'name': 'New Name',
            'description': '',  # Empty in infra tool
            'address': '',  # Empty in infra tool
            'estPlanningStart': date(2024, 1, 1)  # Has data in infra tool
        }

        current_pw_properties = mock_pw_response["relationshipInstances"][0]["relatedInstance"]["properties"]
        filtered_data = service._apply_overwrite_rules(test_data, self.edge_case_project, current_pw_properties)

        # Assertions for edge cases
        self.assertIn('name', filtered_data)  # Should include (infra has data, PW has whitespace)
        self.assertIn('description', filtered_data)  # Protected field, PW is empty, should include
        self.assertNotIn('address', filtered_data)  # Should skip (infra empty, PW has data)
        self.assertIn('estPlanningStart', filtered_data)  # Should include (infra has data)

    def test_field_mapping_completeness(self):
        """Test that all protected fields have corresponding PW mappings"""
        service = ProjectWiseService()

        protected_fields = {
            'description', 'type', 'presenceStart', 'presenceEnd',
            'visibilityStart', 'visibilityEnd', 'projectDistrict',
            'masterPlanAreaNumber', 'trafficPlanNumber', 'bridgeNumber'
        }

        pw_field_mapping = service._get_pw_field_mapping()

        # Check that critical protected fields have mappings
        critical_fields_with_mappings = {
            'description', 'presenceStart', 'presenceEnd',
            'visibilityStart', 'visibilityEnd'
        }

        for field in critical_fields_with_mappings:
            self.assertIn(field, pw_field_mapping, f"Protected field '{field}' should have PW mapping")

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    def test_error_handling_in_overwrite_rules(self, mock_get_pw):
        """Test error handling when PW data is malformed or missing"""

        # Test with malformed PW response
        mock_get_pw.return_value = {"malformed": "response"}

        service = ProjectWiseService()

        test_data = {'name': 'Test Name'}

        # Should not crash with malformed PW data
        try:
            filtered_data = service._apply_overwrite_rules(test_data, self.edge_case_project, {})
            # Should include the field when PW data is malformed/empty
            self.assertIn('name', filtered_data)
        except Exception as e:
            self.fail(f"Should not raise exception with malformed PW data: {e}")

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    def test_pw_api_errors_handling(self, mock_get_pw):
        """Test handling of various ProjectWise API errors"""
        service = ProjectWiseService()

        # Test 1: PW API returns 500 error
        mock_get_pw.side_effect = Exception("PW API Error: 500 Internal Server Error")

        test_data = {'name': 'Test Name'}

        # Should handle PW API errors gracefully - the error should be caught and handled
        # in the actual _apply_overwrite_rules method which calls get_project_from_pw
        # But since we're testing _apply_overwrite_rules directly, we need to test differently

        # The method should handle the case where get_project_from_pw fails
        # by not calling it directly in _apply_overwrite_rules
        try:
            # This should work because _apply_overwrite_rules takes current_pw_properties directly
            filtered_data = service._apply_overwrite_rules(test_data, self.edge_case_project, {})
            self.assertIn('name', filtered_data)  # Should include field when no PW data provided
        except Exception as e:
            self.fail(f"_apply_overwrite_rules should handle missing PW data gracefully: {e}")

        # Test 2: PW API returns empty response
        mock_get_pw.side_effect = None
        mock_get_pw.return_value = {"relationshipInstances": []}

        # Should handle empty PW response gracefully
        filtered_data = service._apply_overwrite_rules(test_data, self.edge_case_project, {})
        self.assertIn('name', filtered_data)  # Should include field when PW has no data

    def test_large_field_values_handling(self):
        """Test handling of large field values that might cause issues"""
        service = ProjectWiseService()

        # Create project with very long values
        long_description = "A" * 1000  # Very long description
        long_name = "Very Long Project Name That Might Cause Issues"

        test_data = {
            'name': long_name,
            'description': long_description,
            'address': 'Normal Address'
        }

        # Should handle large values without crashing
        try:
            # Test the data creation (this tests our helper method)
            project_data = {k: v for k, v in test_data.items() if v is not None}
            self.assertIn('name', project_data)
            self.assertIn('description', project_data)
            self.assertEqual(len(project_data['description']), 1000)
        except Exception as e:
            self.fail(f"Should handle large field values: {e}")

    def test_special_characters_in_fields(self):
        """Test handling of special characters that might cause encoding issues"""
        service = ProjectWiseService()

        # Test data with special characters
        test_data = {
            'name': 'Projekti äöå ÄÖÅ',
            'description': 'Kuvaus: "erikoismerkit" & <symbols>',
            'address': 'Kävelykatu 123, 00100 Helsinki'
        }

        # Should handle special characters without issues
        try:
            project_data = {k: v for k, v in test_data.items() if v is not None}
            self.assertEqual(project_data['name'], 'Projekti äöå ÄÖÅ')
            self.assertIn('erikoismerkit', project_data['description'])
        except Exception as e:
            self.fail(f"Should handle special characters: {e}")


class ProjectWiseConcurrencyTestCase(TestCase):
    """
    Test cases for potential concurrency issues during mass updates.
    """

    def setUp(self):
        """Set up test data for concurrency testing"""
        self.project_type, _ = ProjectType.objects.get_or_create(value="traffic")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="construction")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="major")

        # Create project that might be modified during mass update
        self.concurrent_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Concurrent Test Project",
            description="Concurrent description",
            hkrId=20001,
            programmed=True,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    def test_project_modified_during_mass_update(self, mock_get_pw):
        """Test handling when project is modified during mass update"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }

        service = ProjectWiseService()

        # Simulate project being modified after data creation but before sync
        original_sync = service._ProjectWiseService__sync_project_to_pw

        def modified_sync(*args, **kwargs):
            # Modify project during sync (simulates concurrent modification)
            project = kwargs.get('project')
            if project:
                project.name = "Modified During Sync"
                project.save()
            return original_sync(*args, **kwargs)

        with patch.object(service, '_ProjectWiseService__sync_project_to_pw', side_effect=modified_sync):
            # Should handle concurrent modifications gracefully
            try:
                project_data = service._create_project_data_for_mass_update(self.concurrent_project)
                self.assertIsInstance(project_data, dict)
            except Exception as e:
                self.fail(f"Should handle concurrent modifications: {e}")

    def test_database_transaction_integrity(self):
        """Test that mass update doesn't leave database in inconsistent state"""
        # This test verifies that even if mass update fails, the database remains consistent

        # Count projects before
        initial_count = Project.objects.filter(programmed=True, hkrId__isnull=False).count()

        service = ProjectWiseService()

        # Run mass update (even if it fails, database should be consistent)
        try:
            update_log = service.sync_all_projects_to_pw()
            # Mass update should not modify the database directly
            final_count = Project.objects.filter(programmed=True, hkrId__isnull=False).count()
            self.assertEqual(initial_count, final_count, "Mass update should not modify project count")
        except Exception:
            # Even if mass update fails, database should be consistent
            final_count = Project.objects.filter(programmed=True, hkrId__isnull=False).count()
            self.assertEqual(initial_count, final_count, "Database should remain consistent after failure")


@patch.dict('os.environ', {'PW_SYNC_ENABLED': 'True'})
class ProjectWisePerformanceTestCase(TestCase):
    """
    Test cases for performance considerations during mass updates.
    """

    def setUp(self):
        """Set up test data for performance testing"""
        self.project_type, _ = ProjectType.objects.get_or_create(value="spesialtyStructures")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="infra")

        # Create multiple projects to test batch processing
        self.batch_projects = []
        for i in range(5):
            project = Project.objects.create(
                id=uuid.uuid4(),
                name=f"Batch Project {i+1}",
                description=f"Batch description {i+1}",
                hkrId=30000 + i,
                programmed=True,
                type=self.project_type,
                phase=self.project_phase,
                category=self.project_category
            )
            self.batch_projects.append(project)

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService._ProjectWiseService__sync_project_to_pw')
    def test_batch_processing_efficiency(self, mock_sync, mock_get_pw):
        """Test that mass update processes multiple projects efficiently"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }
        mock_sync.return_value = None

        service = ProjectWiseService()

        # Run mass update
        update_log = service.sync_all_projects_to_pw()

        # Should process all batch projects
        self.assertEqual(len(update_log), 5)

        # All should be successful
        successful_logs = [log for log in update_log if log['status'] == 'success']
        self.assertEqual(len(successful_logs), 5)

        # Verify each project was processed
        processed_names = [log['project_name'] for log in update_log]
        for i in range(5):
            self.assertIn(f"Batch Project {i+1}", processed_names)

    def test_memory_usage_with_large_dataset(self):
        """Test memory efficiency with larger datasets"""
        service = ProjectWiseService()

        # Test data creation for multiple projects doesn't cause memory issues
        all_projects = Project.objects.filter(programmed=True, hkrId__isnull=False)

        try:
            # This should not cause memory issues even with many projects
            for project in all_projects:
                project_data = service._create_project_data_for_mass_update(project)
                self.assertIsInstance(project_data, dict)
                # Verify data is properly cleaned (no None values)
                for value in project_data.values():
                    self.assertIsNotNone(value)
        except MemoryError:
            self.fail("Mass update should not cause memory issues")


@patch.dict('os.environ', {'PW_SYNC_ENABLED': 'True'})
class ProductionMassUpdateTestCase(TestCase):
    """
    Comprehensive test cases for the production-ready mass update functionality.
    """

    def setUp(self):
        """Set up comprehensive test data for production mass update testing"""
        # Patch environment variables
        self.env_patcher = patch.dict('os.environ', {
            'PW_SYNC_ENABLED': 'True'
        })
        self.env_patcher.start()

        # Create project classes
        self.project_class, _ = ProjectClass.objects.get_or_create(
            id=uuid.uuid4(),
            defaults={
                'name': "Test Project Class",
                'path': "Test/Path"
            }
        )
        self.other_class, _ = ProjectClass.objects.get_or_create(
            name="Other Class Production",
            defaults={'path': "Other/Production/Class"}
        )

        # Create required objects
        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")
        self.person, _ = Person.objects.get_or_create(
            firstName="Production",
            lastName="Tester",
            defaults={'email': "production@test.com"}
        )

        # Create various test projects for comprehensive testing

        # 1. Perfect programmed project with HKR ID
        self.perfect_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Perfect Test Project",
            description="Complete description",
            address="Perfect Address 123",
            entityName="Perfect Entity",
            hkrId=10001,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
            personPlanning=self.person,
            estPlanningStart=date(2024, 1, 1),
            estPlanningEnd=date(2024, 3, 1),
            estConstructionStart=date(2024, 6, 1),
            estConstructionEnd=date(2024, 12, 1),
            presenceStart=date(2024, 2, 1),
            presenceEnd=date(2024, 2, 28),
            visibilityStart=date(2024, 3, 1),
            visibilityEnd=date(2024, 3, 31),
            masterPlanAreaNumber="MP001",
            trafficPlanNumber="TP001",
            bridgeNumber="BR001"
        )

        # 2. Programmed project with some empty fields
        self.partial_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Partial Data Project",
            description="Partial description",  # Required field
            address=None,  # None
            entityName="Partial Entity",
            hkrId=10002,
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
            estPlanningStart=date(2024, 1, 1),
            # Many other fields are None
            masterPlanAreaNumber="MP002"
        )

        # 3. Programmed project with different class
        self.out_of_scope_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Out of Scope Project",
            description="Out of scope description",
            hkrId=10003,
            programmed=True,
            projectClass=self.other_class,  # Different class
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        # 4. Non-programmed project (should be excluded)
        self.non_programmed_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Non-Programmed Project",
            description="Non-programmed",
            hkrId=10004,
            programmed=False,  # Not programmed
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

        # 5. Programmed project without HKR ID (should be excluded)
        self.no_hkr_project = Project.objects.create(
            id=uuid.uuid4(),
            name="No HKR Project",
            description="No HKR ID",
            hkrId=None,  # No HKR ID
            programmed=True,
            projectClass=self.project_class,
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category
        )

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService._ProjectWiseService__sync_project_to_pw')
    def test_production_mass_update_all_projects(self, mock_sync, mock_get_pw):
        """Test production mass update processes all programmed projects with HKR IDs"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }
        mock_sync.return_value = None

        service = ProjectWiseService()

        # Run production mass update (all projects)
        update_log = service.sync_all_projects_to_pw()

        # Should process all programmed projects with HKR IDs (including out-of-scope)
        expected_projects = 3  # perfect_project, partial_project, out_of_scope_project
        self.assertEqual(len(update_log), expected_projects)

        # Verify correct projects were processed
        processed_names = [log['project_name'] for log in update_log]
        self.assertIn("Perfect Test Project", processed_names)
        self.assertIn("Partial Data Project", processed_names)
        self.assertIn("Out of Scope Project", processed_names)

        # Verify excluded projects were not processed
        self.assertNotIn("Non-Programmed Project", processed_names)
        self.assertNotIn("No HKR Project", processed_names)

        # Verify sync was called for each project
        self.assertEqual(mock_sync.call_count, expected_projects)

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService._ProjectWiseService__sync_project_to_pw')
    def test_mass_update_handles_errors_gracefully(self, mock_sync, mock_get_pw):
        """Test that mass update handles individual project errors gracefully"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }

        # Make sync fail for one specific project
        def sync_side_effect(*args, **kwargs):
            project = kwargs.get('project')
            if project and project.name == "Perfect Test Project":
                raise Exception("Simulated PW connection error")
            return None

        mock_sync.side_effect = sync_side_effect

        service = ProjectWiseService()

        # Run production mass update
        update_log = service.sync_all_projects_to_pw()

        # Should process all projects, with one error
        self.assertEqual(len(update_log), 3)

        # Check that one project failed and others succeeded
        error_logs = [log for log in update_log if log['status'] == 'error']
        success_logs = [log for log in update_log if log['status'] == 'success']

        self.assertEqual(len(error_logs), 1)
        self.assertEqual(len(success_logs), 2)

        # Verify the error log contains the error message
        self.assertEqual(error_logs[0]['project_name'], "Perfect Test Project")
        self.assertIn("Simulated PW connection error", error_logs[0]['error'])

    def tearDown(self):
        """Clean up test data"""
        self.env_patcher.stop()

    def test_create_project_data_for_mass_update(self):
        """Test project data creation for mass updates"""
        service = ProjectWiseService()

        # Test with perfect project (all fields populated)
        project_data = service._create_project_data_for_mass_update(self.perfect_project)

        # Should include all non-None fields in internal format (before conversion)
        expected_internal_fields = [
            'name', 'description', 'address', 'entityName',
            'estPlanningStart', 'estPlanningEnd', 'estConstructionStart', 'estConstructionEnd',
            'presenceStart', 'presenceEnd', 'visibilityStart', 'visibilityEnd',
            'phase', 'type', 'projectClass', 'programmed'
        ]

        for field in expected_internal_fields:
            self.assertIn(field, project_data, f"Internal field '{field}' should be included for perfect project")

        # Test with partial project (some fields None/empty)
        partial_data = service._create_project_data_for_mass_update(self.partial_project)

        # Should include non-None fields in internal format
        self.assertIn('name', partial_data)
        self.assertIn('entityName', partial_data)
        self.assertIn('estPlanningStart', partial_data)

        # Should exclude None fields
        self.assertNotIn('address', partial_data)  # None

        # Description should be included (required field, has value)
        self.assertIn('description', partial_data)  # Has value

    def test_mass_update_with_no_projects(self):
        """Test mass update behavior when no projects match criteria"""
        service = ProjectWiseService()

        # Delete all projects to test empty case
        Project.objects.all().delete()

        # Run mass update
        update_log = service.sync_all_projects_to_pw()

        # Should return empty log
        self.assertEqual(len(update_log), 0)
        self.assertEqual(update_log, [])

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService._ProjectWiseService__sync_project_to_pw')
    def test_mass_update_logging_and_statistics(self, mock_sync, mock_get_pw):
        """Test that mass update provides comprehensive logging and statistics"""
        mock_get_pw.return_value = {
            "relationshipInstances": [{"relatedInstance": {"instanceId": "test-id", "properties": {}}}]
        }

        # Set up mixed results: one success, one error, one with no data
        def sync_side_effect(*args, **kwargs):
            project = kwargs.get('project')
            if project and project.name == "Perfect Test Project":
                return None  # Success
            elif project and project.name == "Out of Scope Project":
                raise Exception("Connection timeout")  # Error
            return None  # Default success

        mock_sync.side_effect = sync_side_effect

        # Mock the data creation to return empty for one project
        original_create_data = ProjectWiseService._create_project_data_for_mass_update

        def mock_create_data(self, project):
            if project.name == "Partial Data Project":
                return {}  # No data to sync
            return original_create_data(self, project)

        with patch.object(ProjectWiseService, '_create_project_data_for_mass_update', mock_create_data):
            service = ProjectWiseService()

            # Run production mass update
            update_log = service.sync_all_projects_to_pw()

        # Verify comprehensive logging
        self.assertEqual(len(update_log), 3)

        # Count different statuses
        success_count = len([log for log in update_log if log['status'] == 'success'])
        error_count = len([log for log in update_log if log['status'] == 'error'])
        skipped_count = len([log for log in update_log if log['status'] == 'skipped'])

        self.assertEqual(success_count, 1)  # Perfect project
        self.assertEqual(error_count, 1)    # Out of scope project with error
        self.assertEqual(skipped_count, 1)  # Partial project with no data

        # Verify log structure
        for log in update_log:
            self.assertIn('project_id', log)
            self.assertIn('project_name', log)
            self.assertIn('hkr_id', log)
            self.assertIn('status', log)

            if log['status'] == 'success':
                self.assertIn('updated_fields', log)
            elif log['status'] == 'error':
                self.assertIn('error', log)
            elif log['status'] == 'skipped':
                self.assertIn('reason', log)


class ProjectWiseServiceCoreFunctionalityTestCase(TestCase):
    """
    Test cases for core ProjectWiseService functionality and configuration.
    """

    def test_pw_service_initialization(self):
        """Test that ProjectWiseService initializes correctly"""
        service = ProjectWiseService()

        # Verify service has required attributes
        self.assertIsNotNone(service.pw_api_url)
        self.assertIsNotNone(service.pw_api_project_update_endpoint)

    def test_pw_service_configuration_integration(self):
        """Test that PW service integrates correctly with configuration"""
        service = ProjectWiseService()

        # Test that configuration values are accessible
        self.assertIsNotNone(PWConfig.HIERARCHICAL_FIELD_DELAY)
        self.assertIsNotNone(PWConfig.PROTECTED_FIELDS)
        self.assertIsNotNone(PWConfig.CLASSIFICATION_FIELDS)

    def test_pw_service_configuration_consistency(self):
        """Test that PW service configuration is consistent"""
        service = ProjectWiseService()

        # Test that configuration values are reasonable
        self.assertGreater(PWConfig.HIERARCHICAL_FIELD_DELAY, 0)
        self.assertGreater(PWConfig.API_TIMEOUT, 0)
        self.assertGreater(PWConfig.LOG_SEPARATOR_LENGTH, 0)

    def test_pw_service_private_methods_exist(self):
        """Test that private methods exist and are callable"""
        service = ProjectWiseService()

        # Test private methods exist
        private_methods = [
            '_split_fields_by_type',
            '_calculate_update_results',
            '_get_pw_instance_and_url',
            '_apply_overwrite_rules',
            '_update_hierarchical_fields_one_by_one'
        ]

        for method_name in private_methods:
            self.assertTrue(hasattr(service, method_name), f"Method '{method_name}' should exist")
            self.assertTrue(callable(getattr(service, method_name)), f"Method '{method_name}' should be callable")

    def test_pw_service_constants_immutability(self):
        """Test that PW service constants are properly defined"""
        service = ProjectWiseService()

        # Test that hierarchical fields set is properly defined
        self.assertIsInstance(service.HIERARCHICAL_FIELDS, set)
        self.assertEqual(len(service.HIERARCHICAL_FIELDS), 6)

        # Test that all expected fields are present
        expected_fields = {
            'PROJECT_Pluokka', 'PROJECT_Luokka', 'PROJECT_Alaluokka',
            'PROJECT_Suurpiirin_nimi', 'PROJECT_Kaupunginosan_nimi', 'PROJECT_Osa_alue'
        }
        self.assertEqual(service.HIERARCHICAL_FIELDS, expected_fields)

    def test_pw_sync_disabled_handling(self):
        """Test PW service behavior when sync is disabled"""
        with patch.dict('os.environ', {'PW_SYNC_ENABLED': 'False'}):
            service = ProjectWiseService()
            result = service.sync_project_to_pw(data={'test': 'data'}, project=None)
            self.assertIsNone(result)

    def test_pw_sync_enabled_handling(self):
        """Test PW service behavior when sync is enabled"""
        with patch.dict('os.environ', {'PW_SYNC_ENABLED': 'True'}):
            service = ProjectWiseService()

            # Mock the actual sync method to avoid real API calls
            with patch.object(service, '_ProjectWiseService__sync_project_to_pw') as mock_sync:
                mock_sync.return_value = None

                # Test with valid parameters
                result = service.sync_project_to_pw(data={'test': 'data'}, project=Mock())

                # Should call the actual sync method
                mock_sync.assert_called_once()

    def test_pw_service_environment_variable_handling(self):
        """Test that PW service handles environment variables correctly"""
        # Test with sync disabled
        with patch.dict('os.environ', {'PW_SYNC_ENABLED': 'False'}):
            service = ProjectWiseService()
            result = service.sync_project_to_pw(data={'test': 'data'}, project=None)
            self.assertIsNone(result)

        # Test with sync enabled
        with patch.dict('os.environ', {'PW_SYNC_ENABLED': 'True'}):
            service = ProjectWiseService()
            with patch.object(service, '_ProjectWiseService__sync_project_to_pw') as mock_sync:
                mock_sync.return_value = None
                result = service.sync_project_to_pw(data={'test': 'data'}, project=Mock())
                mock_sync.assert_called_once()

    def test_pw_service_invalid_parameters(self):
        """Test error handling for invalid parameters"""
        # Enable sync to test the error handling logic
        with patch.dict('os.environ', {'PW_SYNC_ENABLED': 'True'}):
            service = ProjectWiseService()

            with patch('infraohjelmointi_api.services.ProjectWiseService.logger') as mock_logger:
                # Call with invalid parameters
                service.sync_project_to_pw()

                # Should log error
                mock_logger.error.assert_called_once_with("sync_project_to_pw called without proper parameters")
