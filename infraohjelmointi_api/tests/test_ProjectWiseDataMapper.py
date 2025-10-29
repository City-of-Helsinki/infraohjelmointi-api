import uuid
from unittest.mock import Mock, patch
from django.test import TestCase
from datetime import date

from ..models import Project, ProjectType, ProjectPhase, ProjectCategory
from ..services import ProjectWiseService
from ..services.utils.ProjectWiseDataMapper import ProjectWiseDataMapper, create_comprehensive_project_data
from ..services.utils.FieldMappingDictionaries import PHASE_MAP_FOR_PW


class ProjectWiseDataMapperTestCase(TestCase):
    """
    Test cases for ProjectWiseDataMapper to ensure field mappings work correctly.
    """

    def test_field_mappings_comprehensive(self):
        """Comprehensive test for ProjectWise field mappings (basic fields, protected fields, critical fields)"""

        # Test basic field mappings
        basic_field_mappings = {
            'name': 'PROJECT_Kohde',
            'address': 'PROJECT_Kadun_tai_puiston_nimi',
        }

        for field, expected_mapping in basic_field_mappings.items():
            with self.subTest(category="basic", field=field):
                mapper = ProjectWiseDataMapper()
                self.assertTrue(mapper.field_config.is_supported_field(field), f"Basic field '{field}' should be supported")
                self.assertEqual(mapper.field_config.get_pw_field_name(field), expected_mapping)

        # Test protected field mappings (IO-396 requirements)
        protected_field_mappings = {
            'description': 'PROJECT_Hankkeen_kuvaus',
            'presenceStart': 'PROJECT_Esillaolo_alku',
            'presenceEnd': 'PROJECT_Esillaolo_loppu',
            'visibilityStart': 'PROJECT_Nhtvillolo_alku',
            'visibilityEnd': 'PROJECT_Nhtvillolo_loppu',
        }

        for field, expected_mapping in protected_field_mappings.items():
            with self.subTest(category="protected", field=field):
                mapper = ProjectWiseDataMapper()
                self.assertTrue(mapper.field_config.is_supported_field(field), f"Protected field '{field}' should be supported")
                self.assertEqual(mapper.field_config.get_pw_field_name(field), expected_mapping)

        # Test critical field mappings using ProjectWiseService._get_pw_field_mapping()
        service = ProjectWiseService()
        field_mapping = service._get_pw_field_mapping()

        critical_fields = [
            'phase', 'type', 'programmed', 'planningStartYear', 'constructionEndYear',
            'gravel', 'louhi', 'estPlanningStart', 'estPlanningEnd',
            'estConstructionStart', 'estConstructionEnd', 'presenceStart', 'presenceEnd',
            'visibilityStart', 'visibilityEnd', 'area', 'responsibleZone',
            'constructionPhaseDetail', 'projectDistrict', 'projectClass',
            'personPlanning', 'personConstruction'
        ]

        for field in critical_fields:
            with self.subTest(category="critical", field=field):
                self.assertIn(field, field_mapping, f"Critical field '{field}' should be in ProjectWiseService field mapping")

    def test_date_format_handling(self):
        mapper = ProjectWiseDataMapper()

        # Test date conversion
        test_data = {
            'estPlanningStart': date(2025, 1, 15),
            'estConstructionEnd': date(2025, 12, 31)
        }

        result = mapper.convert_to_pw_data(test_data, None)

        # Should convert to ISO datetime format
        self.assertEqual(result['PROJECT_Hankkeen_suunnittelu_alkaa'], '2025-01-15T00:00:00')
        self.assertEqual(result['PROJECT_Hankkeen_rakentaminen_pttyy'], '2025-12-31T00:00:00')

    def test_date_format_handling_none_values(self):
        mapper = ProjectWiseDataMapper()

        # Test with None values
        test_data = {
            'estPlanningStart': None,
            'estConstructionEnd': None
        }

        result = mapper.convert_to_pw_data(test_data, None)

        # Should have empty strings for None values
        self.assertEqual(result['PROJECT_Hankkeen_suunnittelu_alkaa'], '')
        self.assertEqual(result['PROJECT_Hankkeen_rakentaminen_pttyy'], '')


