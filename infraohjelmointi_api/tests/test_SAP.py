import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from overrides import override

from infraohjelmointi_api.models import Project
from infraohjelmointi_api.services.SapApiService import SapApiService
from infraohjelmointi_api.views import BaseViewSet, SapCurrentYearViewSet


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class TestSAPService(TestCase):
    project_1_Id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    sapProjectId = "2814I00708"

    def setUp(self):
        # connection setup
        self.sap_service = SapApiService()
        self.sap_service.sap_api_url = "http://fake-sap-api-url.com"
        self.sap_service.sap_api_costs_endpoint = "$/costs?id='{posid}'&start={budat_start}&end={budat_end}"
        self.sap_service.sap_api_commitments_endpoint = "$/costs?id='{posid}'&start={budat_start}&end={budat_end}"
        self.sap_service.session = MagicMock()
        self.sap_current_year_viewset = SapCurrentYearViewSet()

        # Set the sap start year to be 2017 to get all data from sap
        self.sap_fetch_all_data_start_year = 2017

    @classmethod
    @override
    def setUpTestData(self):
        self.project = Project.objects.create(
            id=self.project_1_Id,
            sapProject=self.sapProjectId,
            name="testi",
            description="testii"
        )

    @patch('infraohjelmointi_api.services.ProjectService.ProjectService.get_by_sap_id')
    def test_get_project_costs_and_commitments_successful(self, mock_get_by_sap_id):
        # Mock the SAP API response for costs
        mock_response_all_costs = MagicMock()
        mock_response_all_costs.status_code = 200
        mock_response_all_costs.json.return_value = {
            "d": {"results": [{"Posid": "123.01", "Wkgbtr": Decimal('100.000')}]}
        }

        # Mock the SAP API response for commitments
        mock_response_all_commitments = MagicMock()
        mock_response_all_commitments.status_code = 200
        mock_response_all_commitments.json.return_value = {
            "d": {"results": [{"Posid": "123.01", "Wkgbtr": Decimal('50.000')}]}
        }

        # Mock the SAP API response for current year costs
        mock_response_current_year_costs = MagicMock()
        mock_response_current_year_costs.status_code = 200
        mock_response_current_year_costs.json.return_value = {
            "d": {"results": [{"Posid": "123.01", "Wkgbtr": Decimal('100.000')}]}
        }

        # Mock the SAP API response for current year commitments
        mock_response_current_year_commitments = MagicMock()
        mock_response_current_year_commitments.status_code = 200
        mock_response_current_year_commitments.json.return_value = {
            "d": {"results": [{"Posid": "123.01", "Wkgbtr": Decimal('50.000')}]}
        }

        # Mock the session.get call to return the mocked responses in sequence
        self.sap_service.session.get.side_effect = [
            mock_response_all_costs,
            mock_response_all_commitments,
            mock_response_current_year_costs,
            mock_response_current_year_commitments
        ]

        # Call the function with a known SAP ID
        project_id = '123'
        all_sap_data = self.sap_service.get_all_project_costs_and_commitments_from_sap(project_id)
        current_year_data = self.sap_service.get_costs_and_commitments_by_year(project_id, datetime.now().year)
        result = {
            'all_sap_data': all_sap_data,
            'current_year': current_year_data
        }

        # Assertions to ensure the returned data structure is as expected
        # Assertions for all_sap_data
        self.assertIn('costs', result['all_sap_data'])
        self.assertIn('commitments', result['all_sap_data'])
        self.assertEqual(result['all_sap_data']['costs']['project_task'], Decimal('100.000'))
        self.assertEqual(result['all_sap_data']['costs']['production_task'], Decimal('0'))
        self.assertEqual(result['all_sap_data']['commitments']['project_task'], Decimal('50.000'))
        self.assertEqual(result['all_sap_data']['commitments']['production_task'], Decimal('0'))

        # Assertions for current_year
        self.assertIn('costs', result['current_year'])
        self.assertIn('commitments', result['current_year'])
        self.assertEqual(result['current_year']['costs']['project_task'], Decimal('100.000'))
        self.assertEqual(result['current_year']['costs']['production_task'], Decimal('0'))
        self.assertEqual(result['current_year']['commitments']['project_task'], Decimal('50.000'))
        self.assertEqual(result['current_year']['commitments']['production_task'], Decimal('0'))

        # Assert that the session.get was called with the correct URL and parameters
        start_date = datetime.now().replace(
            month=1, day=1, hour=0, minute=0, second=0
        ).replace(year=self.sap_fetch_all_data_start_year).strftime("%Y-%m-%dT%H:%M:%S")
        end_date = datetime.now().replace(
            year=datetime.now().year + 1, month=1, day=1, hour=0, minute=0, second=0
        ).strftime("%Y-%m-%dT%H:%M:%S")

        start_date_current_year = datetime.now().replace(
            month=1, day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")

        expected_costs_url_for_all_sap_data = f"{self.sap_service.sap_api_url}{self.sap_service.sap_api_costs_endpoint}".format(posid=project_id, budat_start=start_date, budat_end= end_date)
        expected_commitments_url_for_all_sap_data = f"{self.sap_service.sap_api_url}{self.sap_service.sap_api_commitments_endpoint}".format(posid=project_id, budat_start=start_date, budat_end= end_date)
        self.sap_service.session.get.assert_any_call(expected_costs_url_for_all_sap_data)
        self.sap_service.session.get.assert_any_call(expected_commitments_url_for_all_sap_data)

        expected_costs_url_for_current_year_sap_data = f"{self.sap_service.sap_api_url}{self.sap_service.sap_api_costs_endpoint}".format(posid=project_id, budat_start=start_date_current_year, budat_end= end_date)
        expected_commitments_url_for_current_year_sap_data = f"{self.sap_service.sap_api_url}{self.sap_service.sap_api_commitments_endpoint}".format(posid=project_id, budat_start=start_date_current_year, budat_end= end_date)
        self.sap_service.session.get.assert_any_call(expected_costs_url_for_current_year_sap_data)
        self.sap_service.session.get.assert_any_call(expected_commitments_url_for_current_year_sap_data)

    @patch('infraohjelmointi_api.services.ProjectService.ProjectService.get_by_sap_id')
    def test_get_project_costs_and_commitments_sap_error(self, mock_get_by_sap_id):
        # Mock a project to return from the project service
        mock_project = MagicMock()
        mock_project.planningStartYear = 2022
        mock_get_by_sap_id.return_value = [mock_project]

        # Mock the SAP API response to simulate an error
        mock_response_error = MagicMock()
        mock_response_error.status_code = 400
        mock_response_error.reason = "Bad request"
        self.sap_service.session.get.return_value = mock_response_error

        # Call the function and assert an empty dict is returned due to the error
        project_id = '123'
        all_sap_data = self.sap_service.get_all_project_costs_and_commitments_from_sap(project_id)
        current_year_data = self.sap_service.get_costs_and_commitments_by_year(project_id, datetime.now().year)
        result = {
            'all_sap_data': all_sap_data,
            'current_year': current_year_data
        }
        
        expected_result = {
            'all_sap_data': {
                'costs': {'project_task': Decimal('0'), 'production_task': Decimal('0')},
                'commitments': {'project_task': Decimal('0'), 'production_task': Decimal('0')}
            },
            'current_year': {
                'costs': {'project_task': Decimal('0'), 'production_task': Decimal('0')},
                'commitments': {'project_task': Decimal('0'), 'production_task': Decimal('0')}
            }
        }
        self.assertEqual(result, expected_result)

    def test_validate_costs_and_commitments(self):
        costs_and_commitments = {
            'all_sap_data': {},
            'current_year': {}
        }
        response = self.sap_service.validate_costs_and_commitments(costs_and_commitments)

        costs_and_commitments_not_valid = {}
        response2 = self.sap_service.validate_costs_and_commitments(costs_and_commitments_not_valid)

        self.assertEqual(response, True)
        self.assertEqual(response2, False)

    def test_sync_all_projects_from_sap(self):
        # Mock the SAP API response for current year costs
        # Using .01 suffix = planning task (should go to project_task, not production_task)
        mock_response_current_year_costs = MagicMock()
        mock_response_current_year_costs.status_code = 200
        mock_response_current_year_costs.json.return_value = {
            "d": {"results": [{"Posid": "{self.sapProjectId}.01", "Wkgbtr": Decimal('111.000')}]}
        }

        # Mock the SAP API response for current year commitments
        mock_response_current_year_commitments = MagicMock()
        mock_response_current_year_commitments.status_code = 200
        mock_response_current_year_commitments.json.return_value = {
            "d": {"results": [{"Posid": "{self.sapProjectId}.01", "Wkgbtr": Decimal('333.000')}]}
        }

        # Mock the session.get call to return the mocked responses in sequence
        self.sap_service.session.get.side_effect = [
            mock_response_current_year_costs,
            mock_response_current_year_commitments
        ]
        # Call the method sync_all_projects_from_sap to do sap fetch and save data to database
        self.sap_service.sync_all_projects_from_sap(for_financial_statement=True, sap_year=datetime.now().year)

        # get the data from database
        response = self.client.get("/sap-current-year-costs/{}/".format(datetime.now().year))
        data_in_database = response.data[0]
        # Planning tasks (ending in .01) should be in project_task, not production_task
        self.assertEqual(data_in_database['project_task_costs'], '111.000')
        self.assertEqual(data_in_database['project_task_commitments'], '333.000')
        # Production tasks should be 0
        self.assertEqual(data_in_database['production_task_costs'], '0.000')
        self.assertEqual(data_in_database['production_task_commitments'], '0.000')

    def test_calculate_values_with_dotted_format(self):
        """Test that old dotted format (e.g., 2814I03976.01) is correctly categorized"""
        sap_id = "2814I03976"
        costs = [
            {"Posid": "2814I03976.01", "Wkgbtr": "1000.000"},  # Planning task
            {"Posid": "2814I03976.02", "Wkgbtr": "2000.000"},  # Construction task
            {"Posid": "2814I03976.06", "Wkgbtr": "3000.000"},  # Construction task
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)
        
        self.assertEqual(result['project_task'], Decimal('1000.000'))
        self.assertEqual(result['production_task'], Decimal('5000.000'))

    def test_calculate_values_with_concatenated_format(self):
        """Test that new concatenated format (e.g., 2814I0397600101) is correctly categorized"""
        sap_id = "2814I03976"
        costs = [
            {"Posid": "2814I0397600101", "Wkgbtr": "1500.000"},  # Planning task
            {"Posid": "2814I0397600106", "Wkgbtr": "2500.000"},  # Construction task
            {"Posid": "2814I0397600199", "Wkgbtr": "3500.000"},  # Construction task
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)
        
        self.assertEqual(result['project_task'], Decimal('1500.000'))
        self.assertEqual(result['production_task'], Decimal('6000.000'))

    def test_calculate_values_with_mixed_formats(self):
        """Test that both old and new formats work together"""
        sap_id = "2814I03976"
        costs = [
            {"Posid": "2814I03976.01", "Wkgbtr": "1000.000"},     # Old format - planning
            {"Posid": "2814I0397600101", "Wkgbtr": "1500.000"},   # New format - planning
            {"Posid": "2814I03976.06", "Wkgbtr": "2000.000"},     # Old format - construction
            {"Posid": "2814I0397600106", "Wkgbtr": "2500.000"},   # New format - construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)
        
        self.assertEqual(result['project_task'], Decimal('2500.000'))
        self.assertEqual(result['production_task'], Decimal('4500.000'))

    def test_calculate_values_edge_case_sap_id_ending_in_01(self):
        """
        Test edge case: SAP ID itself ends in '01' (e.g., 2814I03901)
        Bare SAP ID should be categorized as construction, not planning
        """
        sap_id = "2814I03901"
        costs = [
            {"Posid": "2814I03901", "Wkgbtr": "1000.000"},         # Bare SAP ID - construction
            {"Posid": "2814I03901.01", "Wkgbtr": "1500.000"},      # Planning task (old format)
            {"Posid": "2814I0390100101", "Wkgbtr": "2000.000"},    # Planning task (new format)
            {"Posid": "2814I03901.02", "Wkgbtr": "2500.000"},      # Construction task (old format)
            {"Posid": "2814I0390100106", "Wkgbtr": "3000.000"},    # Construction task (new format)
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)
        
        # Planning tasks: 1500 + 2000 = 3500
        self.assertEqual(result['project_task'], Decimal('3500.000'))
        # Construction tasks: 1000 (bare) + 2500 + 3000 = 6500
        self.assertEqual(result['production_task'], Decimal('6500.000'))

    def test_calculate_values_io740_actual_data(self):
        """
        Test with actual production data structure from IO-740
        This was the original bug: planning costs showed as 0
        """
        sap_id = "2814I03976"
        costs = [
            {"Posid": "2814I03976", "Wkgbtr": "37.490"},           # Bare SAP ID
            {"Posid": "2814I0397600101", "Wkgbtr": "6000.000"},    # Planning task
            {"Posid": "2814I0397600106", "Wkgbtr": "180000.000"},  # Construction task
            {"Posid": "2814I0397600199", "Wkgbtr": "30000.000"},   # Construction task
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)
        
        # Planning: 6000
        self.assertEqual(result['project_task'], Decimal('6000.000'))
        # Construction: 37.490 + 180000 + 30000 = 210037.490
        self.assertEqual(result['production_task'], Decimal('210037.490'))
