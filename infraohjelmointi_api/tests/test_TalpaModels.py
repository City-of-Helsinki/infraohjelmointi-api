from datetime import date

from django.test import TestCase

from infraohjelmointi_api.models import (
    Project,
    TalpaProjectOpening,
    TalpaProjectType,
    TalpaServiceClass,
    TalpaAssetClass,
    TalpaProjectNumberRange,
    Person,
    ProjectType,
    ProjectPhase,
    ProjectCategory,
    ProjectClass,
)
import uuid


class TalpaModelsTestCase(TestCase):
    """Essential unit tests for Talpa models"""

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

    def test_talpa_project_opening_creation(self):
        """Test creating a TalpaProjectOpening"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            projectName="Test Project"
        )

        self.assertIsNotNone(talpa_opening.id)
        self.assertEqual(talpa_opening.project, self.project)
        self.assertEqual(talpa_opening.priority, "Normaali")
        self.assertEqual(talpa_opening.subject, "Uusi")
        self.assertEqual(talpa_opening.status, "excel_generated")
        self.assertEqual(talpa_opening.servicePackage, "Taloushallinnon palvelut")
        self.assertEqual(talpa_opening.service, "SAP-projektinumeron avauspyyntö")
        self.assertEqual(talpa_opening.organization, "2800 Kymp")

    def test_talpa_project_opening_is_locked_property(self):
        """Test is_locked property"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi"
        )

        # Default status should not be locked
        self.assertFalse(talpa_opening.is_locked)

        # sent_to_talpa should be locked
        talpa_opening.status = "sent_to_talpa"
        talpa_opening.save()
        self.assertTrue(talpa_opening.is_locked)

        # project_number_opened should also be locked
        talpa_opening.status = "project_number_opened"
        talpa_opening.save()
        self.assertTrue(talpa_opening.is_locked)

    def test_talpa_project_opening_default_status(self):
        """Test that default status is excel_generated"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi"
        )

        self.assertEqual(talpa_opening.status, "excel_generated")

    def test_talpa_project_type_creation(self):
        """Test creating a TalpaProjectType"""
        project_type = TalpaProjectType.objects.create(
            code="8 03 01 01",
            name="Katujen uudisrakentaminen",
            category="KADUT, LIIKENNEVÄYLÄT JA RADAT",
            priority="Normaali",
            isActive=True
        )

        self.assertIsNotNone(project_type.id)
        self.assertEqual(project_type.code, "8 03 01 01")
        self.assertEqual(project_type.name, "Katujen uudisrakentaminen")
        self.assertTrue(project_type.isActive)

    def test_talpa_project_type_unique_constraint(self):
        """Test that TalpaProjectType code + priority combination must be unique"""
        TalpaProjectType.objects.create(
            code="8 03 01 01",
            name="First",
            priority="A",
            isActive=True
        )

        # Same code with different priority should succeed
        TalpaProjectType.objects.create(
            code="8 03 01 01",
            name="Second",
            priority="B",
            isActive=True
        )

        # Same code with same priority should fail
        with self.assertRaises(Exception):  # Should raise IntegrityError
            TalpaProjectType.objects.create(
                code="8 03 01 01",
                name="Third",
                priority="A",  # Same as first
                isActive=True
            )

    def test_talpa_service_class_creation(self):
        """Test creating a TalpaServiceClass"""
        service_class = TalpaServiceClass.objects.create(
            code="4601",
            name="Kadut ja yleiset alueet",
            projectTypePrefix="2814I",
            isActive=True
        )

        self.assertIsNotNone(service_class.id)
        self.assertEqual(service_class.code, "4601")
        self.assertEqual(service_class.projectTypePrefix, "2814I")
        self.assertTrue(service_class.isActive)

    def test_talpa_service_class_unique_constraint(self):
        """Test that TalpaServiceClass code must be unique"""
        TalpaServiceClass.objects.create(
            code="4601",
            name="First",
            isActive=True
        )

        # Try to create another with same code
        with self.assertRaises(Exception):  # Should raise IntegrityError
            TalpaServiceClass.objects.create(
                code="4601",
                name="Second",
                isActive=True
            )

    def test_talpa_asset_class_creation(self):
        """Test creating a TalpaAssetClass"""
        asset_class = TalpaAssetClass.objects.create(
            componentClass="8103000",
            account="103000",
            name="Maa- ja vesialueet",
            category="Kiinteät rakenteet ja laitteet",
            holdingPeriodYears=30,
            hasHoldingPeriod=True,
            isActive=True
        )

        self.assertIsNotNone(asset_class.id)
        self.assertEqual(asset_class.componentClass, "8103000")
        self.assertEqual(asset_class.account, "103000")
        self.assertEqual(asset_class.holdingPeriodYears, 30)
        self.assertTrue(asset_class.hasHoldingPeriod)

    def test_talpa_asset_class_unique_constraint(self):
        """Test that TalpaAssetClass componentClass+account must be unique"""
        TalpaAssetClass.objects.create(
            componentClass="8103000",
            account="103000",
            name="First",
            isActive=True
        )

        # Try to create another with same componentClass and account
        with self.assertRaises(Exception):  # Should raise IntegrityError
            TalpaAssetClass.objects.create(
                componentClass="8103000",
                account="103000",
                name="Second",
                isActive=True
            )

    def test_talpa_project_number_range_creation(self):
        """Test creating a TalpaProjectNumberRange"""
        project_range = TalpaProjectNumberRange.objects.create(
            projectTypePrefix="2814I",
            budgetAccount="8 03 01 01",
            budgetAccountNumber="2814100000",
            rangeStart="2814100003",
            rangeEnd="2814100300",
            majorDistrict="01",
            majorDistrictName="Eteläinen",
            area="011 Keskusta",
            isActive=True
        )

        self.assertIsNotNone(project_range.id)
        self.assertEqual(project_range.projectTypePrefix, "2814I")
        self.assertEqual(project_range.rangeStart, "2814100003")
        self.assertEqual(project_range.rangeEnd, "2814100300")

    def test_talpa_project_number_range_make_format(self):
        """Test creating a MAKE format range (2814E)"""
        project_range = TalpaProjectNumberRange.objects.create(
            projectTypePrefix="2814E",
            budgetAccount="8 01 01 01",
            rangeStart="2814E01000",
            rangeEnd="2814E01599",
            area="011 Keskusta",
            unit="Tontit",
            contactPerson="Test Person",
            contactEmail="test@example.com",
            isActive=True
        )

        self.assertEqual(project_range.projectTypePrefix, "2814E")
        self.assertEqual(project_range.unit, "Tontit")
        self.assertIsNotNone(project_range.contactPerson)

    def test_talpa_project_opening_one_to_one_relationship(self):
        """Test that TalpaProjectOpening has OneToOne relationship with Project"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi"
        )

        # Should be able to access from project
        self.assertEqual(self.project.talpaProjectOpening, talpa_opening)

        # Should not be able to create another for same project
        with self.assertRaises(Exception):  # Should raise IntegrityError
            TalpaProjectOpening.objects.create(
                project=self.project,
                priority="Korkea",
                subject="Muutos"
            )

    def test_talpa_project_opening_foreign_key_relationships(self):
        """Test foreign key relationships"""
        project_type = TalpaProjectType.objects.create(
            code="8 03 01 01",
            name="Test Type",
            isActive=True
        )

        service_class = TalpaServiceClass.objects.create(
            code="4601",
            name="Test Service",
            isActive=True
        )

        asset_class = TalpaAssetClass.objects.create(
            componentClass="8103000",
            account="103000",
            name="Test Asset",
            isActive=True
        )

        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            projectType=project_type,
            serviceClass=service_class,
            assetClass=asset_class
        )

        self.assertEqual(talpa_opening.projectType, project_type)
        self.assertEqual(talpa_opening.serviceClass, service_class)
        self.assertEqual(talpa_opening.assetClass, asset_class)

    def test_talpa_project_opening_string_representation(self):
        """Test string representation of TalpaProjectOpening"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi"
        )

        str_repr = str(talpa_opening)
        self.assertIn("Test Project", str_repr)
        self.assertIn("excel_generated", str_repr)

    def test_talpa_project_opening_new_address_fields(self):
        """Test new address fields (streetAddress, postalCode)"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            streetAddress="Testikatu 1",
            postalCode="00100"
        )

        self.assertEqual(talpa_opening.streetAddress, "Testikatu 1")
        self.assertEqual(talpa_opening.postalCode, "00100")

    def test_talpa_project_opening_new_schedule_fields(self):
        """Test new schedule fields (projectStartDate, projectEndDate)"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            projectStartDate=date(2025, 1, 1),
            projectEndDate=date(2030, 12, 31)
        )

        self.assertEqual(talpa_opening.projectStartDate, date(2025, 1, 1))
        self.assertEqual(talpa_opening.projectEndDate, date(2030, 12, 31))

    def test_talpa_project_opening_readiness_field(self):
        """Test readiness field with valid choices"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            readiness="Kesken"
        )

        self.assertEqual(talpa_opening.readiness, "Kesken")

    def test_talpa_project_opening_unit_choices(self):
        """Test unit field with valid choices for 2814E projects"""
        for unit_value in ["Tontit", "Mao", "Geo"]:
            talpa_opening = TalpaProjectOpening.objects.create(
                project=Project.objects.create(
                    name=f"Test Project {unit_value}",
                    description="Test",
                    type=self.project_type,
                    phase=self.project_phase,
                    category=self.project_category,
                    projectClass=self.project_class,
                ),
                priority="Normaali",
                subject="Uusi",
                unit=unit_value
            )
            self.assertEqual(talpa_opening.unit, unit_value)

    def test_talpa_project_opening_project_name_max_length(self):
        """Test projectName max length is 24 characters"""
        talpa_opening = TalpaProjectOpening.objects.create(
            project=self.project,
            priority="Normaali",
            subject="Uusi",
            projectName="123456789012345678901234"
        )
        self.assertEqual(len(talpa_opening.projectName), 24)

