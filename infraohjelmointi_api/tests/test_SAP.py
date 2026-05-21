import uuid
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase
from overrides import override

from infraohjelmointi_api.models import Project, ProjectGroup, ProjectPhase, SapCurrentYear
from infraohjelmointi_api.serializers import ProjectGetSerializer
from infraohjelmointi_api.services.SapApiService import SapApiService, SapAuthenticationError
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
        # Use pre-freeze logic so URL assertions match (otherwise after 2026-01-30 different URLs are called)
        self.sap_service.sap_freeze_date = datetime(2030, 1, 30, 0, 0, 0, tzinfo=timezone.utc)
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
        # NOTE: Posid must start with the actual SAP ID for correct classification
        mock_response_current_year_costs = MagicMock()
        mock_response_current_year_costs.status_code = 200
        mock_response_current_year_costs.json.return_value = {
            "d": {"results": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('111.000')}]}
        }

        # Mock the SAP API response for current year commitments
        mock_response_current_year_commitments = MagicMock()
        mock_response_current_year_commitments.status_code = 200
        mock_response_current_year_commitments.json.return_value = {
            "d": {"results": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('333.000')}]}
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
        # Planning tasks (first segment .01) should be in project_task, not production_task
        self.assertEqual(data_in_database['project_task_costs'], '111.000')
        self.assertEqual(data_in_database['project_task_commitments'], '333.000')
        # Production tasks should be 0
        self.assertEqual(data_in_database['production_task_costs'], '0.000')
        self.assertEqual(data_in_database['production_task_commitments'], '0.000')

    def test_group_totals_not_duplicated_for_shared_sap_id(self):
        shared_sap_id = "2814I01001"
        other_sap_id = "2814I02002"
        current_year = datetime.now().year
        group = ProjectGroup.objects.create(name="Shared SAP Group")
        phase, _ = ProjectPhase.objects.get_or_create(value="proposal", defaults={"index": 1})

        Project.objects.create(
            name="Shared Project 1",
            description="desc",
            sapProject=shared_sap_id,
            projectGroup=group,
            phase=phase,
        )
        Project.objects.create(
            name="Shared Project 2",
            description="desc",
            sapProject=shared_sap_id,
            projectGroup=group,
            phase=phase,
        )
        Project.objects.create(
            name="Other Project",
            description="desc",
            sapProject=other_sap_id,
            projectGroup=group,
            phase=phase,
        )

        shared_payload = {
            "costs": [{"Posid": f"{shared_sap_id}.01", "Wkgbtr": "100.000"}],
            "commitments": [{"Posid": f"{shared_sap_id}.01", "Wkgbtr": "50.000"}],
        }
        other_payload = {
            "costs": [{"Posid": f"{other_sap_id}.01", "Wkgbtr": "200.000"}],
            "commitments": [{"Posid": f"{other_sap_id}.01", "Wkgbtr": "60.000"}],
        }

        zero_payload = {
            "costs": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": "0"}],
            "commitments": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": "0"}],
        }

        def fake_fetch(budat_start, budat_end, sap_id, all_sap_commitments):
            if sap_id == shared_sap_id:
                return shared_payload
            if sap_id == other_sap_id:
                return other_payload
            if sap_id == self.sapProjectId:
                return zero_payload
            raise AssertionError(f"Unexpected sap id {sap_id}")

        with patch.object(
            self.sap_service,
            "_SapApiService__fetch_costs_and_commitments_from_sap",
            side_effect=fake_fetch,
        ):
            self.sap_service.sync_all_projects_from_sap(
                for_financial_statement=True, sap_year=current_year
            )

        group_entry = SapCurrentYear.objects.get(
            project_group=group, project__isnull=True, year=current_year
        )

        self.assertEqual(group_entry.group_combined_costs, Decimal("300.000"))
        self.assertEqual(group_entry.group_combined_commitments, Decimal("110.000"))

    def test_calculate_values_with_dotted_format(self):
        """Test that old dotted format (e.g., 2814I90003.01) is correctly categorized"""
        sap_id = "2814I90003"
        costs = [
            {"Posid": "2814I90003.01", "Wkgbtr": "1000.000"},  # Planning task
            {"Posid": "2814I90003.02", "Wkgbtr": "2000.000"},  # Construction task
            {"Posid": "2814I90003.06", "Wkgbtr": "3000.000"},  # Construction task
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('1000.000'))
        self.assertEqual(result['production_task'], Decimal('5000.000'))

    def test_calculate_values_with_concatenated_format(self):
        """Test that new concatenated format (e.g., 2814I9000300101) is correctly categorized"""
        sap_id = "2814I90003"
        costs = [
            {"Posid": "2814I9000300101", "Wkgbtr": "1500.000"},  # Planning task (Phase 001)
            {"Posid": "2814I9000300106", "Wkgbtr": "2500.000"},  # Planning task (Phase 001)
            {"Posid": "2814I9000300199", "Wkgbtr": "3500.000"},  # Planning task (Phase 001)
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('7500.000'))
        self.assertEqual(result['production_task'], Decimal('0.000'))

    def test_calculate_values_with_mixed_formats(self):
        """Test that both old and new formats work together"""
        sap_id = "2814I90003"
        costs = [
            {"Posid": "2814I90003.01", "Wkgbtr": "1000.000"},     # Old format - planning
            {"Posid": "2814I9000300101", "Wkgbtr": "1500.000"},   # New format - planning
            {"Posid": "2814I90003.06", "Wkgbtr": "2000.000"},     # Old format - construction
            {"Posid": "2814I9000300106", "Wkgbtr": "2500.000"},   # New format - planning (Phase 001)
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('5000.000'))
        self.assertEqual(result['production_task'], Decimal('2000.000'))

    def test_calculate_values_edge_case_sap_id_ending_in_01(self):
        """
        Test edge case: SAP ID itself ends in '01' (e.g., 2814I90001)
        Bare SAP ID should be categorized as construction, not planning
        """
        sap_id = "2814I90001"
        costs = [
            {"Posid": "2814I90001", "Wkgbtr": "1000.000"},         # Bare SAP ID - construction
            {"Posid": "2814I90001.01", "Wkgbtr": "1500.000"},      # Planning task (old format)
            {"Posid": "2814I9000100101", "Wkgbtr": "2000.000"},    # Planning task (new format)
            {"Posid": "2814I90001.02", "Wkgbtr": "2500.000"},      # Construction task (old format)
            {"Posid": "2814I9000100106", "Wkgbtr": "3000.000"},    # Planning task (new format, Phase 001)
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning tasks: 1500 + 2000 + 3000 = 6500
        self.assertEqual(result['project_task'], Decimal('6500.000'))
        # Construction tasks: 1000 (bare) + 2500 = 3500
        self.assertEqual(result['production_task'], Decimal('3500.000'))

    def test_calculate_values_actual_data(self):
        """
        Test with actual production data structure.
        Phase 001 -> Planning.
        Phase 001 but Task 06? -> Planning (Phase overrides Task)
        """
        sap_id = "2814I90003"
        costs = [
            {"Posid": "2814I90003", "Wkgbtr": "37.490"},           # Bare SAP ID -> construction (default)
            {"Posid": "2814I9000300101", "Wkgbtr": "6000.000"},    # Planning (Phase 001)
            {"Posid": "2814I9000300106", "Wkgbtr": "180000.000"},  # Planning (Phase 001)
            {"Posid": "2814I9000300199", "Wkgbtr": "30000.000"},   # Planning (Phase 001)
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning: 6000 + 180000 + 30000 = 216000
        self.assertEqual(result['project_task'], Decimal('216000.000'))
        # Construction: 37.490
        self.assertEqual(result['production_task'], Decimal('37.490'))

    def test_calculate_values_dotted_construction_first_segment(self):
        """
        IO-789: dotted POSIDs classify by the FIRST non-empty segment after the
        SAP id (the *group identifier* per the Confluence doc "Infraohjelmointi
        API -sovellus"): `.01` = Hanketehtävät (planning), `.02/.03/.04` =
        Tuotantotehtävät (construction). Deeper WBS levels (`.03.01`,
        `.03.01.05`, …) inherit their parent group and MUST NOT flip the bucket.

        Shapes covered: `.03.01`, `.03.02`, `.03.01.03`, `.03.01.05`. The bug
        was that the multi-level rows landed under planning; they must all
        land under construction because the first segment is `.03`.
        """
        sap_id = "2814I90004"
        costs = [
            {"Posid": "2814I90004.03.01", "Wkgbtr": "811295.42"},  # group .03 -> construction
            {"Posid": "2814I90004.03.02", "Wkgbtr": "1816.08"},    # group .03 -> construction
            {"Posid": "2814I90004.03.01.03", "Wkgbtr": "500.00"},  # group .03 -> construction
            {"Posid": "2814I90004.03.01.05", "Wkgbtr": "250.00"},  # group .03 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('0.00'))
        self.assertEqual(result['production_task'], Decimal('813861.50'))

    def test_calculate_values_planning_subtasks(self):
        """Dotted `.01` and any of its subgroups are planning.

        Per Confluence: subgroup costs are added to the main group they belong
        to. So `.01.01` and `.01.02` are both subgroups of group `.01`
        (planning) and inherit that bucket — the trailing `.02` does NOT make
        the row construction.
        """
        sap_id = "2814I90004"
        costs = [
            {"Posid": "2814I90004.01", "Wkgbtr": "100000.00"},     # group .01 -> planning
            {"Posid": "2814I90004.01.01", "Wkgbtr": "50000.00"},   # group .01 -> planning
            {"Posid": "2814I90004.01.02", "Wkgbtr": "25000.00"},   # group .01 -> planning
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('175000.00'))
        self.assertEqual(result['production_task'], Decimal('0.00'))

    def test_calculate_values_mixed_hierarchy(self):
        """Mixed dotted hierarchy: classification is by the first segment
        (group identifier); subgroups inherit the parent group's bucket."""
        sap_id = "2814I90004"
        costs = [
            {"Posid": "2814I90004.01", "Wkgbtr": "100000.00"},     # group .01 -> planning
            {"Posid": "2814I90004.01.01", "Wkgbtr": "50000.00"},   # group .01 -> planning
            {"Posid": "2814I90004.01.02", "Wkgbtr": "25000.00"},   # group .01 -> planning
            {"Posid": "2814I90004.03", "Wkgbtr": "200000.00"},     # group .03 -> construction
            {"Posid": "2814I90004.03.01", "Wkgbtr": "811295.42"},  # group .03 -> construction (IO-789)
            {"Posid": "2814I90004.03.02", "Wkgbtr": "1816.08"},    # group .03 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning: 100000 + 50000 + 25000 = 175000.00
        self.assertEqual(result['project_task'], Decimal('175000.00'))
        # Construction: 200000 + 811295.42 + 1816.08 = 1013111.50
        self.assertEqual(result['production_task'], Decimal('1013111.50'))

    def test_calculate_values_concatenated_subproject_rule(self):
        """Concatenated POSIDs classify by subproject (first 3 chars after SAP ID).

        "001" is SUUNNITTELUVAIHE (planning); "002"+ is construction. The task
        suffix is NOT consulted in this format — e.g. `...00106` is planning
        because subproject is "001", not because task ends in "06".
        """
        sap_id = "2814I90003"
        costs = [
            {"Posid": "2814I9000300101", "Wkgbtr": "6000.00"},    # sub 001 -> planning
            {"Posid": "2814I9000300106", "Wkgbtr": "180000.00"},  # sub 001 -> planning
            {"Posid": "2814I9000300199", "Wkgbtr": "30000.00"},   # sub 001 -> planning
            {"Posid": "2814I9000300201", "Wkgbtr": "2004.47"},    # sub 002 -> construction
            {"Posid": "2814I9000300299", "Wkgbtr": "500.00"},     # sub 002 -> construction
            {"Posid": "2814I9000300301", "Wkgbtr": "400.00"},     # sub 003 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('216000.00'))
        self.assertEqual(result['production_task'], Decimal('2904.47'))

    def test_calculate_values_deep_nested_dotted(self):
        """Deeply nested dotted POSIDs — first segment (group) always decides;
        deeper WBS levels never flip the bucket."""
        sap_id = "2814I90004"
        costs = [
            {"Posid": "2814I90004.01.01.01", "Wkgbtr": "1000.00"},  # group .01 -> planning
            {"Posid": "2814I90004.01.01.02", "Wkgbtr": "2000.00"},  # group .01 -> planning
            {"Posid": "2814I90004.03.01.01", "Wkgbtr": "3000.00"},  # group .03 -> construction
            {"Posid": "2814I90004.03.02.99", "Wkgbtr": "4000.00"},  # group .03 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning: 1000 + 2000 = 3000; Construction: 3000 + 4000 = 7000
        self.assertEqual(result['project_task'], Decimal('3000.00'))
        self.assertEqual(result['production_task'], Decimal('7000.00'))

    def test_calculate_values_prod_log_shapes(self):
        """Smoke regression over every POSID shape seen in prod sync logs.

        Covers bare SAP IDs, concatenated subproject 001/002, dotted group
        `.01` and `.03/.04`, and multi-level dotted `.03.01` (IO-789) plus
        deeper `.03.01.03`/`.03.01.05`. If any of these drift, classification
        is off.
        """
        sap_id = "2814I90004"
        costs = [
            {"Posid": "2814I90004", "Wkgbtr": "10.00"},            # bare -> construction
            {"Posid": "2814I9000400101", "Wkgbtr": "42598.65"},    # sub 001 -> planning
            {"Posid": "2814I9000400201", "Wkgbtr": "2004.47"},     # sub 002 -> construction
            {"Posid": "2814I90004.01", "Wkgbtr": "100.00"},        # group .01 -> planning
            {"Posid": "2814I90004.03", "Wkgbtr": "200.00"},        # group .03 -> construction
            {"Posid": "2814I90004.04", "Wkgbtr": "300.00"},        # group .04 -> construction
            {"Posid": "2814I90004.03.01", "Wkgbtr": "811295.42"},  # group .03 -> construction (IO-789)
            {"Posid": "2814I90004.03.02", "Wkgbtr": "1816.08"},    # group .03 -> construction
            {"Posid": "2814I90004.03.01.03", "Wkgbtr": "50.00"},   # group .03 -> construction
            {"Posid": "2814I90004.03.01.05", "Wkgbtr": "75.00"},   # group .03 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning: 42598.65 + 100.00 = 42698.65
        self.assertEqual(result['project_task'], Decimal('42698.65'))
        # Construction: 10 + 2004.47 + 200 + 300 + 811295.42 + 1816.08 + 50 + 75 = 815750.97
        self.assertEqual(result['production_task'], Decimal('815750.97'))

    def test_calculate_values_concat_subproject_000_fallback(self):
        """Subproject "000" (root-level bookings, no subproject assigned) falls
        back to the task suffix: tail `01` = planning, anything else = construction.

        This preserves pre-IO-740 behaviour for root-level bookings. Subprojects
        other than 001/000 always classify as construction.
        """
        sap_id = "2814I90002"
        costs = [
            {"Posid": "2814I9000200001", "Wkgbtr": "100.00"},   # sub 000, task 01 -> planning
            {"Posid": "2814I9000200002", "Wkgbtr": "200.00"},   # sub 000, task 02 -> construction
            {"Posid": "2814I9000200006", "Wkgbtr": "300.00"},   # sub 000, task 06 -> construction
            {"Posid": "2814I9000200099", "Wkgbtr": "400.00"},   # sub 000, task 99 -> construction
            {"Posid": "2814I9000200501", "Wkgbtr": "500.00"},   # sub 005 (unknown) -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        self.assertEqual(result['project_task'], Decimal('100.00'))
        self.assertEqual(result['production_task'], Decimal('1400.00'))

    def test_calculate_values_concat_sub_000_and_001_mix(self):
        """IO-789: covers the subproject 000 + 001 concat shapes seen in prod
        sync logs (bare row, sub 000 task 01 fallback to planning, sub 001
        rows always planning regardless of task suffix, sub 002+ construction).
        """
        sap_id = "2814I90002"
        costs = [
            {"Posid": "2814I90002", "Wkgbtr": "5.00"},          # bare -> construction
            {"Posid": "2814I9000200001", "Wkgbtr": "1000.00"},  # sub 000, task 01 -> planning
            {"Posid": "2814I9000200101", "Wkgbtr": "24952.82"}, # sub 001 -> planning
            {"Posid": "2814I9000200199", "Wkgbtr": "1690.04"},  # sub 001 -> planning
            {"Posid": "2814I9000200201", "Wkgbtr": "273092.90"},# sub 002 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning: 1000 + 24952.82 + 1690.04 = 27642.86
        self.assertEqual(result['project_task'], Decimal('27642.86'))
        # Construction: 5 + 273092.90 = 273097.90
        self.assertEqual(result['production_task'], Decimal('273097.90'))

    def test_calculate_values_concat_sub_001_repeated_rows(self):
        """IO-740 regression: covers the concat shapes where multiple rows
        share the same sub 001 POSID (repeated bookings against the same
        WBS) and must all be summed into planning, not construction."""
        sap_id = "2814I90003"
        costs = [
            {"Posid": "2814I90003", "Wkgbtr": "37.49"},             # bare -> construction
            {"Posid": "2814I9000300106", "Wkgbtr": "32209.11"},     # sub 001 -> planning
            {"Posid": "2814I9000300106", "Wkgbtr": "2027.26"},      # sub 001 -> planning
            {"Posid": "2814I9000300106", "Wkgbtr": "6203.57"},      # sub 001 -> planning
            {"Posid": "2814I9000300199", "Wkgbtr": "711.11"},       # sub 001 -> planning
            {"Posid": "2814I9000300199", "Wkgbtr": "1145.86"},      # sub 001 -> planning
            {"Posid": "2814I9000300199", "Wkgbtr": "301.74"},       # sub 001 -> planning
            {"Posid": "2814I9000300201", "Wkgbtr": "2004.47"},      # sub 002 -> construction
        ]
        result = self.sap_service._SapApiService__calculate_values(sap_id, costs)

        # Planning: 32209.11 + 2027.26 + 6203.57 + 711.11 + 1145.86 + 301.74 = 42598.65
        self.assertEqual(result['project_task'], Decimal('42598.65'))
        # Construction: 37.49 + 2004.47 = 2041.96
        self.assertEqual(result['production_task'], Decimal('2041.96'))

    def test_make_sap_request_401_raises_sap_authentication_error(self):
        """IO-790: 401 response raises SapAuthenticationError and aborts (no hammering SAP)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.json.side_effect = ValueError("HTML body")
        mock_response.text = "<html>Anmeldung fehlgeschlagen</html>"
        mock_response.raw = MagicMock()
        mock_response.content = b"<html>"
        self.sap_service.session.get.return_value = mock_response

        with self.assertRaises(SapAuthenticationError) as ctx:
            self.sap_service._SapApiService__make_sap_request("http://fake/costs", "2814I00708", "costs")

        self.assertIn("401", str(ctx.exception))
        self.assertIn("2814I00708", str(ctx.exception))

    def test_log_response_error_non_json_body(self):
        """IO-790: __log_response_error handles non-JSON (e.g. 401 HTML) without raising."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.reason = "Unauthorized"
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "<html>Login failed</html>"
        self.sap_service._SapApiService__log_response_error(mock_response, "test-id")
        # No exception; would have raised JSONDecodeError before the fix

    def test_sync_all_projects_from_sap_aborts_on_first_401(self):
        """IO-790: sync aborts on first 401 and re-raises SapAuthenticationError."""
        mock_401 = MagicMock()
        mock_401.status_code = 401
        mock_401.reason = "Unauthorized"
        mock_401.json.side_effect = ValueError("HTML")
        mock_401.text = "<html>401</html>"
        mock_401.raw = MagicMock()
        mock_401.content = b"<html>"
        self.sap_service.session.get.return_value = mock_401

        with self.assertRaises(SapAuthenticationError):
            self.sap_service.sync_all_projects_from_sap(for_financial_statement=True, sap_year=datetime.now().year)

    def test_get_currentYearsSapValue_bulk_context_keys_io796(self):
        """Planning list used sap_values_by_project; serializer expected projects_to_sap_values (IO-796)."""
        year = datetime.now().year
        scy = SapCurrentYear.objects.create(
            project=self.project,
            year=year,
            sap_id=self.sapProjectId,
            project_task_costs=Decimal("11.000"),
            production_task_costs=Decimal("22.000"),
            project_task_commitments=Decimal("0.000"),
            production_task_commitments=Decimal("0.000"),
        )
        bulk_row = [scy]

        for ctx_key in ("projects_to_sap_values", "sap_values_by_project"):
            serializer = ProjectGetSerializer(context={ctx_key: {self.project.id: bulk_row}})
            out = serializer.get_currentYearsSapValue(self.project)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["year"], year)
            self.assertEqual(Decimal(str(out[0]["project_task_costs"])), Decimal("11.000"))
            self.assertEqual(Decimal(str(out[0]["production_task_costs"])), Decimal("22.000"))

    @patch('infraohjelmointi_api.management.commands.fetchsapdatabyyear.SapApiService')
    def test_fetchsapdatabyyear_force_refetch_bypasses_freeze(self, mock_service_cls):
        """IO-740/IO-789: --force-refetch pushes sap_freeze_date to year 9999 so
        frozen-year rows (IO-790) are re-fetched from SAP instead of echoed from DB.
        """
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        out = StringIO()
        call_command('fetchsapdatabyyear', year=2025, force_refetch=True, stdout=out)

        self.assertEqual(
            mock_service.sap_freeze_date,
            datetime(9999, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        mock_service.sync_all_projects_from_sap.assert_called_once_with(
            for_financial_statement=True, sap_year=2025
        )
        self.assertIn("--force-refetch", out.getvalue())

    @patch('infraohjelmointi_api.management.commands.fetchsapdatabyyear.SapApiService')
    def test_fetchsapdatabyyear_without_force_refetch_preserves_freeze(self, mock_service_cls):
        """Without --force-refetch the command must NOT touch sap_freeze_date,
        so the IO-790 freeze continues to short-circuit year 2025 fetches to DB.
        """
        sentinel = datetime(2026, 1, 30, 0, 0, 0, tzinfo=timezone.utc)
        mock_service = MagicMock()
        mock_service.sap_freeze_date = sentinel
        mock_service_cls.return_value = mock_service

        out = StringIO()
        call_command('fetchsapdatabyyear', year=2025, stdout=out)

        self.assertEqual(mock_service.sap_freeze_date, sentinel)
        mock_service.sync_all_projects_from_sap.assert_called_once_with(
            for_financial_statement=True, sap_year=2025
        )
        self.assertNotIn("--force-refetch", out.getvalue())