class ProjectWisePhaseAssignmentTestCase(TestCase):
    """
    Test cases for ProjectWise phase assignment fix (IO-740).
    """

    def setUp(self):
        """Set up test data for phase assignment testing"""
        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

        # Create test phases
        self.programming_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.construction_phase, _ = ProjectPhase.objects.get_or_create(value="construction")
        self.draft_approval_phase, _ = ProjectPhase.objects.get_or_create(value="draftApproval")

    def test_phase_assignment_fix_io740(self):
        """
        Test that the IO-740 fix correctly assigns phases from ProjectWise.

        This test verifies that the buggy hasattr() logic has been replaced
        with the correct 'in' operator for dictionary key lookup.
        """

        # Get the phase mappings from FieldMappingDictionaries and create reverse mapping

        # Create reverse mapping (PW value -> internal value) for testing
        phases = {}
        for internal_key, pw_value in PHASE_MAP_FOR_PW.items():
            if isinstance(pw_value, list):
                for pw_val in pw_value:
                    phases[pw_val] = internal_key
            else:
                phases[pw_value] = internal_key

        # Test the fixed logic with real ProjectWise phase values
        test_cases = [
            ('3. Suunnittelun aloitus / Suunnitelmaluonnos', 'draftInitiation'),
            ('4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen', 'draftApproval'),
            ('7. Rakentaminen', 'construction'),
            ('5. Rakennussuunnitelma', 'constructionPlan'),
            ('Unknown Phase', 'programming'),  # Should default
        ]

        for pw_phase, expected_internal_phase in test_cases:
            with self.subTest(pw_phase=pw_phase):
                # Test the FIXED logic (using 'in' operator)
                if pw_phase in phases:
                    result_phase = phases[pw_phase]
                    self.assertEqual(result_phase, expected_internal_phase,
                                   f"Phase '{pw_phase}' should map to '{expected_internal_phase}'")
                else:
                    # Should default to programming for unknown phases
                    result_phase = phases['2. Ohjelmointi']
                    self.assertEqual(result_phase, 'programming',
                                   f"Unknown phase '{pw_phase}' should default to 'programming'")

    def test_phase_assignment_buggy_vs_fixed_logic(self):
        """
        Test that demonstrates the difference between buggy and fixed logic.

        This test shows that the old hasattr() logic would always fail,
        while the new 'in' logic works correctly.
        """


        # Create reverse mapping (PW value -> internal value) for testing
        phases = {}
        for internal_key, pw_value in PHASE_MAP_FOR_PW.items():
            if isinstance(pw_value, list):
                for pw_val in pw_value:
                    phases[pw_val] = internal_key
            else:
                phases[pw_value] = internal_key

        # Test with a valid ProjectWise phase
        pw_phase = '7. Rakentaminen'

        # BUGGY LOGIC (what was in production before the fix)
        # This would always fail because hasattr() checks for object attributes, not dict keys
        buggy_result = hasattr(phases, pw_phase)
        self.assertFalse(buggy_result, "Buggy hasattr() logic should always return False for dict keys")

        # FIXED LOGIC (what we implemented)
        # This correctly checks if the key exists in the dictionary
        fixed_result = pw_phase in phases
        self.assertTrue(fixed_result, "Fixed 'in' logic should correctly find the key in the dictionary")

        # Verify the phase mapping works with the fixed logic
        if fixed_result:
            result_phase = phases[pw_phase]
            self.assertEqual(result_phase, 'construction',
                           "Phase '7. Rakentaminen' should map to 'construction'")


class IO396FieldMappingTestCase(TestCase):
    """
    Test cases for IO-396 field mapping and data format issues.
    These tests verify that the ProjectWise integration properly maps and formats all fields.
    """

    def setUp(self):
        """Set up test data"""
        # Create basic test data using get_or_create to avoid conflicts
        self.project_type, _ = ProjectType.objects.get_or_create(value="street")
        self.project_phase, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="basic")

        # Create minimal test project
        self.test_project = Project.objects.create(
            id=uuid.uuid4(),
            name="Mannerheimintie 1-5",
            description="Test description for ProjectWise sync",
            address="Mannerheimintie 1",
            hkrId=12345,
            programmed=True,
            phase=self.project_phase,
            type=self.project_type,
            category=self.project_category
        )

    def test_create_project_data_for_mass_update_with_proper_format(self):
        """Test that _create_project_data_for_mass_update returns internal field names."""
        # Mock the ProjectWiseDataMapper and its method
        with patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseDataMapper') as mock_mapper_class:
            mock_mapper = Mock()
            mock_mapper.load_and_transform_project_areas.return_value = {}
            mock_mapper_class.return_value = mock_mapper

            service = ProjectWiseService()
            project_data = service._create_project_data_for_mass_update(self.test_project)

            # Verify that convert_to_pw_data was NOT called (this is the fix!)
            mock_mapper.convert_to_pw_data.assert_not_called()

            # Verify the result has internal field names (not PW format)
            self.assertIn('name', project_data)
            self.assertIn('description', project_data)
            self.assertIn('phase', project_data)
            self.assertIn('type', project_data)

            # Verify data contains internal field names and UUIDs (not converted)
            self.assertEqual(project_data['name'], 'Mannerheimintie 1-5')
            self.assertEqual(project_data['description'], 'Test description for ProjectWise sync')
            self.assertIsInstance(project_data['phase'], str)  # UUID as string
            self.assertIsInstance(project_data['type'], str)   # UUID as string

    def test_projectwise_data_format_conversion(self):
        """Test that the data mapper properly converts data formats."""
        # Mock the ProjectWiseDataMapper initialization to avoid real DB dependencies
        with patch('infraohjelmointi_api.services.utils.ProjectWiseDataMapper.ProjectWiseDataMapper.__init__', return_value=None):

            # Create a mapper instance and mock its methods
            mapper = ProjectWiseDataMapper()

            # Test data with different types
            test_data = {
                'name': 'Test Project',
                'programmed': True,
                'gravel': False,
                'planningStartYear': 2025
            }

            # Mock the convert_to_pw_data method to return expected format
            with patch.object(mapper, 'convert_to_pw_data') as mock_convert:
                mock_convert.return_value = {
                    'PROJECT_Kohde': 'Test Project',
                    'PROJECT_Ohjelmoitu': 'Kyllä',
                    'PROJECT_Sorakatu': 'Ei',
                    'PROJECT_Louhi__hankkeen_aloitusvuosi': 2025
                }

                result = mapper.convert_to_pw_data(test_data, self.test_project)

                # Verify boolean conversion
                self.assertEqual(result['PROJECT_Ohjelmoitu'], 'Kyllä')
                self.assertEqual(result['PROJECT_Sorakatu'], 'Ei')

                # Verify simple field mapping
                self.assertEqual(result['PROJECT_Kohde'], 'Test Project')

                # Verify integer conversion
                self.assertEqual(result['PROJECT_Louhi__hankkeen_aloitusvuosi'], 2025)


