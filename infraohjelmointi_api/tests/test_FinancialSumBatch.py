"""
The list serializers compute ``finances`` in one batch
(``FinancialSumBatchService``) and resolve class hierarchy walks from an
in-memory tree; a single instance still goes through the per-row code. Both
must return the same payload.

The fixture is a seeded random hierarchy with the awkward cases the relation
filters care about: sibling paths sharing a prefix (IO-928), suurpiiri classes,
coordinator twins, 3-level locations, groups in another location branch or
with no location, unprogrammed projects and frame-view finances.
"""

import random
from unittest.mock import patch
from datetime import date

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from infraohjelmointi_api.models import (
    ClassFinancial,
    LocationFinancial,
    Project,
    ProjectClass,
    ProjectFinancial,
    ProjectGroup,
    ProjectLocation,
    ProjectProgrammer,
)
from infraohjelmointi_api.serializers.FinancialSumSerializer import PRECOMPUTED_SUMS_KEY
from infraohjelmointi_api.serializers.ProjectClassSerializer import ProjectClassSerializer
from infraohjelmointi_api.serializers.ProjectGroupSerializer import ProjectGroupSerializer
from infraohjelmointi_api.serializers.ProjectLocationSerializer import ProjectLocationSerializer
from infraohjelmointi_api.tests.helpers import CacheClearingMixin
from infraohjelmointi_api.views import BaseViewSet


class FinancialSumBatchEquivalenceTestCase(CacheClearingMixin, TestCase):
    year = date.today().year

    @classmethod
    def setUpTestData(cls):
        rng = random.Random(1234)

        programmers = [
            ProjectProgrammer.objects.create(firstName=f"First{i}", lastName=f"Last{i}")
            for i in range(3)
        ]

        def make_class(name, parent=None, coordinator=False, related_to=None):
            path = f"{parent.path}/{name}" if parent else name
            return ProjectClass.objects.create(
                name=name, parent=parent, path=path,
                forCoordinatorOnly=coordinator, relatedTo=related_to,
                defaultProgrammer=rng.choice(programmers + [None, None]),
            )

        # Planning classes, including a sibling whose path extends "Malmi".
        master = make_class("8 01 Master")
        classes = [master]
        for class_name in ["Malmi", "Malminkartano", "Keskinen suurpiiri"]:
            child = make_class(class_name, master)
            classes.append(child)
            for sub in range(2):
                classes.append(make_class(f"{class_name} sub {sub}", child))
        orphan = make_class("8 02 No coordinator")
        classes.append(orphan)

        # Coordinator twins for most of them, mirroring the planning tree.
        coordinators = {}
        for planning in classes:
            if planning is orphan or rng.random() < 0.2:
                continue
            parent = coordinators.get(planning.parent_id)
            numbering = f"8 0{rng.randint(1, 3)} {rng.randint(1, 9):02d}"
            coordinators[planning.id] = make_class(
                f"{numbering} K {planning.name}", parent, coordinator=True, related_to=planning
            )

        # Locations: district -> division -> subdivision, plus coordinator districts.
        def make_location(name, parent=None, coordinator=False, related_to=None, parent_class=None):
            return ProjectLocation.objects.create(
                name=name, parent=parent, path=name, forCoordinatorOnly=coordinator,
                relatedTo=related_to, parentClass=parent_class,
            )

        locations = []
        coordinator_classes = list(coordinators.values())
        for d in range(3):
            district = make_location(f"District {d}", parent_class=rng.choice(classes))
            locations.append(district)
            for v in range(2):
                division = make_location(f"Division {d}{v}", district)
                locations.append(division)
                locations.append(make_location(f"Subdivision {d}{v}", division))
            if d < 2:
                make_location(
                    f"K District {d}", coordinator=True, related_to=district,
                    parent_class=rng.choice(coordinator_classes),
                )

        groups = [ProjectGroup.objects.create(name="No location")]
        for i, location in enumerate(rng.sample(locations, 4)):
            groups.append(ProjectGroup.objects.create(name=f"Group {i}", locationRelation=location))

        finances = []
        for i in range(60):
            project = Project.objects.create(
                name=f"Project {i}", description="batch equivalence",
                programmed=rng.random() < 0.85,
                projectClass=rng.choice(classes + [None]),
                projectLocation=rng.choice(locations + [None]),
                projectGroup=rng.choice(groups + [None, None]),
                costForecast=rng.randint(0, 1000),
                budgetOverrunAmount=rng.randint(0, 50),
            )
            for offset in range(-1, 12):
                for frame_view in (False, True):
                    if rng.random() < 0.7:
                        finances.append(ProjectFinancial(
                            project=project, year=cls.year + offset,
                            value=rng.randint(0, 900), forFrameView=frame_view,
                        ))
        ProjectFinancial.objects.bulk_create(finances)

        for model, relation, rows in (
            (ClassFinancial, "classRelation", ProjectClass.objects.all()),
            (LocationFinancial, "locationRelation", ProjectLocation.objects.all()),
        ):
            model.objects.bulk_create(
                model(**{relation: row}, year=cls.year + offset, forFrameView=frame_view,
                      frameBudget=rng.randint(0, 3000), budgetChange=rng.randint(-300, 300))
                for row in rows
                for offset in range(11)
                for frame_view in (False, True)
                if rng.random() < 0.8
            )

    def assert_batch_matches_single(self, serializer_class, queryset, context):
        list_serializer = serializer_class(queryset, many=True, context=dict(context))
        listed = list_serializer.data
        self.assertTrue(listed)
        # Every row must come from the batch, or this compares the per-row path
        # with itself. (Classes without a path are left to the per-row path.)
        batched = list_serializer.context[PRECOMPUTED_SUMS_KEY]
        expected = {i.id for i in queryset if getattr(i, "path", "") is not None}
        self.assertEqual(set(batched), expected, f"{queryset.model.__name__} batch coverage")
        for row in listed:
            instance = queryset.model.objects.get(id=row["id"])
            single = serializer_class(instance, context=dict(context)).data
            self.assertEqual(
                row, single,
                f"{queryset.model.__name__} {instance.name} with {context}",
            )

    def test_batch_matches_single_instance(self):
        for for_coordinator in (False, True):
            for forced_to_frame in (False, True):
                if forced_to_frame and not for_coordinator:
                    continue  # planning lists never ask for frame-view data
                context = {
                    "finance_year": self.year,
                    "for_coordinator": for_coordinator,
                    "forcedToFrame": forced_to_frame,
                }
                with self.subTest(**context):
                    self.assert_batch_matches_single(
                        ProjectGroupSerializer, ProjectGroup.objects.all(), context
                    )
                    self.assert_batch_matches_single(
                        ProjectClassSerializer,
                        ProjectClass.objects.filter(forCoordinatorOnly=for_coordinator),
                        context,
                    )
                    self.assert_batch_matches_single(
                        ProjectLocationSerializer,
                        ProjectLocation.objects.filter(forCoordinatorOnly=for_coordinator),
                        context,
                    )

    def test_batch_query_count_does_not_grow_with_rows(self):
        context = {"finance_year": self.year, "for_coordinator": False, "forcedToFrame": False}
        # groups, project sums, project budgets
        with self.assertNumQueries(3):
            ProjectGroupSerializer(ProjectGroup.objects.all(), many=True, context=context).data

    def test_list_endpoints_use_a_fixed_number_of_queries(self):
        """Through the real views (their querysets select the related rows).

        The fixture has ~30 classes and ~25 locations, so a query per row
        anywhere would blow well past these bounds.
        """
        endpoints = (
            f"/project-classes/?year={self.year}",
            f"/project-classes/coordinator/?year={self.year}&forcedToFrame=false",
            f"/project-locations/?year={self.year}",
            f"/project-locations/coordinator/?year={self.year}&forcedToFrame=false",
            f"/project-groups/?year={self.year}",
            f"/project-groups/coordinator/?year={self.year}&forcedToFrame=false",
        )
        with patch.object(BaseViewSet, "authentication_classes", new=[]), \
                patch.object(BaseViewSet, "permission_classes", new=[]):
            for url in endpoints:
                with self.subTest(url=url):
                    with CaptureQueriesContext(connection) as queries:
                        response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertLessEqual(len(queries.captured_queries), 10)


