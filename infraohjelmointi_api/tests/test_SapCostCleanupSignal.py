from datetime import datetime
from decimal import Decimal
from django.test import TransactionTestCase
from infraohjelmointi_api.models import (
    Project,
    SapCost,
    SapCurrentYear,
    ProjectType,
)
import uuid


class SapCostCleanupSignalTestCase(TransactionTestCase):
    """Test that SAP cost records are cleaned up when sapProject changes"""

    def setUp(self):
        """Set up test data"""
        self.project_type = ProjectType.objects.create(
            id=uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166"),
            value="Test Project Type"
        )

        self.project = Project.objects.create(
            id=uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042"),
            name="Test Project",
            description="Test description",
            type=self.project_type,
            sapProject="2814I00708"
        )

        self.current_year = datetime.now().year

        # Create SapCost record linked to the project
        self.sap_cost = SapCost.objects.create(
            project=self.project,
            year=self.current_year,
            sap_id="2814I00708",
            project_task_costs=Decimal("1000.000"),
            project_task_commitments=Decimal("500.000"),
            production_task_costs=Decimal("2000.000"),
            production_task_commitments=Decimal("1000.000"),
        )

        # Create SapCurrentYear record linked to the project
        self.sap_current_year = SapCurrentYear.objects.create(
            project=self.project,
            year=self.current_year,
            sap_id="2814I00708",
            project_task_costs=Decimal("100.000"),
            project_task_commitments=Decimal("50.000"),
            production_task_costs=Decimal("200.000"),
            production_task_commitments=Decimal("100.000"),
        )

    def test_sap_costs_deleted_when_sap_project_set_to_null(self):
        """When sapProject is changed from a valid value to null, SAP cost records should be deleted"""
        # Verify records exist before
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

        # Change sapProject to null
        self.project.sapProject = None
        self.project.save(update_fields=["sapProject"])

        # Records should be deleted
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 0)

    def test_sap_costs_deleted_when_sap_project_set_to_empty_string(self):
        """When sapProject is changed to empty string, SAP cost records should be deleted"""
        # Verify records exist before
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

        # Change sapProject to empty string
        self.project.sapProject = ""
        self.project.save(update_fields=["sapProject"])

        # Records should be deleted
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 0)

    def test_sap_costs_deleted_when_sap_project_set_to_zero(self):
        """When sapProject is changed to '0' (invalid value), SAP cost records should be deleted"""
        # Verify records exist before
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

        # Change sapProject to "0" (the workaround user tried in IO-777)
        self.project.sapProject = "0"
        self.project.save(update_fields=["sapProject"])

        # Records should be deleted
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 0)

    def test_sap_costs_deleted_when_sap_project_changed_to_different_value(self):
        """When sapProject is changed to a different valid value, old SAP cost records should be deleted"""
        # Verify records exist before
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

        # Change sapProject to a different value
        self.project.sapProject = "2814I99999"
        self.project.save(update_fields=["sapProject"])

        # Old records should be deleted (new ones will be created on next SAP sync)
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 0)

    def test_sap_costs_not_affected_when_sap_project_unchanged(self):
        """When project is saved but sapProject doesn't change, SAP cost records should remain"""
        # Verify records exist before
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

        # Save project without changing sapProject
        self.project.name = "Updated Name"
        self.project.save(update_fields=["name"])

        # Records should still exist
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

    def test_sap_costs_not_affected_when_sap_project_saved_with_same_value(self):
        """When sapProject is saved but value is the same, SAP cost records should remain"""
        # Verify records exist before
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

        # Save with same sapProject value
        self.project.sapProject = "2814I00708"  # Same value
        self.project.save(update_fields=["sapProject"])

        # Records should still exist
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 1)

    def test_no_records_to_delete_when_sap_project_set_on_new_project(self):
        """When sapProject is set on a new project (from null), no records exist to delete"""
        # Create a new project without sapProject
        new_project = Project.objects.create(
            name="New Project",
            description="New description",
            type=self.project_type,
            sapProject=None
        )

        # Set sapProject for the first time
        new_project.sapProject = "2814I12345"
        new_project.save(update_fields=["sapProject"])

        # No error should occur, and no records should exist
        self.assertEqual(SapCost.objects.filter(project=new_project).count(), 0)
        self.assertEqual(SapCurrentYear.objects.filter(project=new_project).count(), 0)

    def test_only_project_specific_records_deleted(self):
        """When sapProject changes, only that project's records are deleted, not others"""
        # Create another project with its own SAP costs
        other_project = Project.objects.create(
            name="Other Project",
            description="Other description",
            type=self.project_type,
            sapProject="2814I11111"
        )

        other_sap_cost = SapCost.objects.create(
            project=other_project,
            year=self.current_year,
            sap_id="2814I11111",
            project_task_costs=Decimal("5000.000"),
        )

        other_sap_current_year = SapCurrentYear.objects.create(
            project=other_project,
            year=self.current_year,
            sap_id="2814I11111",
            project_task_costs=Decimal("500.000"),
        )

        # Verify both projects have records
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 1)
        self.assertEqual(SapCost.objects.filter(project=other_project).count(), 1)

        # Change sapProject on first project
        self.project.sapProject = None
        self.project.save(update_fields=["sapProject"])

        # First project's records should be deleted
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 0)
        self.assertEqual(SapCurrentYear.objects.filter(project=self.project).count(), 0)

        # Other project's records should remain
        self.assertEqual(SapCost.objects.filter(project=other_project).count(), 1)
        self.assertEqual(SapCurrentYear.objects.filter(project=other_project).count(), 1)

    def test_multiple_year_records_deleted(self):
        """When sapProject changes, records from all years should be deleted"""
        # Create records for previous years
        SapCost.objects.create(
            project=self.project,
            year=self.current_year - 1,
            sap_id="2814I00708",
            project_task_costs=Decimal("800.000"),
        )
        SapCost.objects.create(
            project=self.project,
            year=self.current_year - 2,
            sap_id="2814I00708",
            project_task_costs=Decimal("600.000"),
        )

        # Verify we have records for multiple years
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 3)

        # Change sapProject
        self.project.sapProject = None
        self.project.save(update_fields=["sapProject"])

        # All records should be deleted
        self.assertEqual(SapCost.objects.filter(project=self.project).count(), 0)