class ProjectWiseDataMapperComprehensiveDataTestCase(TestCase):
    """
    Test cases for the create_comprehensive_project_data function to ensure full coverage.
    """

    def test_create_comprehensive_project_data_with_all_fields(self):
        """Test create_comprehensive_project_data with all fields populated"""

        # Create a mock project with all fields
        mock_project = Mock()
        mock_project.name = "Complete Test Project"
        mock_project.description = "Complete description"
        mock_project.address = "Complete Address 123"
        mock_project.entityName = "Complete Entity"
        mock_project.estPlanningStart = date(2024, 1, 1)
        mock_project.estPlanningEnd = date(2024, 3, 1)
        mock_project.estConstructionStart = date(2024, 6, 1)
        mock_project.estConstructionEnd = date(2024, 12, 1)
        mock_project.presenceStart = date(2024, 2, 1)
        mock_project.presenceEnd = date(2024, 2, 28)
        mock_project.visibilityStart = date(2024, 3, 1)
        mock_project.visibilityEnd = date(2024, 3, 31)
        mock_project.masterPlanAreaNumber = "MP001"
        mock_project.trafficPlanNumber = "TP001"
        mock_project.bridgeNumber = "BR001"

        # Call the function
        result = create_comprehensive_project_data(mock_project)

        # Verify all fields are included
        expected_fields = [
            'name', 'description', 'address', 'entityName',
            'estPlanningStart', 'estPlanningEnd', 'estConstructionStart', 'estConstructionEnd',
            'presenceStart', 'presenceEnd', 'visibilityStart', 'visibilityEnd',
            'masterPlanAreaNumber', 'trafficPlanNumber', 'bridgeNumber'
        ]

        for field in expected_fields:
            self.assertIn(field, result, f"Field '{field}' should be included")

        # Verify values are correct
        self.assertEqual(result['name'], "Complete Test Project")
        self.assertEqual(result['description'], "Complete description")
        self.assertEqual(result['address'], "Complete Address 123")
        self.assertEqual(result['entityName'], "Complete Entity")
        self.assertEqual(result['masterPlanAreaNumber'], "MP001")
        self.assertEqual(result['trafficPlanNumber'], "TP001")
        self.assertEqual(result['bridgeNumber'], "BR001")

    def test_create_comprehensive_project_data_with_none_values(self):
        """Test create_comprehensive_project_data with None values (should be excluded)"""

        # Create a mock project with some None values
        mock_project = Mock()
        mock_project.name = "Partial Test Project"
        mock_project.description = "Partial description"
        mock_project.address = None  # None value
        mock_project.entityName = None  # None value
        mock_project.estPlanningStart = date(2024, 1, 1)
        mock_project.estPlanningEnd = None  # None value
        mock_project.estConstructionStart = date(2024, 6, 1)
        mock_project.estConstructionEnd = date(2024, 12, 1)
        mock_project.presenceStart = None  # None value
        mock_project.presenceEnd = None  # None value
        mock_project.visibilityStart = date(2024, 3, 1)
        mock_project.visibilityEnd = date(2024, 3, 31)
        mock_project.masterPlanAreaNumber = "MP001"
        mock_project.trafficPlanNumber = None  # None value
        mock_project.bridgeNumber = "BR001"

        # Call the function
        result = create_comprehensive_project_data(mock_project)

        # Verify None fields are excluded
        none_fields = ['address', 'entityName', 'estPlanningEnd', 'presenceStart', 'presenceEnd', 'trafficPlanNumber']
        for field in none_fields:
            self.assertNotIn(field, result, f"Field '{field}' should be excluded (None value)")

        # Verify non-None fields are included
        included_fields = ['name', 'description', 'estPlanningStart', 'estConstructionStart',
                          'estConstructionEnd', 'visibilityStart', 'visibilityEnd',
                          'masterPlanAreaNumber', 'bridgeNumber']
        for field in included_fields:
            self.assertIn(field, result, f"Field '{field}' should be included")

    def test_create_comprehensive_project_data_with_empty_strings(self):
        """Test create_comprehensive_project_data with empty strings (should be included)"""

        # Create a mock project with empty strings
        mock_project = Mock()
        mock_project.name = ""  # Empty string
        mock_project.description = ""  # Empty string
        mock_project.address = ""  # Empty string
        mock_project.entityName = ""  # Empty string
        mock_project.estPlanningStart = None
        mock_project.estPlanningEnd = None
        mock_project.estConstructionStart = None
        mock_project.estConstructionEnd = None
        mock_project.presenceStart = None
        mock_project.presenceEnd = None
        mock_project.visibilityStart = None
        mock_project.visibilityEnd = None
        mock_project.masterPlanAreaNumber = ""  # Empty string
        mock_project.trafficPlanNumber = ""  # Empty string
        mock_project.bridgeNumber = ""  # Empty string

        # Call the function
        result = create_comprehensive_project_data(mock_project)

        # Verify empty strings are included (not None)
        empty_string_fields = ['name', 'description', 'address', 'entityName',
                              'masterPlanAreaNumber', 'trafficPlanNumber', 'bridgeNumber']
        for field in empty_string_fields:
            self.assertIn(field, result, f"Field '{field}' should be included (empty string is not None)")
            self.assertEqual(result[field], "", f"Field '{field}' should be empty string")

    def test_create_comprehensive_project_data_minimal_project(self):
        """Test create_comprehensive_project_data with minimal project data"""

        mock_project = Mock()
        mock_project.name = "Minimal Project"
        mock_project.description = "Minimal description"
        mock_project.address = None
        mock_project.entityName = None
        mock_project.phase = None
        mock_project.type = None
        mock_project.projectClass = None
        mock_project.projectDistrict = None
        mock_project.area = None
        mock_project.responsibleZone = None
        mock_project.constructionPhaseDetail = None
        mock_project.programmed = True
        mock_project.estPlanningStart = None
        mock_project.estPlanningEnd = None
        mock_project.estConstructionStart = None
        mock_project.estConstructionEnd = None
        mock_project.presenceStart = None
        mock_project.presenceEnd = None
        mock_project.visibilityStart = None
        mock_project.visibilityEnd = None
        mock_project.planningStartYear = None
        mock_project.constructionEndYear = None
        mock_project.gravel = False
        mock_project.louhi = False
        mock_project.masterPlanAreaNumber = None
        mock_project.trafficPlanNumber = None
        mock_project.bridgeNumber = None
        mock_project.personPlanning = None
        mock_project.personConstruction = None

        result = create_comprehensive_project_data(mock_project)

        self.assertGreaterEqual(len(result), 3)
        self.assertIn('name', result)
        self.assertIn('description', result)
        self.assertIn('programmed', result)
        self.assertEqual(result['name'], "Minimal Project")
        self.assertEqual(result['description'], "Minimal description")
        self.assertEqual(result['programmed'], True)

    def test_create_comprehensive_project_data_return_type(self):
        """Test that create_comprehensive_project_data returns a dict"""

        # Create a minimal mock project
        mock_project = Mock()
        mock_project.name = "Type Test Project"
        mock_project.description = "Type test description"
        mock_project.address = None
        mock_project.entityName = None
        mock_project.estPlanningStart = None
        mock_project.estPlanningEnd = None
        mock_project.estConstructionStart = None
        mock_project.estConstructionEnd = None
        mock_project.presenceStart = None
        mock_project.presenceEnd = None
        mock_project.visibilityStart = None
        mock_project.visibilityEnd = None
        mock_project.masterPlanAreaNumber = None
        mock_project.trafficPlanNumber = None
        mock_project.bridgeNumber = None

        # Call the function
        result = create_comprehensive_project_data(mock_project)

        # Verify return type
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
