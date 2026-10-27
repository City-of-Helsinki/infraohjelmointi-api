from datetime import date
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from infraohjelmointi_api.models import (
    ClassFinancial,
    LocationFinancial,
    Project,
    ProjectClass,
    ProjectFinancial,
    ProjectLocation,
)
from infraohjelmointi_api.services.CacheService import CacheService
from infraohjelmointi_api.signals import get_financial_sums

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}


def _values_of(node, key):
    """Collects every value stored under `key` anywhere in a payload."""
    found = []
    if isinstance(node, dict):
        if key in node:
            found.append(node[key])
        for value in node.values():
            found += _values_of(value, key)
    elif isinstance(node, (list, tuple)):
        for item in node:
            found += _values_of(item, key)
    return found


@override_settings(CACHES=LOCMEM_CACHE)
class FinanceUpdateEventTest(TestCase):
    """IO-889: finance-update events must carry the values that were just saved."""

    def setUp(self):
        cache.clear()
        self.year = date.today().year

    def _assert_event_has_fresh_value(self, financial, model_name, field, key, old, new):
        with self.captureOnCommitCallbacks(execute=True):
            financial.save()

        # The invalidation after the save cleared the cache; a regular read
        # warms it again, like the UI loading the view does.
        warm_payload = get_financial_sums(
            instance=financial, _type=model_name, finance_year=self.year
        )
        self.assertIn(old, _values_of(warm_payload, key))

        setattr(financial, field, new)
        with patch("infraohjelmointi_api.signals.send_event") as send_event:
            with self.captureOnCommitCallbacks(execute=True):
                financial.save()

        finance_events = [c for c in send_event.call_args_list if c.args[0] == "finance"]
        self.assertEqual(len(finance_events), 1)
        values = _values_of(finance_events[0].args[2], key)
        self.assertIn(new, values)
        self.assertNotIn(old, values)

    def test_class_financial_event_contains_updated_frame_budget(self):
        coordinator_class = ProjectClass.objects.create(
            name="8 01 Event Test Class", path="8/8 01", forCoordinatorOnly=True
        )
        financial = ClassFinancial(
            classRelation=coordinator_class, year=self.year, frameBudget=200
        )

        self._assert_event_has_fresh_value(
            financial, "ClassFinancial", "frameBudget", "frameBudget", 200, 300
        )

    def test_location_financial_event_contains_updated_frame_budget(self):
        coordinator_location = ProjectLocation.objects.create(
            name="Event Test Location", path="EventLoc", forCoordinatorOnly=True
        )
        financial = LocationFinancial(
            locationRelation=coordinator_location, year=self.year, frameBudget=200
        )

        self._assert_event_has_fresh_value(
            financial, "LocationFinancial", "frameBudget", "frameBudget", 200, 300
        )

    def test_project_financial_event_contains_updated_planned_budget(self):
        planning_class = ProjectClass.objects.create(
            name="8 02 Planning Class", path="8/8 02", forCoordinatorOnly=False
        )
        ProjectClass.objects.create(
            name="8 02 Coordinator Class",
            path="8/8 02 coordinator",
            forCoordinatorOnly=True,
            relatedTo=planning_class,
        )
        project = Project.objects.create(
            name="Event Test Project",
            description="Test",
            projectClass=planning_class,
            programmed=True,
        )
        financial = ProjectFinancial(project=project, year=self.year, value=1000)

        self._assert_event_has_fresh_value(
            financial, "ProjectFinancial", "value", "plannedBudget", 1000, 1500
        )


class CacheBypassReadsTest(TestCase):
    @override_settings(CACHES=LOCMEM_CACHE)
    def setUp(self):
        cache.clear()

    @override_settings(CACHES=LOCMEM_CACHE)
    def test_bypass_reads_ignores_cached_values_but_keeps_cache_usable_afterwards(self):
        CacheService.set_lookup("bypass_test", [{"value": "cached"}])

        with CacheService.bypass_reads():
            self.assertIsNone(CacheService.get_lookup("bypass_test"))

        self.assertEqual(CacheService.get_lookup("bypass_test"), [{"value": "cached"}])

    @override_settings(CACHES=LOCMEM_CACHE)
    def test_bypass_reads_is_reset_when_the_block_raises(self):
        CacheService.set_lookup("bypass_test", [{"value": "cached"}])

        with self.assertRaises(RuntimeError):
            with CacheService.bypass_reads():
                raise RuntimeError("boom")

        self.assertEqual(CacheService.get_lookup("bypass_test"), [{"value": "cached"}])
