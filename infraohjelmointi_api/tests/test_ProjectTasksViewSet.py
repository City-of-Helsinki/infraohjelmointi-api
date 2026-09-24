from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionHandoverFinancing,
    ConstructionProcurementMethod,
    FinancingParty,
    Project,
)
from infraohjelmointi_api.serializers.ProjectTaskSerializer import TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER
from infraohjelmointi_api.views.ProjectTasksViewSet import ProjectTasksViewSet


@patch.object(ProjectTasksViewSet, "authentication_classes", new=[])
@patch.object(ProjectTasksViewSet, "permission_classes", new=[])
class ProjectTasksViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Kilpailutus"
        )
        self.handover_procurement_method = ConstructionProcurementMethod.objects.create(
            value="Puite"
        )

        self.submitted_project = Project.objects.create(
            name="Submitted project",
            description="Included in project tasks",
            estPlanningStart=date(2026, 1, 10),
            estPlanningEnd=date(2026, 3, 31),
            estConstructionStart=date(2026, 6, 1),
            estConstructionEnd=date(2026, 12, 31),
            costForecast=150000,
            constructionProcurementMethod=self.project_procurement_method,
        )
        self.non_submitted_project = Project.objects.create(
            name="Draft handover project",
            description="Not included in project tasks",
        )
        self.no_handover_project = Project.objects.create(
            name="No handover project",
            description="Not included in project tasks",
        )

        submitted_handover = ConstructionHandover.objects.create(
            project=self.submitted_project,
            status="SUBMITTED_TO_CONSTRUCTION",
            name="Submitted handover",
            constructionProcurementMethod=self.handover_procurement_method,
        )
        ConstructionHandover.objects.create(
            project=self.non_submitted_project,
            status="DRAFT",
            name="Draft handover",
        )

        ConstructionHandoverFinancing.objects.create(
            handover=submitted_handover,
            financingParty=FinancingParty.KYMP,
            budget=Decimal("100000.00"),
        )
        ConstructionHandoverFinancing.objects.create(
            handover=submitted_handover,
            financingParty=FinancingParty.KYMP,
            budget=Decimal("50000.00"),
        )
        ConstructionHandoverFinancing.objects.create(
            handover=submitted_handover,
            financingParty=FinancingParty.OTHER,
            budget=Decimal("999999.00"),
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
        self.assertEqual(item["costForecast"], self.submitted_project.costForecast)
        self.assertEqual(
            item["constructionProcurementMethod"]["id"],
            str(self.handover_procurement_method.id),
        )
        self.assertEqual(Decimal(item["budget"]), Decimal("150000.00"))

    @patch.object(ProjectTasksViewSet, "_is_construction_management_lead", return_value=False)
    def test_list_returns_empty_for_non_lead(self, _mock_is_lead):
        response = self.client.get("/project-tasks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])