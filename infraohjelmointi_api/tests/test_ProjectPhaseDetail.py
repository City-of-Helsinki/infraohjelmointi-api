from django.test import TestCase
from rest_framework.exceptions import ValidationError

from infraohjelmointi_api.models import (
    Project,
    ProjectCategory,
    ProjectPhase,
    ProjectPhaseDetail,
    ProjectType,
)
from infraohjelmointi_api.services.ProjectPhaseDetailService import ProjectPhaseDetailService
from infraohjelmointi_api.serializers.ProjectPhaseDetailSerializer import (
    ProjectPhaseDetailSerializer,
)
from infraohjelmointi_api.validators.ProjectValidators.ProjectPhaseDetailValidator import (
    ProjectPhaseDetailValidator,
)


class _SerializerStub:
    def __init__(self, instance):
        self.instance = instance


class ProjectPhaseDetailServiceTestCase(TestCase):
    def setUp(self):
        self.phase_programming, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.phase_construction, _ = ProjectPhase.objects.get_or_create(value="construction")
        self.detail_waiting, _ = ProjectPhaseDetail.objects.get_or_create(
            value="waitingPlanningStart",
            projectPhase=self.phase_programming,
        )
        self.detail_contract, _ = ProjectPhaseDetail.objects.get_or_create(
            value="contractPreparation",
            projectPhase=self.phase_construction,
        )

    def test_list_all_returns_created_details(self):
        details = ProjectPhaseDetailService.list_all()
        self.assertGreaterEqual(details.count(), 2)
        self.assertIn(self.detail_waiting, details)
        self.assertIn(self.detail_contract, details)

    def test_get_by_id_returns_expected_detail(self):
        found = ProjectPhaseDetailService.get_by_id(str(self.detail_waiting.id))
        self.assertEqual(found.id, self.detail_waiting.id)
        self.assertEqual(found.value, "waitingPlanningStart")

    def test_find_by_value_supports_optional_phase_filter(self):
        found_without_phase = ProjectPhaseDetailService.find_by_value("contractPreparation")
        self.assertEqual(found_without_phase.id, self.detail_contract.id)

        found_with_phase = ProjectPhaseDetailService.find_by_value(
            "contractPreparation",
            phase_value="construction",
        )
        self.assertEqual(found_with_phase.id, self.detail_contract.id)

        not_found_with_wrong_phase = ProjectPhaseDetailService.find_by_value(
            "contractPreparation",
            phase_value="programming",
        )
        self.assertIsNone(not_found_with_wrong_phase)

    def test_phase_detail_serializer_includes_value_and_project_phase(self):
        data = ProjectPhaseDetailSerializer(self.detail_waiting).data
        self.assertEqual(data["value"], "waitingPlanningStart")
        self.assertEqual(data["projectPhase"]["value"], "programming")


class ProjectPhaseDetailValidatorTestCase(TestCase):
    def setUp(self):
        self.project_type, _ = ProjectType.objects.get_or_create(value="projectComplex")
        self.phase_programming, _ = ProjectPhase.objects.get_or_create(value="programming")
        self.phase_construction, _ = ProjectPhase.objects.get_or_create(value="construction")
        self.category, _ = ProjectCategory.objects.get_or_create(value="K2")

        self.programming_detail, _ = ProjectPhaseDetail.objects.get_or_create(
            value="waitingProjectManager",
            projectPhase=self.phase_programming,
        )
        self.construction_detail, _ = ProjectPhaseDetail.objects.get_or_create(
            value="contractPreparation",
            projectPhase=self.phase_construction,
        )

        self.project = Project.objects.create(
            name="Phase detail validator test",
            description="Description",
            type=self.project_type,
            phase=self.phase_programming,
            category=self.category,
            phaseDetail=self.programming_detail,
        )
        self.validator = ProjectPhaseDetailValidator()

    def test_allows_using_existing_project_phase_detail_when_not_in_payload(self):
        fields = {"projectId": self.project.id}
        serializer = _SerializerStub(instance=self.project)
        self.validator(fields, serializer=serializer)

    def test_raises_if_phase_detail_is_set_without_phase(self):
        fields = {"phaseDetail": self.programming_detail}
        serializer = _SerializerStub(instance=None)

        with self.assertRaises(ValidationError) as err:
            self.validator(fields, serializer=serializer)

        self.assertIn("phaseDetail", err.exception.detail)

    def test_raises_if_phase_detail_does_not_belong_to_selected_phase(self):
        fields = {
            "phaseDetail": self.programming_detail,
            "phase": self.phase_construction,
        }
        serializer = _SerializerStub(instance=self.project)

        with self.assertRaises(ValidationError) as err:
            self.validator(fields, serializer=serializer)

        self.assertIn("phaseDetail", err.exception.detail)

    def test_accepts_phase_detail_that_matches_selected_phase(self):
        fields = {
            "phaseDetail": self.construction_detail,
            "phase": self.phase_construction,
        }
        serializer = _SerializerStub(instance=self.project)
        self.validator(fields, serializer=serializer)

    def test_accepts_phase_detail_when_phase_omitted_uses_project_phase(self):
        """phase is resolved from the project when not in the payload (validator lines 28–30)."""
        fields = {
            "projectId": self.project.id,
            "phaseDetail": self.programming_detail,
        }
        serializer = _SerializerStub(instance=self.project)
        self.validator(fields, serializer=serializer)
