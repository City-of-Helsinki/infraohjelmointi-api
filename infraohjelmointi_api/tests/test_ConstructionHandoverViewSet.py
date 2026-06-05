from unittest.mock import patch
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from helusers.models import ADGroup

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionHandoverFinancing,
    ConstructionProcurementMethod,
    Person,
    Project,
    ProjectPhase,
    ProjectProgrammer,
    ProjectTypeQualifier,
)
from infraohjelmointi_api.serializers import (
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverGetSerializer,
    ConstructionHandoverUpdateSerializer,
)
from infraohjelmointi_api.views.BaseViewSet import BaseViewSet
from infraohjelmointi_api.views.ConstructionHandoverViewSet import ConstructionHandoverViewSet

User = get_user_model()


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ConstructionHandoverViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.person_planning = Person.objects.create(
            firstName="Planning",
            lastName="Person",
            email="planning@example.com",
            title="Planner",
            phone="0100000000",
        )
        self.person_construction = Person.objects.create(
            firstName="Construction",
            lastName="Manager",
            email="construction@example.com",
            title="Construction Manager",
            phone="0200000000",
        )
        self.project_programmer = ProjectProgrammer.objects.create(
            firstName="Program",
            lastName="Manager",
        )
        self.construction_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Kilpailutus",
        )
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover view set tests",
            estConstructionStart=date(2026, 1, 2),
            estConstructionEnd=date(2026, 3, 4),
            personPlanning=self.person_planning,
            personProgramming=self.project_programmer,
            personConstruction=self.person_construction,
            constructionProcurementMethod=self.construction_procurement_method,
        )
        self.user_1 = User.objects.create(
            username="handover_user_1",
            first_name="Handover",
            last_name="User One",
            email="handover1@example.com",
        )
        self.user_2 = User.objects.create(
            username="handover_user_2",
            first_name="Handover",
            last_name="User Two",
            email=self.person_planning.email,
        )
        self.user_3 = User.objects.create(
            username="handover_user_3",
            first_name="Handover",
            last_name="User Three",
            email=self.person_construction.email,
        )
        self.project_manager_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_projektipaallikot",
            display_name="Project Managers",
        )
        self.programmer_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_ohjelmoijat",
            display_name="Programmers",
        )
        self.construction_management_lead_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_rakennuttamisen_esihenkilot",
            display_name="Construction Management Leads",
        )
        self.user_2.ad_groups.add(self.project_manager_group)
        self.user_3.ad_groups.add(self.project_manager_group)

        self.user_4 = User.objects.create(
            username="handover_user_4",
            first_name="Handover",
            last_name="User Four",
            email="handover4@example.com",
        )
        self.user_4.ad_groups.add(self.programmer_group)

        self.user_5 = User.objects.create(
            username="handover_user_6",
            first_name="Handover",
            last_name="User Six",
            email="handover6@example.com",
        )
        self.user_5.ad_groups.add(self.construction_management_lead_group)

    def test_get_serializer_class_by_action(self):
        viewset = ConstructionHandoverViewSet()

        viewset.action = "list"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverGetSerializer)

        viewset.action = "retrieve"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverGetSerializer)

        viewset.action = "create"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverCreateSerializer)

        viewset.action = "update"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverUpdateSerializer)

        viewset.action = "partial_update"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverUpdateSerializer)

    def test_get_construction_handover_by_id(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Test handover",
        )

        response = self.client.get(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(handover.id))
        self.assertEqual(response.data["name"], "Test handover")
        self.assertEqual(response.data["status"], "DRAFT")

    def test_get_construction_handover_includes_financing_rows(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Test handover",
        )
        budget_item = ProjectTypeQualifier.objects.create(value="K1")
        ConstructionHandoverFinancing.objects.create(
            handover=handover,
            financingParty="KYMP",
            budgetItem=budget_item,
            projectNumber="HEL-2024-001",
            budget=Decimal("150000.00"),
        )
        ConstructionHandoverFinancing.objects.create(
            handover=handover,
            financingParty="OTHER",
            description="Other financing source",
            projectNumber="",
            budget=Decimal("50000.00"),
        )

        response = self.client.get(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["constructionHandoverFinancing"]), 2)

        financing_by_party = {
            item["financingParty"]: item for item in response.data["constructionHandoverFinancing"]
        }

        kymp_financing = financing_by_party["KYMP"]
        self.assertEqual(kymp_financing["financingParty"], "KYMP")
        self.assertEqual(kymp_financing["projectNumber"], "HEL-2024-001")
        self.assertEqual(str(kymp_financing["budget"]), "150000.00")
        self.assertIsNotNone(kymp_financing["budgetItem"])

        other_financing = financing_by_party["OTHER"]
        self.assertEqual(other_financing["financingParty"], "OTHER")
        self.assertEqual(other_financing["description"], "Other financing source")
        self.assertEqual(str(other_financing["budget"]), "50000.00")

    def test_create_construction_handover(self):
        self.client.force_authenticate(user=self.user_1)
        type_qualifier = ProjectTypeQualifier.objects.create(value="K1")
        self.project.typeQualifier = type_qualifier
        self.project.sapProject = "SAP-123"
        self.project.costForecast = 123456
        self.project.save(update_fields=["typeQualifier", "sapProject", "costForecast"])

        response = self.client.post(
            "/construction-handovers/",
            {"project": str(self.project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        handover = ConstructionHandover.objects.get(id=response.data["id"])
        self.assertEqual(handover.createdBy_id, self.user_1.uuid)
        self.assertEqual(handover.updatedBy_id, self.user_1.uuid)
        self.assertEqual(handover.name, self.project.name)
        self.assertEqual(handover.description, self.project.description)
        self.assertEqual(handover.constructionStart, self.project.estConstructionStart)
        self.assertEqual(handover.constructionEnd, self.project.estConstructionEnd)
        self.assertEqual(handover.personPlanning, self.project.personPlanning)
        self.assertEqual(handover.personFinancing, self.project.personProgramming)
        self.assertEqual(
            handover.constructionProcurementMethod,
            self.project.constructionProcurementMethod,
        )
        self.assertEqual(
            handover.constructionProjectManager,
            self.project.personConstruction,
        )

        financing_rows = ConstructionHandoverFinancing.objects.filter(handover=handover)
        self.assertEqual(financing_rows.count(), 1)

        financing_row = financing_rows.first()
        self.assertEqual(financing_row.financingParty, "KYMP")
        self.assertEqual(financing_row.budgetItem_id, type_qualifier.id)
        self.assertEqual(financing_row.projectNumber, self.project.sapProject)
        self.assertEqual(financing_row.budget, self.project.costForecast)

    def test_create_construction_handover_sets_null_project_manager_when_project_person_construction_is_null(self):
        self.client.force_authenticate(user=self.user_1)

        self.project.personConstruction = None
        self.project.save(update_fields=["personConstruction"])

        response = self.client.post(
            "/construction-handovers/",
            {"project": str(self.project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        handover = ConstructionHandover.objects.get(id=response.data["id"])
        self.assertIsNone(handover.constructionProjectManager)

    def test_project_updates_do_not_update_existing_handover(self):
        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            "/construction-handovers/",
            {"project": str(self.project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        handover = ConstructionHandover.objects.get(id=response.data["id"])

        original_name = handover.name
        original_description = handover.description
        original_construction_start = handover.constructionStart
        original_construction_end = handover.constructionEnd
        original_person_planning_id = handover.personPlanning_id
        original_person_financing_id = handover.personFinancing_id
        original_procurement_method_id = handover.constructionProcurementMethod_id
        original_project_manager_id = handover.constructionProjectManager_id

        updated_planning_person = Person.objects.create(
            firstName="Updated",
            lastName="Planner",
            email="updated-planning@example.com",
            title="Updated Planner",
            phone="0300000000",
        )
        updated_project_manager = Person.objects.create(
            firstName="Updated",
            lastName="Construction Manager",
            email="updated-construction@example.com",
            title="Updated Construction Manager",
            phone="0400000000",
        )
        updated_programmer = ProjectProgrammer.objects.create(
            firstName="Updated",
            lastName="Programmer",
        )
        updated_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Yhteistoiminnalliset",
        )

        self.project.name = "Updated project name"
        self.project.description = "Updated project description"
        self.project.estConstructionStart = date(2027, 5, 6)
        self.project.estConstructionEnd = date(2027, 8, 9)
        self.project.personPlanning = updated_planning_person
        self.project.personProgramming = updated_programmer
        self.project.constructionProcurementMethod = updated_procurement_method
        self.project.personConstruction = updated_project_manager
        self.project.save()

        handover.refresh_from_db()

        self.assertEqual(handover.name, original_name)
        self.assertEqual(handover.description, original_description)
        self.assertEqual(handover.constructionStart, original_construction_start)
        self.assertEqual(handover.constructionEnd, original_construction_end)
        self.assertEqual(handover.personPlanning_id, original_person_planning_id)
        self.assertEqual(handover.personFinancing_id, original_person_financing_id)
        self.assertEqual(
            handover.constructionProcurementMethod_id,
            original_procurement_method_id,
        )
        self.assertEqual(
            handover.constructionProjectManager_id,
            original_project_manager_id,
        )

        patch_response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"otherTimelineNotes": "Updated from handover"},
            format="json",
        )

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        handover.refresh_from_db()

        self.assertEqual(handover.otherTimelineNotes, "Updated from handover")
        self.assertEqual(handover.name, original_name)
        self.assertEqual(handover.description, original_description)
        self.assertEqual(handover.constructionStart, original_construction_start)
        self.assertEqual(handover.constructionEnd, original_construction_end)
        self.assertEqual(handover.personPlanning_id, original_person_planning_id)
        self.assertEqual(handover.personFinancing_id, original_person_financing_id)
        self.assertEqual(
            handover.constructionProcurementMethod_id,
            original_procurement_method_id,
        )
        self.assertEqual(
            handover.constructionProjectManager_id,
            original_project_manager_id,
        )

    def test_create_returns_409_when_active_handover_exists(self):
        ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Existing handover",
        )

        response = self.client.post(
            "/construction-handovers/",
            {"project": str(self.project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "An active construction handover already exists for this project.",
        )
        self.assertEqual(
            ConstructionHandover.objects.filter(project=self.project).count(),
            1,
        )

    def test_partial_update_returns_409_for_non_draft(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
            name="Before update",
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"name": "After update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be edited.",
        )

        handover.refresh_from_db()
        self.assertEqual(handover.name, "Before update")

    def test_partial_update_allows_draft(self):
        self.client.force_authenticate(user=self.user_2)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Before update",
            createdBy=self.user_1,
            updatedBy=self.user_1,
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"name": "After update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.assertEqual(handover.name, "After update")
        self.assertEqual(handover.createdBy_id, self.user_1.uuid)
        self.assertEqual(handover.updatedBy_id, self.user_2.uuid)

    def test_destroy_returns_409_for_non_draft(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        response = self.client.delete(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be deleted.",
        )
        self.assertTrue(ConstructionHandover.objects.filter(id=handover.id).exists())

    def test_destroy_allows_draft(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
        )

        response = self.client.delete(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ConstructionHandover.objects.filter(id=handover.id).exists())

    def test_transitions_allows_submitted_to_programmer_for_project_manager(self):
        self.client.force_authenticate(user=self.user_2)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            updatedBy=self.user_1,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "SUBMITTED_TO_PROGRAMMER"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currentStatus"], "SUBMITTED_TO_PROGRAMMER")
        self.assertEqual(response.data["possibleTransitions"], ["SUBMITTED_TO_CONSTRUCTION"])

        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_PROGRAMMER")
        self.assertEqual(handover.updatedBy_id, self.user_2.uuid)

    def test_transitions_denies_submitted_to_programmer_for_non_project_manager(self):
        self.client.force_authenticate(user=self.user_1)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "SUBMITTED_TO_PROGRAMMER"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        handover.refresh_from_db()
        self.assertEqual(handover.status, "DRAFT")

    def test_transitions_allows_submitted_to_construction_for_programmer(self):
        self.client.force_authenticate(user=self.user_4)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "SUBMITTED_TO_CONSTRUCTION"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_CONSTRUCTION")
        self.assertEqual(self.project.phase_id, construction_phase.id)

    def test_transitions_denies_submitted_to_construction_for_non_programmer(self):
        self.client.force_authenticate(user=self.user_1)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "SUBMITTED_TO_CONSTRUCTION"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_PROGRAMMER")

    def test_transitions_allows_project_manager_named_for_construction_management_lead(self):
        self.client.force_authenticate(user=self.user_5)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_CONSTRUCTION",
            constructionProjectManager=self.person_construction,
            constructionProcurementMethod=self.construction_procurement_method,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "PROJECT_MANAGER_NAMED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(handover.status, "PROJECT_MANAGER_NAMED")
        self.assertEqual(self.project.personConstruction_id, self.person_construction.id)
        self.assertEqual(
            self.project.constructionProcurementMethod_id,
            self.construction_procurement_method.id,
        )

    def test_transitions_denies_project_manager_named_for_non_construction_management_lead(self):
        self.client.force_authenticate(user=self.user_1)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_CONSTRUCTION",
            constructionProjectManager=self.person_construction,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "PROJECT_MANAGER_NAMED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_CONSTRUCTION")

    def test_transitions_denies_project_manager_named_when_construction_project_manager_missing(self):
        self.client.force_authenticate(user=self.user_5)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_CONSTRUCTION",
            constructionProjectManager=None,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "PROJECT_MANAGER_NAMED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "constructionProjectManager is required for this transition.",
        )

        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_CONSTRUCTION")

    def test_transitions_allows_moved_to_construction_preparation_for_matching_project_manager(self):
        self.client.force_authenticate(user=self.user_3)
        proposal_phase, _ = ProjectPhase.objects.get_or_create(value="proposal")
        construction_preparation_phase, _ = ProjectPhase.objects.get_or_create(
            value="constructionPreparation"
        )
        self.project.phase = proposal_phase
        self.project.save(update_fields=["phase"])

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="PROJECT_MANAGER_NAMED",
            constructionProcurementMethod=self.construction_procurement_method,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "MOVED_TO_CONSTRUCTION_PREPARATION"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(handover.status, "MOVED_TO_CONSTRUCTION_PREPARATION")
        self.assertEqual(self.project.phase_id, construction_preparation_phase.id)

    def test_transitions_denies_moved_to_construction_preparation_for_non_matching_project_manager(self):
        self.client.force_authenticate(user=self.user_2)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="PROJECT_MANAGER_NAMED",
            constructionProcurementMethod=self.construction_procurement_method,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "MOVED_TO_CONSTRUCTION_PREPARATION"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        handover.refresh_from_db()
        self.assertEqual(handover.status, "PROJECT_MANAGER_NAMED")

    def test_transitions_returns_400_when_target_status_missing(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Field 'to' is required.")
        self.assertEqual(response.data["currentStatus"], "DRAFT")
        self.assertEqual(response.data["possibleTransitions"], ["SUBMITTED_TO_PROGRAMMER"])

    def test_transitions_rejects_skipping_status(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            constructionProjectManager=self.person_construction,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "SUBMITTED_TO_CONSTRUCTION"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "Invalid status transition.")
        self.assertEqual(response.data["possibleTransitions"], ["SUBMITTED_TO_PROGRAMMER"])

        handover.refresh_from_db()
        self.assertEqual(handover.status, "DRAFT")

    def test_transitions_rejects_unknown_status(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            constructionProjectManager=self.person_construction,
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "INVALID_STATUS"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid status 'INVALID_STATUS'.")

    def test_partial_update_auto_transitions_to_project_manager_named_when_trigger_fields_are_updated(self):
        self.client.force_authenticate(user=self.user_5)

        updated_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Yhteistoiminnalliset",
        )

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_CONSTRUCTION",
            constructionProjectManager=self.person_construction,
            constructionProcurementMethod=self.construction_procurement_method,
        )
        self.project.personConstruction = self.person_construction
        self.project.constructionProcurementMethod = self.construction_procurement_method
        self.project.save(update_fields=["personConstruction", "constructionProcurementMethod"])

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {
                "constructionProjectManager": str(self.person_planning.id),
                "constructionProcurementMethod": str(updated_procurement_method.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        handover.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(handover.status, "PROJECT_MANAGER_NAMED")
        self.assertEqual(handover.constructionProjectManager_id, self.person_planning.id)

    def test_partial_update_does_not_auto_transition_to_project_manager_named_when_only_procurement_method_is_updated(self):
        self.client.force_authenticate(user=self.user_5)

        updated_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Yhteistoiminnalliset",
        )
        self.assertEqual(self.project.personConstruction_id, self.person_planning.id)
        self.assertEqual(
            self.project.constructionProcurementMethod_id,
            updated_procurement_method.id,
        )

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_CONSTRUCTION",
            constructionProjectManager=self.person_construction,
            constructionProcurementMethod=self.construction_procurement_method,
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {
                "constructionProcurementMethod": str(updated_procurement_method.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be edited.",
        )

        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_CONSTRUCTION")
        self.assertEqual(
            handover.constructionProcurementMethod_id,
            self.construction_procurement_method.id,
        )

    def test_partial_update_auto_transition_returns_403_for_non_construction_management_lead(self):
        self.client.force_authenticate(user=self.user_1)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_CONSTRUCTION",
            constructionProjectManager=self.person_construction,
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"constructionProjectManager": str(self.person_planning.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_CONSTRUCTION")
        self.assertEqual(handover.constructionProjectManager_id, self.person_construction.id)

    def test_partial_update_auto_transitions_to_moved_to_construction_preparation_when_only_procurement_method_is_updated(self):
        self.client.force_authenticate(user=self.user_3)
        proposal_phase, _ = ProjectPhase.objects.get_or_create(value="proposal")
        construction_preparation_phase, _ = ProjectPhase.objects.get_or_create(
            value="constructionPreparation"
        )
        self.project.phase = proposal_phase
        self.project.save(update_fields=["phase"])

        updated_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Kilpailutus",
        )

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="PROJECT_MANAGER_NAMED",
            constructionProcurementMethod=self.construction_procurement_method,
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"constructionProcurementMethod": str(updated_procurement_method.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        handover.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(handover.status, "MOVED_TO_CONSTRUCTION_PREPARATION")
        self.assertEqual(
            handover.constructionProcurementMethod_id,
            updated_procurement_method.id,
        )
        self.assertEqual(self.project.phase_id, construction_preparation_phase.id)

    @patch("infraohjelmointi_api.views.ConstructionHandoverViewSet.IsPlanner.user_in_planner_group", return_value=True)
    def test_transitions_submitted_to_construction_succeeds_when_phase_row_is_missing(self, _mock_is_programmer):
        self.client.force_authenticate(user=self.user_1)
        proposal_phase, _ = ProjectPhase.objects.get_or_create(value="proposal")
        self.project.phase = proposal_phase
        self.project.save(update_fields=["phase"])
        ProjectPhase.objects.filter(value="construction").delete()

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        response = self.client.post(
            f"/construction-handovers/{handover.id}/transitions/",
            {"to": "SUBMITTED_TO_CONSTRUCTION"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_CONSTRUCTION")
        self.assertEqual(self.project.phase_id, proposal_phase.id)

    @patch("infraohjelmointi_api.views.ConstructionHandoverViewSet.IsPlanner.user_in_planner_group", return_value=True)
    @patch(
        "infraohjelmointi_api.views.ConstructionHandoverViewSet.ConstructionHandoverViewSet._sync_project_fields_for_transition",
        side_effect=RuntimeError("forced sync failure"),
    )
    def test_transitions_manual_status_rollback_when_project_sync_fails(
        self,
        _mock_sync,
        _mock_is_programmer,
    ):
        self.client.force_authenticate(user=self.user_1)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        with self.assertRaises(RuntimeError):
            self.client.post(
                f"/construction-handovers/{handover.id}/transitions/",
                {"to": "SUBMITTED_TO_CONSTRUCTION"},
                format="json",
            )

        handover.refresh_from_db()
        self.assertEqual(handover.status, "SUBMITTED_TO_PROGRAMMER")

    def test_partial_update_does_not_auto_transition_to_moved_to_construction_preparation_when_extra_fields_are_present(self):
        self.client.force_authenticate(user=self.user_3)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="PROJECT_MANAGER_NAMED",
            constructionProcurementMethod=self.construction_procurement_method,
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {
                "constructionProcurementMethod": str(self.construction_procurement_method.id),
                "otherTimelineNotes": "extra update",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be edited.",
        )

        handover.refresh_from_db()
        self.assertEqual(handover.status, "PROJECT_MANAGER_NAMED")

    def test_partial_update_saves_total_cost(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Test handover",
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"totalCost": "50000.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.assertEqual(handover.totalCost, Decimal("50000.00"))

    def test_partial_update_saves_total_cost_as_integer(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Test handover",
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"totalCost": 75000},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.assertEqual(handover.totalCost, Decimal("75000"))

    def test_partial_update_clears_total_cost(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Test handover",
            totalCost=Decimal("100000.00"),
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"totalCost": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.assertIsNone(handover.totalCost)
