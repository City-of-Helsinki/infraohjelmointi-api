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
        mock_response_costs = MagicMock()
        mock_response_costs.status_code = 200
        mock_response_costs.json.return_value = {
            "d": {"results": [{"Posid": "123.01", "Wkgbtr": Decimal('100.000')}]}
        }

        # Mock the SAP API response for commitments
        mock_response_commitments = MagicMock()
        mock_response_commitments.status_code = 200
        mock_response_commitments.json.return_value = {
            "d": {"results": [{"Posid": "123.01", "Wkgbtr": Decimal('50.000')}]}
        }

        # Mock the session.get call to return the mocked responses in sequence
        self.sap_service.session.get.side_effect = [mock_response_costs, mock_response_commitments]

        # Mock the ProjectService.get_by_sap_id to return a project with a planning start year
        mock_project = MagicMock()
        mock_project.planningStartYear = 2022
        mock_get_by_sap_id.return_value = [mock_project]

        # Call the function with a known SAP ID
        project_id = '123'
        result = self.sap_service.get_project_costs_and_commitments_from_sap(project_id)

        # Assertions to ensure the returned data structure is as expected
        self.assertIn('costs', result)
        self.assertIn('commitments', result)
        self.assertEqual(result['costs']['project_task'], Decimal('100.000'))
        self.assertEqual(result['costs']['production_task'], Decimal('0'))
        self.assertEqual(result['commitments']['project_task'], Decimal('50.000'))
        self.assertEqual(result['commitments']['production_task'], Decimal('0'))

        # Assert that the session.get was called with the correct URL and parameters
        start_date = datetime.now().replace(
            month=1, day=1, hour=0, minute=0, second=0
        ).replace(year=mock_project.planningStartYear).strftime("%Y-%m-%dT%H:%M:%S")
        end_date = datetime.now().replace(
            year=datetime.now().year + 1, month=1, day=1, hour=0, minute=0, second=0
        ).strftime("%Y-%m-%dT%H:%M:%S")
        expected_costs_url = f"{self.sap_service.sap_api_url}{self.sap_service.sap_api_costs_endpoint}".format(posid=project_id, budat_start=start_date, budat_end= end_date)
        expected_commitments_url = f"{self.sap_service.sap_api_url}{self.sap_service.sap_api_commitments_endpoint}".format(posid=project_id, budat_start=start_date, budat_end= end_date)
        self.sap_service.session.get.assert_any_call(expected_costs_url)
        self.sap_service.session.get.assert_any_call(expected_commitments_url)
