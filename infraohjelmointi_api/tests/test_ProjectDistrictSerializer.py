"""
Tests for ProjectDistrictSerializer.computedDefaultProgrammer (IO-411).

The project form's location dropdowns are backed by ``GET /project-districts/``
(``ProjectDistrictSerializer``) — *not* ``project-locations/``. So the
default-programmer preview the FE pre-fills the Ohjelmoija field with has to
travel through this serializer for the preview to actually appear before save.
The matching logic is the same as on the location side (walk parent chain,
look up programmer-view ProjectClass by name).
"""

from unittest.mock import patch

from django.test import RequestFactory, TestCase
from rest_framework.test import force_authenticate

from infraohjelmointi_api.models import (
    ProjectClass,
    ProjectDistrict,
    ProjectProgrammer,
    User,
)
from infraohjelmointi_api.serializers.ProjectDistrictSerializer import (
    ProjectDistrictSerializer,
)
from infraohjelmointi_api.views.BaseViewSet import BaseViewSet
from infraohjelmointi_api.views.ProjectDistrictViewSet import ProjectDistrictViewSet


class ProjectDistrictSerializerComputedDefaultProgrammerTestCase(TestCase):
    """
    Mirror of GetProgrammerFromLocationHierarchyTestCase but exercising the
    serializer-level field consumed by the FE form.
    """

    @classmethod
    def setUpTestData(cls):
        cls.programmer_anna = ProjectProgrammer.objects.create(
            firstName="Anna", lastName="Esimerkki"
        )
        cls.programmer_eero = ProjectProgrammer.objects.create(
            firstName="Eero", lastName="Esimerkki"
        )

        # Programmer-view suurpiiri classes (the ones that drive the lookup).
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_anna,
        )
        ProjectClass.objects.create(
            name="Läntinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_eero,
        )
        # A coordinator-only duplicate must be ignored.
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=True,
            defaultProgrammer=cls.programmer_eero,
        )

        # District tree:
        #   Itäinen suurpiiri (district)
        #     └─ 45. Vartiokylä (division)         ← matches via parent
        #         └─ Vartiokylän alaosa (subDivision) ← matches via grand-parent
        # Plus one stand-alone district that won't match anything.
        cls.district_east = ProjectDistrict.objects.create(
            name="Itäinen suurpiiri",
            level="district",
            path="Itäinen suurpiiri",
        )
        cls.division_vartiokyla = ProjectDistrict.objects.create(
            name="45. Vartiokylä",
            level="division",
            path="Itäinen suurpiiri/45. Vartiokylä",
            parent=cls.district_east,
        )
        cls.subdivision_alaosa = ProjectDistrict.objects.create(
            name="Vartiokylän alaosa",
            level="subDivision",
            path="Itäinen suurpiiri/45. Vartiokylä/Vartiokylän alaosa",
            parent=cls.division_vartiokyla,
        )

        cls.district_unmatched = ProjectDistrict.objects.create(
            name="Muu alue",
            level="district",
            path="Muu alue",
        )

    def test_direct_district_match_returns_programmer_object(self):
        data = ProjectDistrictSerializer(self.district_east).data

        self.assertIn("computedDefaultProgrammer", data)
        self.assertIsNotNone(data["computedDefaultProgrammer"])
        self.assertEqual(
            data["computedDefaultProgrammer"]["id"], str(self.programmer_anna.id)
        )
        self.assertEqual(data["computedDefaultProgrammer"]["firstName"], "Anna")
        self.assertEqual(data["computedDefaultProgrammer"]["lastName"], "Esimerkki")

    def test_walks_parent_chain_for_division(self):
        """45. Vartiokylä has no matching class — its parent (suurpiiri) does."""
        data = ProjectDistrictSerializer(self.division_vartiokyla).data
        self.assertEqual(
            data["computedDefaultProgrammer"]["id"], str(self.programmer_anna.id)
        )

    def test_walks_parent_chain_for_subdivision(self):
        """Two levels up: subDivision → division → suurpiiri."""
        data = ProjectDistrictSerializer(self.subdivision_alaosa).data
        self.assertEqual(
            data["computedDefaultProgrammer"]["id"], str(self.programmer_anna.id)
        )

    def test_no_match_returns_null(self):
        data = ProjectDistrictSerializer(self.district_unmatched).data
        self.assertIn("computedDefaultProgrammer", data)
        self.assertIsNone(data["computedDefaultProgrammer"])

    def test_ignores_coordinator_only_class(self):
        """The duplicate ``forCoordinatorOnly=True`` row points at the other
        programmer and must not be picked over the programmer-view row."""
        data = ProjectDistrictSerializer(self.district_east).data
        self.assertEqual(
            data["computedDefaultProgrammer"]["lastName"], "Esimerkki"
        )
        self.assertEqual(
            data["computedDefaultProgrammer"]["firstName"], "Anna"
        )

    def test_cycle_in_district_chain_is_logged_and_returns_null(self):
        """A corrupt district chain must not crash the serializer; the row
        falls back to ``None`` and the error is logged for ops to fix."""
        loop_a = ProjectDistrict.objects.create(
            name="LoopA", level="district", path="LoopA"
        )
        loop_b = ProjectDistrict.objects.create(
            name="LoopB", level="division", path="LoopA/LoopB", parent=loop_a
        )
        ProjectDistrict.objects.filter(pk=loop_a.pk).update(parent=loop_b)
        loop_b.refresh_from_db()

        with self.assertLogs(
            "infraohjelmointi_api.serializers.ProjectDistrictSerializer",
            level="ERROR",
        ) as cm:
            data = ProjectDistrictSerializer(loop_b).data

        self.assertIsNone(data["computedDefaultProgrammer"])
        self.assertTrue(
            any("District hierarchy error" in msg for msg in cm.output),
            f"Expected an ERROR log for the cycle, got: {cm.output}",
        )

    def test_many_serialization_builds_lookup_once(self):
        """
        Serializing N districts in one ``many=True`` pass must build the
        name→programmer lookup exactly once. Without the per-context cache
        every row would re-query ``ProjectClass`` and the form's
        ``GET /project-districts/`` would balloon to N+1 queries.
        """
        districts = [
            self.district_east,
            self.division_vartiokyla,
            self.subdivision_alaosa,
            self.district_unmatched,
        ]

        # Patch the lookup builder to count invocations while still returning
        # real data. We resolve the submodule via ``importlib.import_module``
        # on purpose: ``infraohjelmointi_api.serializers.__init__`` re-exports
        # the class with the same name as the submodule, so plain ``import
        # ... as mod`` resolves via attribute access and binds to the class
        # rather than the module. Going through ``import_module`` always
        # returns the module object that the serializer's global namespace
        # actually lives in.
        from importlib import import_module

        mod = import_module(
            "infraohjelmointi_api.serializers.ProjectDistrictSerializer"
        )
        real_builder = mod.build_location_programmer_lookup
        with patch.object(
            mod,
            "build_location_programmer_lookup",
            wraps=real_builder,
        ) as spy:
            data = ProjectDistrictSerializer(districts, many=True).data

        self.assertEqual(spy.call_count, 1)
        # And the data is still correct end-to-end:
        ids = {row["id"]: row.get("computedDefaultProgrammer") for row in data}
        self.assertIsNotNone(ids[str(self.district_east.id)])
        self.assertIsNotNone(ids[str(self.division_vartiokyla.id)])
        self.assertIsNotNone(ids[str(self.subdivision_alaosa.id)])
        self.assertIsNone(ids[str(self.district_unmatched.id)])


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectDistrictViewSetSmokeTestCase(TestCase):
    """
    Smoke test: ``GET /project-districts/`` must include
    ``computedDefaultProgrammer`` in every row so the FE has the field
    available to wire into the form.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="districts-smoke")

        cls.programmer = ProjectProgrammer.objects.create(
            firstName="Anna", lastName="Esimerkki"
        )
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer,
        )
        cls.district_east = ProjectDistrict.objects.create(
            name="Itäinen suurpiiri",
            level="district",
            path="Itäinen suurpiiri",
        )
        cls.district_unmatched = ProjectDistrict.objects.create(
            name="Tuntematon",
            level="district",
            path="Tuntematon",
        )

    def test_list_endpoint_includes_computed_default_programmer(self):
        request = RequestFactory().get("/project-districts/")
        force_authenticate(request, user=self.user)
        view = ProjectDistrictViewSet.as_view({"get": "list"})

        response = view(request)
        self.assertEqual(response.status_code, 200)

        # Ensure the serializer has fully rendered before we read .data
        response.render()
        rows = response.data
        self.assertGreaterEqual(len(rows), 2)
        for row in rows:
            self.assertIn(
                "computedDefaultProgrammer",
                row,
                msg=f"Row {row.get('name')!r} missing computedDefaultProgrammer",
            )

        by_id = {str(r["id"]): r for r in rows}
        self.assertEqual(
            by_id[str(self.district_east.id)]["computedDefaultProgrammer"]["lastName"],
            "Esimerkki",
        )
        self.assertIsNone(
            by_id[str(self.district_unmatched.id)]["computedDefaultProgrammer"]
        )
