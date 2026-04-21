"""
Tests for the project_class_utils helpers, covering both class-based and
location-based default programmer resolution (IO-411).
"""

from unittest.mock import patch

from django.test import TestCase

from infraohjelmointi_api.models import (
    ProjectClass,
    ProjectLocation,
    ProjectProgrammer,
)
from infraohjelmointi_api.utils.project_class_utils import (
    build_location_programmer_lookup,
    get_default_programmer_for_project,
    get_programmer_from_hierarchy,
    get_programmer_from_location_hierarchy,
)


class GetProgrammerFromHierarchyTestCase(TestCase):
    """Existing class-parent walker behavior."""

    @classmethod
    def setUpTestData(cls):
        cls.programmer = ProjectProgrammer.objects.create(
            firstName="Eero", lastName="Esimerkki"
        )
        cls.parent_class = ProjectClass.objects.create(
            name="8 01 Liikennejärjestelyt",
            defaultProgrammer=cls.programmer,
        )
        cls.child_class = ProjectClass.objects.create(
            name="8 01 02 Some sub class", parent=cls.parent_class
        )
        cls.orphan_class = ProjectClass.objects.create(name="Standalone")

    def test_returns_none_for_none(self):
        self.assertIsNone(get_programmer_from_hierarchy(None))

    def test_returns_direct_programmer(self):
        self.assertEqual(
            get_programmer_from_hierarchy(self.parent_class), self.programmer
        )

    def test_walks_parent_chain(self):
        self.assertEqual(
            get_programmer_from_hierarchy(self.child_class), self.programmer
        )

    def test_returns_none_when_no_default_anywhere(self):
        self.assertIsNone(get_programmer_from_hierarchy(self.orphan_class))


class GetProgrammerFromLocationHierarchyTestCase(TestCase):
    """
    Location-based fallback: matches each location name against a
    programmer-view ProjectClass with defaultProgrammer set.
    Mirrors the IO-411 prod scenario where the suurpiiri lives on
    projectLocation rather than projectClass.
    """

    @classmethod
    def setUpTestData(cls):
        cls.programmer_anna = ProjectProgrammer.objects.create(
            firstName="Anna", lastName="Esimerkki"
        )
        cls.programmer_eero = ProjectProgrammer.objects.create(
            firstName="Eero", lastName="Esimerkki"
        )

        # Programmer-view (forCoordinatorOnly=False) suurpiiri classes with
        # defaultProgrammer set, mirroring how prod data looks.
        cls.cls_east = ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_anna,
        )
        cls.cls_west = ProjectClass.objects.create(
            name="Läntinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_eero,
        )

        # A coordinator-only class with the same name should be ignored.
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=True,
            defaultProgrammer=cls.programmer_eero,
        )

        # Locations
        cls.loc_east = ProjectLocation.objects.create(name="Itäinen suurpiiri")
        cls.loc_west = ProjectLocation.objects.create(name="Läntinen suurpiiri")
        cls.loc_district = ProjectLocation.objects.create(
            name="45. Vartiokylä", parent=cls.loc_east
        )
        cls.loc_unmatched = ProjectLocation.objects.create(name="Muu alue")

    def test_returns_none_for_none(self):
        self.assertIsNone(get_programmer_from_location_hierarchy(None))

    def test_direct_location_match(self):
        self.assertEqual(
            get_programmer_from_location_hierarchy(self.loc_east),
            self.programmer_anna,
        )

    def test_walks_location_parent_chain(self):
        # Vartiokylä has no matching ProjectClass, but its parent is
        # Itäinen suurpiiri which does.
        self.assertEqual(
            get_programmer_from_location_hierarchy(self.loc_district),
            self.programmer_anna,
        )

    def test_unmatched_location_returns_none(self):
        self.assertIsNone(
            get_programmer_from_location_hierarchy(self.loc_unmatched)
        )

    def test_ignores_coordinator_only_class(self):
        # The Eastern programmer-view class points at the programmer-view
        # row; the coordinator-only duplicate must not be picked.
        self.assertEqual(
            get_programmer_from_location_hierarchy(self.loc_east),
            self.programmer_anna,
        )

    def test_cycle_detection_raises(self):
        loc_a = ProjectLocation.objects.create(name="LoopA")
        loc_b = ProjectLocation.objects.create(name="LoopB", parent=loc_a)
        # Force a cycle bypassing model validation
        ProjectLocation.objects.filter(pk=loc_a.pk).update(parent=loc_b)
        loc_b.refresh_from_db()
        with self.assertRaises(ValueError):
            get_programmer_from_location_hierarchy(loc_b)


