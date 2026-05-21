from django.test import TestCase

from infraohjelmointi_api.models import ConstructionHandover, Project


class ConstructionHandoverTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover tests",
        )

    def test_handover_has_draft_status_and_history_row_after_update(self):
        handover = ConstructionHandover.objects.create(project=self.project)

        self.assertEqual(handover.status, "DRAFT")

        handover.name = "Updated handover name"
        handover.save()

        self.assertEqual(handover.history.count(), 1)
        self.assertEqual(handover.history.latest().status, "DRAFT")
