import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime
from infraohjelmointi_api.services.SapApiService import SapApiService

class TestSAPService(unittest.TestCase):
    def setUp(self):
        # connection setup
        self.sap_service = SapApiService()
        self.sap_service.sap_api_url = "http://fake-sap-api-url.com"
        self.sap_service.sap_api_costs_endpoint = "$/costs?id='{posid}'&start={budat_start}&end={budat_end}"
        self.sap_service.sap_api_commitments_endpoint = "$/costs?id='{posid}'&start={budat_start}&end={budat_end}"
        self.sap_service.session = MagicMock()

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

        # Mock the ProjectService.get_by_sap_id to return a project with a planning start year
        mock_project = MagicMock()
        mock_project.planningStartYear = 2022
        mock_get_by_sap_id.return_value = [mock_project]

        # Call the function with a known SAP ID
        # Model of the result from function:
        # {
        # 'all_sap_data': {
        #     'costs': {
        #         'project_task': Decimal('100.000'), 
        #         'production_task': Decimal('0')
        #     }, 
        #     'commitments': {
        #         'project_task': Decimal('50.000'), 
        #         'production_task': Decimal('0')
        #     }
        # }, 
        # 'current_year': {
        #     'costs': {
        #         'project_task': Decimal('100.000'), 
        #         'production_task': Decimal('0')
        #     }, 
        #     'commitments': {
        #         'project_task': Decimal('50.000'), 
        #         'production_task': Decimal('0')
        #     }
        # }
        # }
        project_id = '123'
        result = self.sap_service.get_project_costs_and_commitments_from_sap(project_id)

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
        ).replace(year=mock_project.planningStartYear).strftime("%Y-%m-%dT%H:%M:%S")
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
