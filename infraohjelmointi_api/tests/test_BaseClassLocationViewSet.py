"""
Tests for BaseClassLocationViewSet functionality including frame_budgets context building.
"""

from datetime import date
from collections import defaultdict
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from unittest.mock import Mock, patch

from infraohjelmointi_api.models import (
    ProjectClass, 
    ProjectLocation,
    ClassFinancial,
    LocationFinancial,
    User
)
from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet


class BaseClassLocationViewSetTestCase(TestCase):
    """Test BaseClassLocationViewSet methods"""
    
    def setUp(self):
        """Set up test data"""
        self.year = date.today().year
        self.user = User.objects.create(
            first_name='Test', 
            last_name='User',
            email='test@example.com'
        )
        
        # Create test coordinator class
        self.coordinator_class = ProjectClass.objects.create(
            name="Test Coordinator Class",
            path="001",
            forCoordinatorOnly=True
        )
        
        # Create test coordinator location
        self.coordinator_location = ProjectLocation.objects.create(
            name="Test Coordinator Location",
            path="L001",
            forCoordinatorOnly=True
        )
        
        # Create ClassFinancial data
        ClassFinancial.objects.create(
            classRelation=self.coordinator_class,
            year=self.year,
            frameBudget=50000,
            budgetChange=0
        )
        
        # Create LocationFinancial data
        LocationFinancial.objects.create(
            locationRelation=self.coordinator_location,
            year=self.year + 1,
            frameBudget=30000,
            budgetChange=0
        )
        
        self.factory = APIRequestFactory()

    def test_build_frame_budgets_context_static_method(self):
        """Test the static build_frame_budgets_context method"""
        frame_budgets = BaseClassLocationViewSet.build_frame_budgets_context(self.year)
        
        # Verify return type
        self.assertIsInstance(frame_budgets, defaultdict)
        
        # Verify class financial data is included
        class_key = f"{self.year}-{self.coordinator_class.id}"
        self.assertEqual(frame_budgets[class_key], 50000)
        
        # Verify location financial data is included
        location_key = f"{self.year + 1}-{self.coordinator_location.id}"
        self.assertEqual(frame_budgets[location_key], 30000)
        
        # Verify default value for non-existent keys
        non_existent_key = f"{self.year + 5}-00000000-0000-0000-0000-000000000000"
        self.assertEqual(frame_budgets[non_existent_key], 0)

    def test_build_frame_budgets_context_with_multiple_years(self):
        """Test frame_budgets context building with multiple years of data"""
        # Add more financial data for testing
        ClassFinancial.objects.create(
            classRelation=self.coordinator_class,
            year=self.year + 2,
            frameBudget=75000,
            budgetChange=0
        )
        
        frame_budgets = BaseClassLocationViewSet.build_frame_budgets_context(self.year)
        
        # Verify both years are included
        year1_key = f"{self.year}-{self.coordinator_class.id}"
        year3_key = f"{self.year + 2}-{self.coordinator_class.id}"
        
        self.assertEqual(frame_budgets[year1_key], 50000)
        self.assertEqual(frame_budgets[year3_key], 75000)

    def test_build_frame_budgets_context_empty_data(self):
        """Test frame_budgets context building with no financial data"""
        # Clear all financial data
        ClassFinancial.objects.all().delete()
        LocationFinancial.objects.all().delete()
        
        frame_budgets = BaseClassLocationViewSet.build_frame_budgets_context(self.year)
        
        # Should still return defaultdict with 0 values
        self.assertIsInstance(frame_budgets, defaultdict)
        test_key = f"{self.year}-{self.coordinator_class.id}"
        self.assertEqual(frame_budgets[test_key], 0)

    def test_is_patch_data_valid_with_valid_data(self):
        """Test is_patch_data_valid method with valid data"""
        viewset = BaseClassLocationViewSet()
        
        valid_data = {
            "finances": {
                "year": self.year,
                "year0": {
                    "frameBudget": 50000
                },
                "year1": {
                    "budgetChange": 10000
                }
            }
        }
        
        self.assertTrue(viewset.is_patch_data_valid(valid_data))

    def test_is_patch_data_valid_with_valid_both_fields(self):
        """Test is_patch_data_valid method with both frameBudget and budgetChange"""
        viewset = BaseClassLocationViewSet()
        
        valid_data = {
            "finances": {
                "year": self.year,
                "year0": {
                    "frameBudget": 50000,
                    "budgetChange": 10000
                }
            }
        }
        
        self.assertTrue(viewset.is_patch_data_valid(valid_data))

    def test_is_patch_data_valid_missing_finances(self):
        """Test is_patch_data_valid method with missing finances"""
        viewset = BaseClassLocationViewSet()
        
        invalid_data = {}
        
        self.assertFalse(viewset.is_patch_data_valid(invalid_data))

    def test_is_patch_data_valid_missing_year(self):
        """Test is_patch_data_valid method with missing year"""
        viewset = BaseClassLocationViewSet()
        
        invalid_data = {
            "finances": {
                "year0": {
                    "frameBudget": 50000
                }
            }
        }
        
        self.assertFalse(viewset.is_patch_data_valid(invalid_data))

    def test_is_patch_data_valid_invalid_parameter_type(self):
        """Test is_patch_data_valid method with invalid parameter type"""
        viewset = BaseClassLocationViewSet()
        
        invalid_data = {
            "finances": {
                "year": self.year,
                "year0": "not_a_dict"
            }
        }
        
        self.assertFalse(viewset.is_patch_data_valid(invalid_data))

    def test_is_patch_data_valid_too_many_parameters(self):
        """Test is_patch_data_valid method with too many parameters"""
        viewset = BaseClassLocationViewSet()
        
        invalid_data = {
            "finances": {
                "year": self.year,
                "year0": {
                    "frameBudget": 50000,
                    "budgetChange": 10000,
                    "extraField": 123
                }
            }
        }
        
        self.assertFalse(viewset.is_patch_data_valid(invalid_data))

    def test_is_patch_data_valid_no_required_fields(self):
        """Test is_patch_data_valid method with no frameBudget or budgetChange"""
        viewset = BaseClassLocationViewSet()
        
        invalid_data = {
            "finances": {
                "year": self.year,
                "year0": {
                    "someOtherField": 123
                }
            }
        }
        
        self.assertFalse(viewset.is_patch_data_valid(invalid_data))

    def test_is_patch_data_valid_empty_parameters(self):
        """Test is_patch_data_valid method with empty parameter dict"""
        viewset = BaseClassLocationViewSet()
        
        invalid_data = {
            "finances": {
                "year": self.year,
                "year0": {}
            }
        }
        
        self.assertFalse(viewset.is_patch_data_valid(invalid_data))

    @patch('infraohjelmointi_api.views.BaseClassLocationViewSet.BaseClassLocationViewSet.get_queryset')
    @patch('infraohjelmointi_api.views.BaseClassLocationViewSet.BaseClassLocationViewSet.get_serializer')
    def test_list_method_calls_build_frame_budgets_context(self, mock_get_serializer, mock_get_queryset):
        """Test that list method calls build_frame_budgets_context"""
        # Setup mocks
        mock_queryset = Mock()
        mock_get_queryset.return_value = mock_queryset
        
        mock_serializer = Mock()
        mock_serializer.data = []
        mock_get_serializer.return_value = mock_serializer
        
        # Create viewset and request  
        viewset = BaseClassLocationViewSet()
        django_request = self.factory.get(f'/test/?year={self.year}')
        request = Request(django_request)
        
        # Call list method
        response = viewset.list(request)
        
        # Verify get_serializer was called with frame_budgets context
        mock_get_serializer.assert_called_once()
        call_args = mock_get_serializer.call_args
        context = call_args[1]['context']
        
        self.assertIn('frame_budgets', context)
        self.assertIn('finance_year', context)
        self.assertEqual(context['finance_year'], self.year)
        self.assertIsInstance(context['frame_budgets'], defaultdict)

    @patch('infraohjelmointi_api.views.BaseClassLocationViewSet.BaseClassLocationViewSet.get_queryset')
    @patch('infraohjelmointi_api.views.BaseClassLocationViewSet.BaseClassLocationViewSet.get_serializer')
    def test_list_method_default_year(self, mock_get_serializer, mock_get_queryset):
        """Test that list method uses current year when year parameter is not provided"""
        # Setup mocks
        mock_queryset = Mock()
        mock_get_queryset.return_value = mock_queryset
        
        mock_serializer = Mock()
        mock_serializer.data = []
        mock_get_serializer.return_value = mock_serializer
        
        # Create viewset and request without year parameter
        viewset = BaseClassLocationViewSet()
        django_request = self.factory.get('/test/')
        request = Request(django_request)
        
        # Call list method
        response = viewset.list(request)
        
        # Verify get_serializer was called with current year
        mock_get_serializer.assert_called_once()
        call_args = mock_get_serializer.call_args
        context = call_args[1]['context']
        
        self.assertEqual(context['finance_year'], date.today().year)

    def test_parse_forced_to_frame_param_false_strings(self):
        """Test parse_forced_to_frame_param with false string values"""
        self.assertFalse(BaseClassLocationViewSet.parse_forced_to_frame_param("False"))
        self.assertFalse(BaseClassLocationViewSet.parse_forced_to_frame_param("false"))

    def test_parse_forced_to_frame_param_true_strings(self):
        """Test parse_forced_to_frame_param with true string values"""
        self.assertTrue(BaseClassLocationViewSet.parse_forced_to_frame_param("True"))
        self.assertTrue(BaseClassLocationViewSet.parse_forced_to_frame_param("true"))

    def test_parse_forced_to_frame_param_boolean_values(self):
        """Test parse_forced_to_frame_param with actual boolean values"""
        self.assertTrue(BaseClassLocationViewSet.parse_forced_to_frame_param(True))
        self.assertFalse(BaseClassLocationViewSet.parse_forced_to_frame_param(False))

    def test_parse_forced_to_frame_param_invalid_value(self):
        """Test parse_forced_to_frame_param with invalid values"""
        from rest_framework.exceptions import ParseError
        
        with self.assertRaises(ParseError):
            BaseClassLocationViewSet.parse_forced_to_frame_param("invalid")
        
        with self.assertRaises(ParseError):
            BaseClassLocationViewSet.parse_forced_to_frame_param("maybe")

    @patch('infraohjelmointi_api.views.BaseClassLocationViewSet.Response')
    def test_validate_and_process_patch_finances_entity_not_found(self, mock_response):
        """Test validate_and_process_patch_finances when entity doesn't exist"""
        from infraohjelmointi_api.services import ProjectClassService
        from infraohjelmointi_api.models import ClassFinancial
        
        viewset = BaseClassLocationViewSet()
        mock_request = Mock()
        mock_request.data = {"forcedToFrame": False}
        
        # Mock service to return False for instance_exists
        with patch.object(ProjectClassService, 'instance_exists', return_value=False):
            success, result = viewset.validate_and_process_patch_finances(
                request=mock_request,
                entity_id="test-id",
                entity_service=ProjectClassService,
                financial_service=Mock(),
                financial_model=ClassFinancial,
                relation_field="classRelation"
            )
        
        self.assertFalse(success)

    @patch('infraohjelmointi_api.views.BaseClassLocationViewSet.Response')
    def test_validate_and_process_patch_finances_invalid_data(self, mock_response):
        """Test validate_and_process_patch_finances with invalid patch data"""
        from infraohjelmointi_api.services import ProjectClassService
        from infraohjelmointi_api.models import ClassFinancial
        
        viewset = BaseClassLocationViewSet()
        mock_request = Mock()
        mock_request.data = {"invalid": "data"}  # Missing finances
        
        with patch.object(ProjectClassService, 'instance_exists', return_value=True):
            success, result = viewset.validate_and_process_patch_finances(
                request=mock_request,
                entity_id="test-id",
                entity_service=ProjectClassService,
                financial_service=Mock(),
                financial_model=ClassFinancial,
                relation_field="classRelation"
            )
        
        self.assertFalse(success)
