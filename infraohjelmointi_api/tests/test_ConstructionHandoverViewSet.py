from unittest.mock import patch
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionHandoverFinancing,
    ConstructionProcurementMethod,
    Person,
    Project,
    ProjectProgrammer,
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
            email="handover2@example.com",
        )

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

    def test_create_construction_handover(self):
        self.client.force_authenticate(user=self.user_1)
        self.project.sapProject = "SAP-123"
        self.project.costForecast = 123456
        self.project.save(update_fields=["sapProject", "costForecast"])

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
