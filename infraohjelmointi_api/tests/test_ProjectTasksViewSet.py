from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from infraohjelmointi_api.models import ConstructionHandover, ConstructionProcurementMethod, Project
from infraohjelmointi_api.serializers.ProjectTaskSerializer import TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER
from infraohjelmointi_api.views.ProjectTasksViewSet import ProjectTasksViewSet


@patch.object(ProjectTasksViewSet, "authentication_classes", new=[])
@patch.object(ProjectTasksViewSet, "permission_classes", new=[])
class ProjectTasksViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.procurement_method = ConstructionProcurementMethod.objects.create(
            value="Kilpailutus"
        )

        self.submitted_project = Project.objects.create(
            name="Submitted project",
            description="Included in project tasks",
            estPlanningStart=date(2026, 1, 10),
            estPlanningEnd=date(2026, 3, 31),
            estConstructionStart=date(2026, 6, 1),
            estConstructionEnd=date(2026, 12, 31),
            budget=150000,
            constructionProcurementMethod=self.procurement_method,
        )
        self.non_submitted_project = Project.objects.create(
            name="Draft handover project",
            description="Not included in project tasks",
        )
        self.no_handover_project = Project.objects.create(
            name="No handover project",
            description="Not included in project tasks",
        )

        ConstructionHandover.objects.create(
            project=self.submitted_project,
            status="SUBMITTED_TO_CONSTRUCTION",
            name="Submitted handover",
        )
        ConstructionHandover.objects.create(
            project=self.non_submitted_project,
            status="DRAFT",
            name="Draft handover",
        )

    @patch.object(ProjectTasksViewSet, "_is_construction_management_lead", return_value=True)
    def test_list_returns_submitted_to_construction_projects_for_lead(self, _mock_is_lead):
        response = self.client.get("/project-tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        item = response.data[0]
        self.assertEqual(item["id"], str(self.submitted_project.id))
        self.assertEqual(item["name"], self.submitted_project.name)
        self.assertEqual(item["taskType"], TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER)
        self.assertEqual(item["budget"], self.submitted_project.budget)
        self.assertEqual(
            item["constructionProcurementMethod"]["id"],
            str(self.procurement_method.id),
        )

    @patch.object(ProjectTasksViewSet, "_is_construction_management_lead", return_value=False)
    def test_list_returns_empty_for_non_lead(self, _mock_is_lead):
        response = self.client.get("/project-tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])