class FinancialSumBatchHierarchyTestCase(CacheClearingMixin, TestCase):
    """The batch finds a class's descendants by parent id, not by ``path``,
    which can drift from the parent links (IO-960: migration 0092 gave the
    Itäkeskus coordinator classes a path outside their parent's)."""

    year = date.today().year

    def list_totals(self, queryset, for_coordinator):
        context = {"finance_year": self.year, "for_coordinator": for_coordinator, "forcedToFrame": False}
        serializer = ProjectClassSerializer(queryset, many=True, context=context)
        rows = serializer.data
        self.assertEqual(set(serializer.context[PRECOMPUTED_SUMS_KEY]), {c.id for c in queryset})
        return {row["name"]: row["finances"]["year0"]["plannedBudget"] for row in rows}

    def add_project(self, project_class):
        project = Project.objects.create(
            name=f"Project in {project_class.name}", description="hierarchy",
            programmed=True, projectClass=project_class,
        )
        ProjectFinancial.objects.create(project=project, year=self.year, value=300)

    def test_planning_rows_include_a_child_with_a_drifted_path(self):
        master = ProjectClass.objects.create(name="8 08 Planning", path="8 08 Planning")
        parks = ProjectClass.objects.create(
            name="8 08 03 Parks", parent=master, path="8 08 Planning/8 08 03 Parks"
        )
        drifted = ProjectClass.objects.create(
            name="Itäkeskus", parent=parks, path="Somewhere else/Itäkeskus"
        )
        self.add_project(drifted)

        totals = self.list_totals(ProjectClass.objects.filter(forCoordinatorOnly=False), False)

        self.assertEqual(totals, {"8 08 Planning": 300, "8 08 03 Parks": 300, "Itäkeskus": 300})

    def test_coordinator_rows_include_a_child_with_a_drifted_path(self):
        root = ProjectClass.objects.create(
            name="8 08 K", path="8 08 K, Khn käytettäväksi", forCoordinatorOnly=True
        )
        parks = ProjectClass.objects.create(
            name="8 08 03 K Parks", parent=root, forCoordinatorOnly=True,
            path="8 08 K, Khn käytettäväksi/8 08 03 K Parks",
        )
        planning = ProjectClass.objects.create(name="Itäkeskus planning", path="Itäkeskus planning")
        ProjectClass.objects.create(
            name="8 08 03 12 K Itäkeskus", parent=parks, forCoordinatorOnly=True, relatedTo=planning,
            # The prefix 0092 wrote, without ", Khn käytettäväksi".
            path="8 08 K/8 08 03 K Parks/8 08 03 12 K Itäkeskus",
        )
        self.add_project(planning)

        totals = self.list_totals(ProjectClass.objects.filter(forCoordinatorOnly=True), True)

        self.assertEqual(
            totals, {"8 08 K": 300, "8 08 03 K Parks": 300, "8 08 03 12 K Itäkeskus": 300}
        )
