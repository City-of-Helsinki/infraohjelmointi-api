from django.test import TestCase
from infraohjelmointi_api.models import Project, ProjectPhase, ProjectCategory, ProjectType

class ProjectSignalTestCase(TestCase):
    def setUp(self):
        self.projectType, _ = ProjectType.objects.get_or_create(value="projectComplex")
        self.phase_proposal, _ = ProjectPhase.objects.get_or_create(value="proposal", defaults={"index": 1})
        self.phase_construction, _ = ProjectPhase.objects.get_or_create(value="construction", defaults={"index": 2})
        self.phase_other, _ = ProjectPhase.objects.get_or_create(value="planning", defaults={"index": 3})
        self.category_k1, _ = ProjectCategory.objects.get_or_create(value="K1")
        self.category_k2, _ = ProjectCategory.objects.get_or_create(value="K2")

    def test_project_category_updates_to_k1_when_phase_changes_to_construction(self):
        # Create project in proposal phase
        project = Project.objects.create(
            name="Test Project",
            description="Description",
            type=self.projectType,
            phase=self.phase_proposal,
            category=self.category_k2
        )

        # Verify initial state
        self.assertEqual(project.phase, self.phase_proposal)
        self.assertEqual(project.category, self.category_k2)

        # Change phase to construction
        project.phase = self.phase_construction
        project.save()

        # Refresh from db
        project.refresh_from_db()

        # Verify category changed to K1
        self.assertEqual(project.phase, self.phase_construction)
        self.assertEqual(project.category, self.category_k1)

    def test_project_category_does_not_change_if_phase_is_not_construction(self):
        # Create project in proposal phase
        project = Project.objects.create(
            name="Test Project 2",
            description="Description",
            type=self.projectType,
            phase=self.phase_proposal,
            category=self.category_k2
        )

        # Change phase to something else than construction
        project.phase = self.phase_other
        project.save()

        # Refresh from db
        project.refresh_from_db()

        # Verify category did NOT change
        self.assertEqual(project.phase, self.phase_other)
        self.assertEqual(project.category, self.category_k2)

    def test_project_created_in_construction_phase_gets_k1(self):
        # Create project directly in construction phase
        project = Project.objects.create(
            name="Test Project 3",
            description="Description",
            type=self.projectType,
            phase=self.phase_construction,
            category=self.category_k2
        )

        # Refresh from db
        project.refresh_from_db()

        # If the signal works on creation too, it should be K1.
        # For now let's assume valid behavior is K1.
        self.assertEqual(project.category, self.category_k1)

    def test_project_category_does_not_change_when_updating_other_fields(self):
        # Create project in construction phase with K1
        project = Project.objects.create(
            name="Test Project 4",
            description="Description",
            type=self.projectType,
            phase=self.phase_construction,
            category=self.category_k1
        )

        # Change name. Category should remain K1.
        project.name = "Updated Name"
        project.save()
        project.refresh_from_db()
        self.assertEqual(project.category, self.category_k1)
