"""/projects/ and /projects/coordinator/ pick the page's ids first and load the
rows by id (ProjectViewSet.get_projects); order and pagination must not change."""

import uuid
from datetime import date
from unittest.mock import patch

from django.test import TestCase

from infraohjelmointi_api.models import Project, ProjectClass, ProjectFinancial
from infraohjelmointi_api.views import BaseViewSet


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectListPagesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.year = date.today().year
        cls.planning_class = ProjectClass.objects.create(name="8 01 Pages", path="8 01 Pages")
        cls.coordinator_class = ProjectClass.objects.create(
            name="8 01 K Pages", path="8 01 K Pages",
            forCoordinatorOnly=True, relatedTo=cls.planning_class,
        )
        cls.projects = [
            Project.objects.create(
                id=uuid.uuid4(), name=f"Project {i}", description="pages",
                programmed=True, projectClass=cls.planning_class,
            )
            for i in range(5)
        ]
        Project.objects.create(
            name="Not programmed", description="pages", projectClass=cls.planning_class,
        )
        for project in cls.projects:
            ProjectFinancial.objects.create(project=project, year=cls.year, value=10)
        # Model ordering is -id; UUIDs sort as strings in the response.
        cls.expected_ids = sorted((str(p.id) for p in cls.projects), reverse=True)

    def params(self, **extra):
        query = {"year": self.year, "direct": "false", "programmed": "true", "forcedToFrame": "false"}
        query.update(extra)
        return "&".join(f"{k}={v}" for k, v in query.items())

    def test_all_rows_come_back_in_id_order(self):
        for url in (
            f"/projects/?masterClass={self.planning_class.id}&{self.params()}",
            f"/projects/coordinator/?masterClass={self.coordinator_class.id}&{self.params()}",
        ):
            with self.subTest(url=url):
                body = self.client.get(url).json()
                self.assertEqual([r["id"] for r in body["results"]], self.expected_ids)
                self.assertEqual(body["count"], 5)

    def test_a_middle_page_keeps_order_and_envelope(self):
        body = self.client.get(
            f"/projects/?masterClass={self.planning_class.id}&{self.params(limit=2, page=2)}"
        ).json()

        self.assertEqual([r["id"] for r in body["results"]], self.expected_ids[2:4])
        self.assertEqual(body["count"], 5)
        self.assertIn("page=3", body["next"])
        self.assertIsNotNone(body["previous"])

    def test_rows_carry_their_finances_and_relations(self):
        body = self.client.get(f"/projects/?masterClass={self.planning_class.id}&{self.params()}").json()
        row = body["results"][0]

        self.assertEqual(row["finances"]["budgetProposalCurrentYearPlus0"], "10.00")
        self.assertEqual(row["projectClass"], str(self.planning_class.id))