class GetDefaultProgrammerForProjectTestCase(TestCase):
    """
    Combined resolver used by ProjectCreateSerializer and the
    programmerimporter backfill.
    """

    @classmethod
    def setUpTestData(cls):
        cls.programmer_class_owner = ProjectProgrammer.objects.create(
            firstName="Maija", lastName="Esimerkki"
        )
        cls.programmer_loc_owner = ProjectProgrammer.objects.create(
            firstName="Anna", lastName="Esimerkki"
        )

        cls.parent_class = ProjectClass.objects.create(
            name="8 03 Some thing",
            defaultProgrammer=cls.programmer_class_owner,
        )
        cls.generic_child_class = ProjectClass.objects.create(
            name="8 03 01 Liikennejärjestelyt", parent=cls.parent_class
        )
        cls.unrelated_class = ProjectClass.objects.create(name="Liikennejärjestelyt")

        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=cls.programmer_loc_owner,
        )
        cls.location_east = ProjectLocation.objects.create(name="Itäinen suurpiiri")

    def test_class_chain_wins_when_present(self):
        result = get_default_programmer_for_project(
            self.generic_child_class, self.location_east
        )
        self.assertEqual(result, self.programmer_class_owner)

    def test_falls_back_to_location_when_class_has_none(self):
        result = get_default_programmer_for_project(
            self.unrelated_class, self.location_east
        )
        self.assertEqual(result, self.programmer_loc_owner)

    def test_returns_none_when_neither_resolves(self):
        empty_loc = ProjectLocation.objects.create(name="No match")
        self.assertIsNone(
            get_default_programmer_for_project(self.unrelated_class, empty_loc)
        )

    def test_works_with_only_location(self):
        result = get_default_programmer_for_project(None, self.location_east)
        self.assertEqual(result, self.programmer_loc_owner)

    def test_works_with_only_class(self):
        result = get_default_programmer_for_project(self.parent_class, None)
        self.assertEqual(result, self.programmer_class_owner)

    def test_class_cycle_does_not_block_location_fallback(self):
        """
        A corrupted class hierarchy (cycle) must not prevent the location
        chain from being consulted. The class-side ValueError is logged and
        swallowed, then the location chain is tried.
        """
        a = ProjectClass.objects.create(name="cycle-a")
        b = ProjectClass.objects.create(name="cycle-b", parent=a)
        ProjectClass.objects.filter(pk=a.pk).update(parent=b)
        a.refresh_from_db()
        b.refresh_from_db()

        result = get_default_programmer_for_project(b, self.location_east)
        self.assertEqual(result, self.programmer_loc_owner)


class BuildLocationProgrammerLookupTestCase(TestCase):
    """
    The lookup table is the request-scoped cache that backs the location
    walker. It must:
      - ignore coordinator-only ProjectClass rows
      - ignore rows without a defaultProgrammer
      - be deterministic when multiple programmer-view classes share a name
      - emit a warning when same-named classes resolve to *different*
        programmers (data-quality alert)
    """

    @classmethod
    def setUpTestData(cls):
        cls.programmer_a = ProjectProgrammer.objects.create(firstName="A", lastName="One")
        cls.programmer_b = ProjectProgrammer.objects.create(firstName="B", lastName="Two")

    def test_excludes_coordinator_only_and_unset(self):
        ProjectClass.objects.create(
            name="Programmer view",
            forCoordinatorOnly=False,
            defaultProgrammer=self.programmer_a,
        )
        ProjectClass.objects.create(
            name="Coordinator only",
            forCoordinatorOnly=True,
            defaultProgrammer=self.programmer_b,
        )
        ProjectClass.objects.create(
            name="No programmer",
            forCoordinatorOnly=False,
            defaultProgrammer=None,
        )

        lookup = build_location_programmer_lookup()
        self.assertIn("Programmer view", lookup)
        self.assertNotIn("Coordinator only", lookup)
        self.assertNotIn("No programmer", lookup)
        self.assertEqual(lookup["Programmer view"], self.programmer_a)

    def test_duplicates_with_same_programmer_resolve_consistently(self):
        # Three programmer-view rows ("Itäinen suurpiiri" exists 3 times in
        # prod, one per project type) all pointing at the same programmer.
        for _ in range(3):
            ProjectClass.objects.create(
                name="Itäinen suurpiiri",
                forCoordinatorOnly=False,
                defaultProgrammer=self.programmer_a,
            )

        lookup = build_location_programmer_lookup()
        self.assertEqual(lookup["Itäinen suurpiiri"], self.programmer_a)

    def test_duplicates_with_conflicting_programmers_warn_and_stay_deterministic(self):
        """
        When two same-named classes point at different programmers, the
        oldest (by createdDate) wins deterministically and a warning is
        logged so the data drift can be reconciled.
        """
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=self.programmer_a,
        )
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=self.programmer_b,
        )

        with self.assertLogs("infraohjelmointi_api.utils.project_class_utils", level="WARNING") as cm:
            lookup_first = build_location_programmer_lookup()
            lookup_second = build_location_programmer_lookup()

        self.assertEqual(lookup_first["Itäinen suurpiiri"], self.programmer_a)
        self.assertEqual(lookup_second["Itäinen suurpiiri"], self.programmer_a)
        self.assertTrue(
            any("Itäinen suurpiiri" in msg for msg in cm.output),
            f"Expected a warning naming the conflicting class, got: {cm.output}",
        )

    def test_walker_uses_supplied_lookup_without_extra_queries(self):
        """
        When a precomputed lookup is supplied, the walker must not query the
        database for ProjectClass rows again (the whole point of the cache).
        """
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=self.programmer_a,
        )
        location = ProjectLocation.objects.create(name="Itäinen suurpiiri")
        precomputed = build_location_programmer_lookup()

        # Patch the model loader inside the util to make any further queries
        # explode; the walker must not touch it when name_lookup is supplied.
        with patch(
            "infraohjelmointi_api.utils.project_class_utils.build_location_programmer_lookup",
            side_effect=AssertionError("should not rebuild lookup"),
        ):
            result = get_programmer_from_location_hierarchy(
                location, name_lookup=precomputed
            )

        self.assertEqual(result, self.programmer_a)
