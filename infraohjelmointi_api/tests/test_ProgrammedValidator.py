"""Tests for ProgrammedValidator (IO-755 completed, IO-389 suspended)."""

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from infraohjelmointi_api.models import (
    Project,
    ProjectCategory,
    ProjectClass,
    ProjectPhase,
    ProjectType,
)
from infraohjelmointi_api.validators.ProjectValidators.ProgrammedValidator import (
    ProgrammedValidator,
)


class _Stub:
    def __init__(self, instance):
        self.instance = instance


class ProgrammedValidatorTestCase(TestCase):
    def setUp(self):
        self.project_type, _ = ProjectType.objects.get_or_create(value="park")
        self.category, _ = ProjectCategory.objects.get_or_create(value="basic")
        self.project_class, _ = ProjectClass.objects.get_or_create(
            name="PV Test Class",
            defaults={"path": "PV/Test/Class"},
        )
        self.phase_programming, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.phase_proposal, _ = ProjectPhase.objects.get_or_create(value="proposal")
        self.phase_completed, _ = ProjectPhase.objects.get_or_create(value="completed")
        self.phase_suspended, _ = ProjectPhase.objects.get_or_create(value="suspended")
        self.validator = ProgrammedValidator()

    def test_programmed_false_with_suspended_phase_allowed(self):
        project = Project.objects.create(
            name="PV suspended",
            description="d",
            type=self.project_type,
            phase=self.phase_suspended,
            category=self.category,
            projectClass=self.project_class,
            programmed=False,
            planningStartYear=2024,
            constructionEndYear=2025,
        )
        fields = {"projectId": project.id, "programmed": False}
        self.validator(fields, serializer=_Stub(project))

    def test_programmed_false_with_completed_phase_allowed(self):
        project = Project.objects.create(
            name="PV completed",
            description="d",
            type=self.project_type,
            phase=self.phase_completed,
            category=self.category,
            projectClass=self.project_class,
            programmed=False,
            planningStartYear=2024,
            constructionEndYear=2025,
        )
        fields = {"projectId": project.id, "programmed": False}
        self.validator(fields, serializer=_Stub(project))

    def test_programmed_false_with_programming_phase_rejected(self):
        project = Project.objects.create(
            name="PV programming",
            description="d",
            type=self.project_type,
            phase=self.phase_programming,
            category=self.category,
            projectClass=self.project_class,
            programmed=True,
            planningStartYear=2024,
            constructionEndYear=2025,
        )
        fields = {"projectId": project.id, "programmed": False}
        with self.assertRaises(ValidationError) as ctx:
            self.validator(fields, serializer=_Stub(project))
        self.assertIn("programmed", ctx.exception.detail)

    def test_programmed_none_returns_without_error(self):
        project = Project.objects.create(
            name="PV no programmed key",
            description="d",
            type=self.project_type,
            phase=self.phase_proposal,
            category=self.category,
            projectClass=self.project_class,
            programmed=True,
            planningStartYear=2024,
            constructionEndYear=2025,
        )
        fields = {"projectId": project.id}
        self.validator(fields, serializer=_Stub(project))
