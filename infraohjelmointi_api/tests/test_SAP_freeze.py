
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from infraohjelmointi_api.models import Project, SapCost
from infraohjelmointi_api.services.SapApiService import SapApiService
from infraohjelmointi_api.views import BaseViewSet

@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class TestSAPServiceFreeze(TestCase):
    project_1_Id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    sapProjectId = "2814I00708"

    def setUp(self):
        # connection setup
        self.sap_service = SapApiService()
        self.sap_service.sap_api_url = "http://fake-sap-api-url.com"
        # We need to set these to match how they are used in the service
        self.sap_service.sap_api_costs_endpoint = "costs?id={posid}&start={budat_start}&end={budat_end}"
        self.sap_service.sap_api_commitments_endpoint = "commitments?id={posid}&start={budat_start}&end={budat_end}"
        self.sap_service.session = MagicMock()
        
        # Ensure freeze date matches what's in the service (or we can override it in test)
        self.sap_service.sap_freeze_date = datetime(2026, 1, 30, 0, 0, 0, tzinfo=timezone.utc)
        self.sap_service.sap_freeze_year = 2025
        self.sap_service.sap_fetch_all_data_start_year = 2017

    @patch('infraohjelmointi_api.services.SapApiService.datetime')
    def test_get_project_costs_and_commitments_before_freeze(self, mock_datetime):
        """Test standard behavior before freeze date"""
        # Mock datetime.now() to return a date BEFORE freeze
        mock_datetime.now.return_value = datetime(2026, 1, 29, 0, 0, 0, tzinfo=timezone.utc)
        # We must also mock side effects or other methods if needed, but for now we just need 'now'
        
        # Mock fetch to return some data
        self.sap_service._SapApiService__fetch_costs_and_commitments_from_sap = MagicMock(return_value={
            "costs": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('100.000')}],
            "commitments": []
        })
        
        # Execute
        result = self.sap_service.get_all_project_costs_and_commitments_from_sap(self.sapProjectId)
        
        # Verify call args - should be normal start (2017)
        # We check the arguments passed to the internal fetch method
        args, kwargs = self.sap_service._SapApiService__fetch_costs_and_commitments_from_sap.call_args
        
        # args[0] is budat_start (should be 2017), because in non-freeze path it is positional
        self.assertEqual(args[0].year, 2017)

    @patch('infraohjelmointi_api.services.SapCostService.SapCostService.get_by_sap_id')
    @patch.object(SapApiService, '_SapApiService__fetch_costs_and_commitments_from_sap')
    @patch('infraohjelmointi_api.services.SapApiService.datetime') 
    def test_get_project_costs_and_commitments_after_freeze(self, mock_datetime, mock_fetch, mock_get_by_sap_id):
        """Test behavior AFTER freeze date"""
        # Mock datetime.now() to return a date AFTER freeze
        mock_datetime.now.return_value = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # 1. Setup Frozen Data in DB (2025)
        # Note: In real app, SapCost stores exact values.
        frozen_sap_cost = SapCost(
            year=2025,
            sap_id=self.sapProjectId,
            project_task_costs=Decimal('500.000'), # Frozen cost
            production_task_costs=Decimal('0.000'),
            project_task_commitments=Decimal('0.000'), 
            production_task_commitments=Decimal('0.000')
        )
        mock_get_by_sap_id.return_value = [frozen_sap_cost]
        
        # 2. Setup New SAP Data (2026)
        # This is what __fetch... returns. It simulates fetching ONLY 2026 data.
        mock_fetch.return_value = {
            "costs": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('100.000')}], # New cost
            "commitments": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('50.000')}] # All commitments
        }
        
        # Execute
        result = self.sap_service.get_all_project_costs_and_commitments_from_sap(self.sapProjectId)
        
        # 3. Verify fetch arguments
        # fetching logic:
        # - budat_start (for costs) should be 2026-01-01
        # - budat_start_commitments should be 2017-01-01
        
        args, kwargs = mock_fetch.call_args
        self.assertEqual(kwargs['budat_start'].year, 2026) 
        self.assertEqual(kwargs['budat_start_commitments'].year, 2017)
        
        # 4. Verify Final Result Summing
        # Should be Frozen(500) + New(100) = 600
        self.assertEqual(result['costs']['project_task'], Decimal('600.000'))
        self.assertEqual(result['commitments']['project_task'], Decimal('50.000'))

    @patch('infraohjelmointi_api.services.SapCostService.SapCostService.get_by_sap_id')
    @patch('infraohjelmointi_api.services.SapApiService.datetime')
    def test_get_costs_and_commitments_by_year_after_freeze_2025(self, mock_datetime, mock_get_by_sap_id):
        """Test that get_costs_and_commitments_by_year returns frozen 2025 data after freeze date"""
        # Mock datetime.now() to return a timezone-aware date AFTER freeze
        mock_datetime.now.return_value = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # Setup frozen 2025 data
        frozen_sap_cost = SapCost(
            year=2025,
            sap_id=self.sapProjectId,
            project_task_costs=Decimal('300.000'),
            production_task_costs=Decimal('200.000'),
            project_task_commitments=Decimal('150.000'),
            production_task_commitments=Decimal('100.000')
        )
        mock_get_by_sap_id.return_value = [frozen_sap_cost]
        
        # Execute - requesting 2025 data after freeze
        result = self.sap_service.get_costs_and_commitments_by_year(self.sapProjectId, 2025)
        
        # Verify it returns frozen data from DB, not from SAP API
        self.assertEqual(result['costs']['project_task'], Decimal('300.000'))
        self.assertEqual(result['costs']['production_task'], Decimal('200.000'))
        self.assertEqual(result['commitments']['project_task'], Decimal('150.000'))
        self.assertEqual(result['commitments']['production_task'], Decimal('100.000'))

    @patch.object(SapApiService, '_SapApiService__fetch_costs_and_commitments_from_sap')
    @patch('infraohjelmointi_api.services.SapApiService.datetime')
    def test_get_costs_and_commitments_by_year_after_freeze_2026(self, mock_datetime, mock_fetch):
        """Test that get_costs_and_commitments_by_year fetches 2026 data from new SAP after freeze date"""
        # Mock datetime.now() to return a timezone-aware date AFTER freeze
        mock_datetime.now.return_value = datetime(2026, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # Mock SAP API response for 2026 data
        mock_fetch.return_value = {
            "costs": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('75.000')}],
            "commitments": [{"Posid": f"{self.sapProjectId}.01", "Wkgbtr": Decimal('25.000')}]
        }
        
        # Execute - requesting 2026 data after freeze
        result = self.sap_service.get_costs_and_commitments_by_year(self.sapProjectId, 2026)
        
        # Verify it fetches from SAP API (not frozen)
        self.assertEqual(result['costs']['project_task'], Decimal('75.000'))
        # Verify fetch was called
        mock_fetch.assert_called_once()
