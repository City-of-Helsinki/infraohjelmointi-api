"""Migration 0126 repairs the coordinator Itäkeskus paths written by 0092 (IO-822)."""

import importlib
from datetime import date
from unittest.mock import patch

from django.apps import apps as django_apps
from django.test import TestCase

from infraohjelmointi_api.models import Project, ProjectClass, ProjectFinancial
from infraohjelmointi_api.serializers.ProjectClassSerializer import ProjectClassSerializer
from infraohjelmointi_api.tests.helpers import CacheClearingMixin

fix_migration = importlib.import_module(
    "infraohjelmointi_api.migrations.0126_fix_itakeskus_coordinator_paths"
)

PLANNING_ROOT = "8 08 Projektialueiden infrarakentaminen"
COORDINATOR_ROOT = "8 08 Projektialueiden infrarakentaminen, Khn käytettäväksi"


class ItakeskusCoordinatorPathTests(CacheClearingMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.year = date.today().year

        def make(name, path, parent=None, coordinator=False, related_to=None):
            return ProjectClass.objects.create(
                name=name, path=path, parent=parent,
                forCoordinatorOnly=coordinator, relatedTo=related_to,
            )

        planning_root = make(PLANNING_ROOT, PLANNING_ROOT)
        planning_parks = make(
            "Puistot ja liikunta-alueet", f"{PLANNING_ROOT}/Puistot ja liikunta-alueet", planning_root
        )
        planning_itakeskus = make(
            "Itäkeskus", f"{PLANNING_ROOT}/Puistot ja liikunta-alueet/Itäkeskus", planning_parks
        )

        self.coordinator_root = make(
            COORDINATOR_ROOT, COORDINATOR_ROOT, coordinator=True, related_to=planning_root
        )
        self.coordinator_parks = make(
            "8 08 03 Puistot ja liikunta-alueet",
            f"{COORDINATOR_ROOT}/8 08 03 Puistot ja liikunta-alueet",
            self.coordinator_root, coordinator=True, related_to=planning_parks,
        )
        # As written by 0092: right parent, path missing ", Khn käytettäväksi".
        self.coordinator_itakeskus = make(
            "8 08 03 12 Itäkeskus",
            f"{PLANNING_ROOT}/8 08 03 Puistot ja liikunta-alueet/8 08 03 12 Itäkeskus",
            self.coordinator_parks, coordinator=True, related_to=planning_itakeskus,
        )

        project = Project.objects.create(
            name="Itäkeskus, Stoan ja Puhoksen alue", description="IO-822 regression",
            programmed=True, projectClass=planning_itakeskus,
        )
        ProjectFinancial.objects.create(project=project, year=self.year, value=300)

    def coordinator_total(self, project_class):
        context = {"finance_year": self.year, "for_coordinator": True, "forcedToFrame": False}
        data = ProjectClassSerializer(project_class, context=context).data
        return data["finances"]["year0"]["plannedBudget"]

    def run_migration(self):
        fix_migration.fix_itakeskus_coordinator_paths(django_apps, schema_editor=None)

    def test_parent_totals_include_itakeskus_after_the_fix(self):
        self.assertEqual(self.coordinator_total(self.coordinator_parks), 0)

        self.run_migration()

        self.coordinator_itakeskus.refresh_from_db()
        self.assertEqual(
            self.coordinator_itakeskus.path,
            f"{COORDINATOR_ROOT}/8 08 03 Puistot ja liikunta-alueet/8 08 03 12 Itäkeskus",
        )
        self.assertEqual(self.coordinator_total(self.coordinator_itakeskus), 300)
        self.assertEqual(self.coordinator_total(self.coordinator_parks), 300)
        self.assertEqual(self.coordinator_total(self.coordinator_root), 300)

    def test_descendants_follow_the_new_path(self):
        child = ProjectClass.objects.create(
            name="Child", path=f"{self.coordinator_itakeskus.path}/Child",
            parent=self.coordinator_itakeskus, forCoordinatorOnly=True,
        )

        self.run_migration()

        child.refresh_from_db()
        self.coordinator_itakeskus.refresh_from_db()
        self.assertEqual(child.path, f"{self.coordinator_itakeskus.path}/Child")

    def test_is_idempotent_and_leaves_correct_paths_alone(self):
        self.run_migration()
        fixed = ProjectClass.objects.get(id=self.coordinator_itakeskus.id).path

        with patch.object(fix_migration, "_clear_cached_sums") as clear:
            self.run_migration()

        clear.assert_not_called()
        self.assertEqual(ProjectClass.objects.get(id=self.coordinator_itakeskus.id).path, fixed)
        self.assertEqual(
            ProjectClass.objects.get(id=self.coordinator_parks.id).path,
            f"{COORDINATOR_ROOT}/8 08 03 Puistot ja liikunta-alueet",
        )

    def test_cache_failure_does_not_fail_the_migration(self):
        with patch("django.core.cache.cache.clear", side_effect=Exception("Redis down")):
            self.run_migration()

        self.coordinator_itakeskus.refresh_from_db()
        self.assertTrue(self.coordinator_itakeskus.path.startswith(COORDINATOR_ROOT + "/"))
