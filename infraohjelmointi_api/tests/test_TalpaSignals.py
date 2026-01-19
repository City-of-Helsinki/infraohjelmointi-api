from django.test import TransactionTestCase
from django.db import transaction
from infraohjelmointi_api.models import (
    Project,
    TalpaProjectOpening,
    Person,
    ProjectType,
    ProjectPhase,
    ProjectCategory,
    ProjectClass,
)
import uuid


class TalpaSignalsTestCase(TransactionTestCase):
    """Essential unit tests for Talpa signals"""

    def setUp(self):
        """Set up test data"""
        # Create test Person
        self.person = Person.objects.create(
            id=uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc"),
            firstName="Test",
            lastName="User",
            email="test@example.com"
        )
        
        # Create test ProjectType
        self.project_type = ProjectType.objects.create(
            id=uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166"),
            value="Test Project Type"
        )
        
        # Create test ProjectPhase
        self.project_phase = ProjectPhase.objects.create(
            id=uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256"),
            value="Test Phase"
        )
        
        # Create test ProjectCategory
        self.project_category = ProjectCategory.objects.create(
            id=uuid.UUID("dbc92a70-8a8a-4a25-8014-14c7d16eb86c"),
            value="K5.1"
        )
        
        # Create test ProjectClass
        self.project_class = ProjectClass.objects.create(
            id=uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c241"),
            name="Test Class"
        )
        
        # Create test Project
        self.project = Project.objects.create(
            id=uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042"),
            name="Test Project",
            description="Test description",
            type=self.project_type,
            phase=self.project_phase,
            category=self.project_category,
            projectClass=self.project_class,
        )

    def test_signal_updates_status_when_sap_project_set(self):
        """Test that signal updates status to project_number_opened when sapProject is set"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            status="sent_to_talpa"  # Must be locked first
        )
        
        # Set sapProject on project
        self.project.sapProject = "2814I00708"
        self.project.save(update_fields=["sapProject"])
        
        # Refresh from database
        talpa_opening.refresh_from_db()
        
        # Status should be updated
        self.assertEqual(talpa_opening.status, "project_number_opened")

    def test_signal_only_updates_if_status_is_sent_to_talpa(self):
        """Test that signal only updates if status is sent_to_talpa"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            status="excel_generated"  # Not locked
        )
        
        # Set sapProject on project
        self.project.sapProject = "2814I00708"
        self.project.save(update_fields=["sapProject"])
        
        # Refresh from database
        talpa_opening.refresh_from_db()
        
        # Status should NOT be updated (still excel_generated)
        self.assertEqual(talpa_opening.status, "excel_generated")

    def test_signal_doesnt_update_if_talpa_opening_doesnt_exist(self):
        """Test that signal doesn't update if TalpaProjectOpening doesn't exist"""
        # Don't create TalpaProjectOpening
        
        # Set sapProject on project
        self.project.sapProject = "2814I00708"
        self.project.save(update_fields=["sapProject"])
        
        # Should not raise error, just do nothing
        self.assertEqual(TalpaProjectOpening.objects.count(), 0)

    def test_signal_doesnt_update_if_sap_project_not_set(self):
        """Test that signal doesn't update if sapProject is not set"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            status="sent_to_talpa"
        )
        
        # Update project without setting sapProject
        self.project.name = "Updated Name"
        self.project.save(update_fields=["name"])
        
        # Refresh from database
        talpa_opening.refresh_from_db()
        
        # Status should NOT be updated
        self.assertEqual(talpa_opening.status, "sent_to_talpa")

    def test_signal_doesnt_update_if_sap_project_cleared(self):
        """Test that signal doesn't update if sapProject is cleared (set to None/empty)"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            status="sent_to_talpa"
        )
        
        # Set sapProject first
        self.project.sapProject = "2814I00708"
        self.project.save(update_fields=["sapProject"])
        
        # Clear sapProject
        self.project.sapProject = None
        self.project.save(update_fields=["sapProject"])
        
        # Refresh from database
        talpa_opening.refresh_from_db()
        
        # Status should remain as is (should not revert)
        # The signal only processes when sapProject is set, not when cleared
        self.assertEqual(talpa_opening.status, "project_number_opened")

    def test_signal_handles_multiple_updates(self):
        """Test that signal handles multiple updates correctly"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            status="sent_to_talpa"
        )
        
        # Set sapProject
        self.project.sapProject = "2814I00708"
        self.project.save(update_fields=["sapProject"])
        
        talpa_opening.refresh_from_db()
        self.assertEqual(talpa_opening.status, "project_number_opened")
        
        # Update sapProject again (should not change status again)
        self.project.sapProject = "2814I00709"
        self.project.save(update_fields=["sapProject"])
        
        talpa_opening.refresh_from_db()
        # Status should remain project_number_opened
        self.assertEqual(talpa_opening.status, "project_number_opened")

