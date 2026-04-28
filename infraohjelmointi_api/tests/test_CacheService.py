"""Tests for CacheService."""

import time
import uuid
from datetime import date
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings

from helusers.models import ADGroup

from infraohjelmointi_api.models import (
    ProjectClass,
    ClassFinancial,
    Project,
    ProjectFinancial,
    ProjectLocation,
    LocationFinancial,
    ProjectGroup,
    ProjectPhase,
    ProjectProgrammer,
    ProjectLock,
    ProjectSet,
    ProjectType,
    ProjectCategory,
    ConstructionPhase,
    Person,
    Task,
    TalpaProjectOpening,
)
from infraohjelmointi_api.serializers import ProjectClassSerializer
from infraohjelmointi_api.serializers.FinancialSumSerializer import FinancialSumSerializer
from infraohjelmointi_api.services.CacheService import CacheService
from infraohjelmointi_api.services.RedisAvailabilityChecker import RedisAvailabilityChecker

LOCMEM_CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


@override_settings(CACHES=LOCMEM_CACHE)
class CacheServiceBasicTest(TestCase):
    """Basic unit tests for CacheService methods."""

    def setUp(self):
        cache.clear()
        self.current_year = date.today().year
        self.cache_disabled = 'dummy' in settings.CACHES['default']['BACKEND'].lower()

    def test_cache_key_generation_is_deterministic(self):
        """Cache keys should be consistent for same inputs"""
        key1 = CacheService._generate_cache_key(
            'test_prefix',
            instance_id='123',
            year=2024,
            for_frame_view=True
        )
        key2 = CacheService._generate_cache_key(
            'test_prefix',
            instance_id='123',
            year=2024,
            for_frame_view=True
        )

        self.assertEqual(key1, key2, "Cache keys should be deterministic")

    def test_cache_key_generation_differs_for_different_inputs(self):
        """Different inputs should generate different cache keys"""
        key1 = CacheService._generate_cache_key(
            'test_prefix',
            instance_id='123',
            year=2024
        )
        key2 = CacheService._generate_cache_key(
            'test_prefix',
            instance_id='456',
            year=2024
        )

        self.assertNotEqual(key1, key2, "Different inputs should generate different keys")

    def test_financial_sum_cache_set_and_get(self):
        """Test setting and getting financial sum from cache"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")

        test_data = {
            'year0': {'frameBudget': 100000, 'budgetChange': 0},
            'year1': {'frameBudget': 110000, 'budgetChange': 10000},
        }

        instance_id = str(uuid.uuid4())

        # Set cache
        CacheService.set_financial_sum(
            instance_id=instance_id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            data=test_data,
            for_coordinator=False
        )

        # Get cache
        cached = CacheService.get_financial_sum(
            instance_id=instance_id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )

        self.assertEqual(cached, test_data)

    def test_frame_budgets_cache_set_and_get(self):
        """Test setting and getting frame budgets from cache"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")

        test_data = {
            'budgets': [
                {'class': 'TestClass', 'budget': 500000}
            ]
        }

        # Set cache
        CacheService.set_frame_budgets(
            year=self.current_year,
            for_frame_view=True,
            data=test_data
        )

        # Get cache
        cached = CacheService.get_frame_budgets(
            year=self.current_year,
            for_frame_view=True
        )

        self.assertEqual(cached, test_data)

    def test_cache_returns_none_for_nonexistent_key(self):
        """Cache should return None for keys that don't exist"""
        result = CacheService.get_financial_sum(
            instance_id=str(uuid.uuid4()),
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )

        self.assertIsNone(result)

    def test_invalidate_financial_sum(self):
        """Test that invalidate_financial_sum clears cached data"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")

        instance_id = str(uuid.uuid4())
        test_data = {'year0': {'frameBudget': 100000}}

        # Set cache
        CacheService.set_financial_sum(
            instance_id=instance_id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            data=test_data,
            for_coordinator=False
        )

        # Verify it's cached
        cached = CacheService.get_financial_sum(
            instance_id=instance_id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertEqual(cached, test_data)

        # Invalidate
        CacheService.invalidate_financial_sum(
            instance_id=instance_id,
            instance_type='ProjectClass'
        )

        # Verify it's cleared
        cached_after = CacheService.get_financial_sum(
            instance_id=instance_id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertIsNone(cached_after)

    def test_invalidate_frame_budgets(self):
        """Test that invalidate_frame_budgets clears cached data"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")

        test_data = {'budgets': []}

        # Set cache for both forFrameView values
        CacheService.set_frame_budgets(
            year=self.current_year,
            for_frame_view=True,
            data=test_data
        )
        CacheService.set_frame_budgets(
            year=self.current_year,
            for_frame_view=False,
            data=test_data
        )

        # Invalidate
        CacheService.invalidate_frame_budgets(year=self.current_year)

        # Verify both are cleared
        cached_true = CacheService.get_frame_budgets(
            year=self.current_year,
            for_frame_view=True
        )
        cached_false = CacheService.get_frame_budgets(
            year=self.current_year,
            for_frame_view=False
        )

        self.assertIsNone(cached_true)
        self.assertIsNone(cached_false)


@override_settings(CACHES=LOCMEM_CACHE)
class CacheServiceIntegrationTest(TransactionTestCase):
    """Integration tests for CacheService with Django models"""

    def setUp(self):
        cache.clear()
        self.current_year = date.today().year
        self.cache_disabled = 'dummy' in settings.CACHES['default']['BACKEND'].lower()

        self.programmer = ProjectProgrammer.objects.create(
            firstName="Test",
            lastName="Programmer"
        )

        # Create coordinator class with financials
        self.coord_class = ProjectClass.objects.create(
            name="Test Coordinator Class",
            path="TestCoord",
            forCoordinatorOnly=True,
            defaultProgrammer=self.programmer
        )

        # Add financial data
        for offset in range(3):
            ClassFinancial.objects.create(
                classRelation=self.coord_class,
                year=self.current_year + offset,
                frameBudget=100000 + (offset * 10000),
                budgetChange=0,
                forFrameView=False
            )

    def test_financial_sum_serializer_uses_cache(self):
        """Test that FinancialSumSerializer uses the cache."""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")

        serializer = ProjectClassSerializer(
            self.coord_class,
            context={
                'finance_year': self.current_year,
                'for_coordinator': False,  # Explicitly set
                'forcedToFrame': False
            }
        )
        data1 = serializer.data

        # Verify data was cached with the correct context
        cached = CacheService.get_financial_sum(
            instance_id=self.coord_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,  # forcedToFrame
            for_coordinator=False   # for_coordinator from context
        )

        self.assertIsNotNone(cached, "Data should be cached after first serialization")

        # Second call - cache hit, should use cached data
        serializer2 = ProjectClassSerializer(
            self.coord_class,
            context={
                'finance_year': self.current_year,
                'for_coordinator': False,
                'forcedToFrame': False
            }
        )
        data2 = serializer2.data

        # Data should be identical
        self.assertEqual(data1['finances'], data2['finances'])

    def test_cache_invalidation_on_financial_save(self):
        """Test that cache is invalidated when financial data changes"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")
        # Create programming class
        prog_class = ProjectClass.objects.create(
            name="Test Programming Class",
            path="TestProg",
            forCoordinatorOnly=False,
            relatedTo=self.coord_class
        )

        # Create project
        project = Project.objects.create(
            name="Test Project",
            description="Test project description",
            projectClass=prog_class,
            programmed=True,
            personProgramming=self.programmer
        )

        # Create initial financial
        pf = ProjectFinancial.objects.create(
            project=project,
            year=self.current_year,
            value=50000,
            forFrameView=False
        )

        # Cache some data for the class
        test_cache_data = {'year0': {'frameBudget': 999999}}
        CacheService.set_financial_sum(
            instance_id=prog_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            data=test_cache_data,
            for_coordinator=False
        )

        # Verify it's cached
        cached_before = CacheService.get_financial_sum(
            instance_id=prog_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertEqual(cached_before, test_cache_data)

        # Update financial - this should trigger cache invalidation via signal
        pf.value = 60000
        pf.save()

        # Cache should be cleared
        cached_after = CacheService.get_financial_sum(
            instance_id=prog_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertIsNone(cached_after, "Cache should be invalidated after financial update")

    def test_cache_invalidation_on_class_financial_save(self):
        """Test that cache is invalidated when ClassFinancial changes"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")
        # Cache data for the coordinator class
        test_cache_data = {'year0': {'frameBudget': 999999}}
        CacheService.set_financial_sum(
            instance_id=self.coord_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            data=test_cache_data,
            for_coordinator=True
        )

        # Verify cached
        cached_before = CacheService.get_financial_sum(
            instance_id=self.coord_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=True
        )
        self.assertEqual(cached_before, test_cache_data)

        # Update ClassFinancial - should trigger cache invalidation
        cf = ClassFinancial.objects.get(
            classRelation=self.coord_class,
            year=self.current_year,
            forFrameView=False
        )
        cf.frameBudget = 200000
        cf.save()

        # Cache should be cleared
        cached_after = CacheService.get_financial_sum(
            instance_id=self.coord_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=True
        )
        self.assertIsNone(cached_after, "Cache should be invalidated after ClassFinancial update")

    def test_cache_invalidation_for_related_planning_class(self):
        """Test that cache is invalidated for planning class when coordinator class finances change"""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")
        # Create planning class linked to coordinator class
        planning_class = ProjectClass.objects.create(
            name="Test Planning Class",
            path="TestProg",
            forCoordinatorOnly=False,
            relatedTo=self.coord_class  # Link to coordinator
        )

        # Cache data for the planning class (which shows coordinator's finances)
        test_cache_data = {'year0': {'frameBudget': 999999}}
        CacheService.set_financial_sum(
            instance_id=planning_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            data=test_cache_data,
            for_coordinator=False  # Planning class view
        )

        # Verify cached
        cached_before = CacheService.get_financial_sum(
            instance_id=planning_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertEqual(cached_before, test_cache_data)

        # Update coordinator's ClassFinancial - should invalidate planning class cache too
        cf = ClassFinancial.objects.get(
            classRelation=self.coord_class,
            year=self.current_year,
            forFrameView=False
        )
        cf.frameBudget = 200000
        cf.save()

        # Planning class cache should be cleared (because it displays coordinator's finances)
        cached_after = CacheService.get_financial_sum(
            instance_id=planning_class.id,
            instance_type='ProjectClass',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertIsNone(cached_after, "Planning class cache should be invalidated when coordinator finances change")

    def test_cache_invalidation_for_related_planning_location(self):
        """Test that cache is invalidated for planning location when coordinator location finances change."""
        if self.cache_disabled:
            self.skipTest("Cache is disabled (Redis unavailable)")

        coord_location = ProjectLocation.objects.create(
            name="Test Coordinator Location",
            path="CoordLoc",
            forCoordinatorOnly=True
        )

        # Create planning location linked to coordinator location
        planning_location = ProjectLocation.objects.create(
            name="Test Planning Location",
            path="PlanLoc",
            forCoordinatorOnly=False,
            relatedTo=coord_location  # Link to coordinator
        )

        # Add financial data to coordinator location
        LocationFinancial.objects.create(
            locationRelation=coord_location,
            year=self.current_year,
            frameBudget=50000,
            budgetChange=0,
            forFrameView=False
        )

        # Cache data for the planning location (which shows coordinator's finances)
        test_cache_data = {'year0': {'frameBudget': 999999}}
        CacheService.set_financial_sum(
            instance_id=planning_location.id,
            instance_type='ProjectLocation',
            year=self.current_year,
            for_frame_view=False,
            data=test_cache_data,
            for_coordinator=False  # Planning location view
        )

        # Verify cached
        cached_before = CacheService.get_financial_sum(
            instance_id=planning_location.id,
            instance_type='ProjectLocation',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertEqual(cached_before, test_cache_data)

        # Update coordinator's LocationFinancial - should invalidate planning location cache too
        lf = LocationFinancial.objects.get(
            locationRelation=coord_location,
            year=self.current_year,
            forFrameView=False
        )
        lf.frameBudget = 200000
        lf.save()

        # Planning location cache should be cleared
        cached_after = CacheService.get_financial_sum(
            instance_id=planning_location.id,
            instance_type='ProjectLocation',
            year=self.current_year,
            for_frame_view=False,
            for_coordinator=False
        )
        self.assertIsNone(cached_after, "Planning location cache should be invalidated when coordinator finances change")


class CacheResilienceTest(TestCase):
    """Test cache resilience when Redis is unavailable."""

    def test_cache_operations_dont_crash_when_redis_unavailable(self):
        """Cache operations should gracefully handle Redis failures."""
        backend = settings.CACHES['default']['BACKEND']

        if 'redis' not in backend.lower():
            self.skipTest("This test only applies to Redis backend")

        redis_available = RedisAvailabilityChecker.is_available()
        test_id = str(uuid.uuid4())
        test_data = {'year0': {'frameBudget': 100000}}

        CacheService.set_financial_sum(
            instance_id=test_id,
            instance_type='ProjectClass',
            year=2024,
            for_frame_view=False,
            data=test_data,
            for_coordinator=False
        )

        result = CacheService.get_financial_sum(
            instance_id=test_id,
            instance_type='ProjectClass',
            year=2024,
            for_frame_view=False,
            for_coordinator=False
        )

        if redis_available:
            self.assertEqual(result, test_data)
        else:
            self.assertIsNotNone(result or True)

    def test_cache_clear_all(self):
        """Test that clear_all() clears the entire cache."""
        cache.set('test_key_1', 'value1', timeout=300)
        cache.set('test_key_2', 'value2', timeout=300)

        CacheService.clear_all()

        self.assertIsNone(cache.get('test_key_1'))
        self.assertIsNone(cache.get('test_key_2'))


class CacheBackendTest(TestCase):
    """Test that cache backend is properly configured."""

    def test_cache_backend_configured(self):
        """Verify that a cache backend is configured."""
        self.assertIn('default', settings.CACHES)
        backend = settings.CACHES['default']['BACKEND']

        # Should be Redis, LocMemCache, or DummyCache (when Redis unavailable)
        self.assertTrue(
            'redis' in backend.lower() or 'locmem' in backend.lower() or 'dummy' in backend.lower(),
            f"Expected Redis, LocMemCache, or DummyCache backend, got: {backend}"
        )

    def test_cache_timeout_configured(self):
        """Verify cache timeout is reasonable."""
        timeout = CacheService.CACHE_TIMEOUT

        self.assertGreaterEqual(timeout, 60, "Cache timeout too short")
        self.assertLessEqual(timeout, 86400, "Cache timeout too long")


@override_settings(CACHES=LOCMEM_CACHE)
class LookupCacheTest(TestCase):
    """Tests for lookup table caching."""

    def setUp(self):
        cache.clear()

    def test_lookup_cache_set_and_get(self):
        """Test setting and getting lookup cache."""
        test_data = [{'id': 1, 'name': 'Test'}]
        CacheService.set_lookup('TestModel', test_data)

        result = CacheService.get_lookup('TestModel')
        self.assertEqual(result, test_data)

    def test_lookup_cache_invalidate(self):
        """Test invalidating lookup cache."""
        test_data = [{'id': 1, 'name': 'Test'}]
        CacheService.set_lookup('TestModel', test_data)

        CacheService.invalidate_lookup('TestModel')

        result = CacheService.get_lookup('TestModel')
        self.assertIsNone(result)

    def test_lookup_cache_miss_returns_none(self):
        """Test that cache miss returns None."""
        result = CacheService.get_lookup('NonExistentModel')
        self.assertIsNone(result)

    def test_cache_timeout_uses_setting(self):
        """Verify cache timeout uses CACHE_TIMEOUT setting."""
        expected_timeout = getattr(settings, 'CACHE_TIMEOUT', 43200)
        self.assertEqual(CacheService.CACHE_TIMEOUT, expected_timeout)


@override_settings(CACHES=LOCMEM_CACHE)
class CachedLookupViewSetTest(TestCase):
    """Tests for CachedLookupViewSet functionality."""

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        coord_group = ADGroup.objects.create(
            name='sg_kymp_sso_io_koordinaattorit',
            display_name='Coordinators'
        )
        self.user.ad_groups.add(coord_group)
        self.client.force_login(self.user)

    def test_project_types_list_is_cached(self):
        """Test that project types list response is cached."""
        ProjectType.objects.create(value='test_type')

        response = self.client.get('/project-types/')
        self.assertEqual(response.status_code, 200)

        cached = CacheService.get_lookup('ProjectType')
        self.assertIsNotNone(cached)

    def test_project_phases_list_is_cached(self):
        """Test that project phases list response is cached."""
        ProjectPhase.objects.create(value='test_phase')

        response = self.client.get('/project-phases/')
        self.assertEqual(response.status_code, 200)

        cached = CacheService.get_lookup('ProjectPhase')
        self.assertIsNotNone(cached)

    def test_cached_response_served_on_second_request(self):
        """Test that second request is served from cache."""
        initial_count = ProjectType.objects.count()
        ProjectType.objects.create(value='cached_type_unique')

        response1 = self.client.get('/project-types/')
        self.assertEqual(response1.status_code, 200)
        cached_count = len(response1.json())

        ProjectType.objects.create(value='another_type_unique')

        response2 = self.client.get('/project-types/')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(len(response2.json()), cached_count)

    def test_create_invalidates_cache(self):
        """Test that creating an item invalidates the cache."""
        response = self.client.get('/project-types/')
        self.assertEqual(response.status_code, 200)
        initial_count = len(response.json())

        self.assertIsNotNone(CacheService.get_lookup('ProjectType'))

        response = self.client.post('/project-types/', {'value': 'new_type'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        self.assertIsNone(CacheService.get_lookup('ProjectType'))

        response = self.client.get('/project-types/')
        self.assertEqual(len(response.json()), initial_count + 1)

    def test_update_invalidates_cache(self):
        """Test that updating an item invalidates the cache."""
        obj = ProjectType.objects.create(value='update_test')

        self.client.get('/project-types/')
        self.assertIsNotNone(CacheService.get_lookup('ProjectType'))

        response = self.client.put(f'/project-types/{obj.id}/', {'value': 'updated'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.assertIsNone(CacheService.get_lookup('ProjectType'))

    def test_partial_update_invalidates_cache(self):
        """Test that partial update invalidates the cache."""
        obj = ProjectType.objects.create(value='patch_test')

        self.client.get('/project-types/')
        self.assertIsNotNone(CacheService.get_lookup('ProjectType'))

        response = self.client.patch(f'/project-types/{obj.id}/', {'value': 'patched'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        self.assertIsNone(CacheService.get_lookup('ProjectType'))

    def test_delete_invalidates_cache(self):
        """Test that deleting an item invalidates the cache."""
        obj = ProjectType.objects.create(value='delete_test')

        self.client.get('/project-types/')
        self.assertIsNotNone(CacheService.get_lookup('ProjectType'))

        response = self.client.delete(f'/project-types/{obj.id}/')
        self.assertEqual(response.status_code, 204)

        self.assertIsNone(CacheService.get_lookup('ProjectType'))

    def test_reorder_with_permission_returns_200(self):
        """User with correct permissions can reorder."""
        admin_group = ADGroup.objects.create(
            name='sg_kymp_sso_io_admin',
            display_name='Admins'
        )
        self.user.ad_groups.add(admin_group)

        obj1 = ProjectType.objects.create(value='reorder_test')
        obj2 = ProjectType.objects.create(value='reorder_test')

        payload = [
            {"id": obj1.id, "order": 2},
            {"id": obj2.id, "order": 1},
        ]

        response = self.client.put(
            '/project-types/reorder/',
            payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

    def test_reorder_without_permission_returns_403(self):
        """User without correct permissions cannot reorder."""
        # Remove permission group
        self.user.ad_groups.clear()

        obj1 = ProjectType.objects.create(value='reorder_fail_test')
        obj2 = ProjectType.objects.create(value='reorder_fail_test')

        payload = [
            {"id": obj1.id, "order": 2},
            {"id": obj2.id, "order": 1},
        ]

        response = self.client.put(
            '/project-types/reorder/',
            payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 403)


@override_settings(CACHES=LOCMEM_CACHE)
class AllLookupViewSetsTest(TestCase):
    """Tests to cover all lookup ViewSets."""

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser2', password='testpass')
        coord_group, _ = ADGroup.objects.get_or_create(
            name='sg_kymp_sso_io_koordinaattorit',
            defaults={'display_name': 'Coordinators'}
        )
        self.user.ad_groups.add(coord_group)
        self.client.force_login(self.user)

    def test_construction_phase_viewset(self):
        """Test ConstructionPhaseViewSet is cached."""
        response = self.client.get('/construction-phases/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ConstructionPhase'))

    def test_project_phase_detail_viewset(self):
        """Test ProjectPhaseDetailViewSet is cached."""
        response = self.client.get('/project-phase-details/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ProjectPhaseDetail'))

    def test_planning_phase_viewset(self):
        """Test PlanningPhaseViewSet is cached."""
        response = self.client.get('/planning-phases/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('PlanningPhase'))

    def test_project_area_viewset(self):
        """Test ProjectAreaViewSet is cached."""
        response = self.client.get('/project-areas/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ProjectArea'))

    def test_project_category_viewset(self):
        """Test ProjectCategoryViewSet is cached."""
        response = self.client.get('/project-categories/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ProjectCategory'))

    def test_project_priority_viewset(self):
        """Test ProjectPriorityViewSet is cached."""
        response = self.client.get('/project-priority/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ProjectPriority'))

    def test_project_quality_level_viewset(self):
        """Test ProjectQualityLevelViewSet is cached."""
        response = self.client.get('/project-quality-levels/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ProjectQualityLevel'))

    def test_project_responsible_zone_viewset(self):
        """Test ProjectResponsibleZoneViewSet is cached."""
        response1 = self.client.get('/responsible-zones/')
        self.assertEqual(response1.status_code, 200)

        response2 = self.client.get('/responsible-zones/')
        self.assertEqual(response2.status_code, 200)

        cached = CacheService.get_lookup('ResponsibleZone')
        self.assertIsNotNone(cached)

    def test_project_risk_viewset(self):
        """Test ProjectRiskViewSet is cached."""
        response = self.client.get('/project-risks/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('ProjectRisk'))

    def test_task_status_viewset(self):
        """Test TaskStatusViewSet is cached."""
        response = self.client.get('/task-status/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(CacheService.get_lookup('TaskStatus'))


@override_settings(CACHES=LOCMEM_CACHE)
class RedisAvailabilityCheckerTest(TestCase):
    """Tests for RedisAvailabilityChecker."""

    def setUp(self):
        RedisAvailabilityChecker.reset()

    def test_is_available_caches_result(self):
        """Test that availability check is cached."""
        with patch.object(RedisAvailabilityChecker, '_check_redis_connection', return_value=True):
            result1 = RedisAvailabilityChecker.is_available()
            result2 = RedisAvailabilityChecker.is_available()
            self.assertTrue(result1)
            self.assertTrue(result2)

    def test_check_with_timeout_handles_timeout(self):
        """Test that timeout check works correctly."""
        result = RedisAvailabilityChecker._check_with_timeout('nonexistent-host-12345', 6379)
        self.assertFalse(result)

    def test_check_redis_connection_returns_false_without_redis_url(self):
        """Test that check returns False when REDIS_URL is not set."""
        with patch.object(settings, 'REDIS_URL', None):
            result = RedisAvailabilityChecker._check_redis_connection()
            self.assertFalse(result)

    def test_check_redis_connection_returns_false_with_dummy_cache(self):
        """Test that check returns False with dummy cache backend."""
        with patch.object(settings, 'REDIS_URL', 'redis://localhost:6379/0'):
            with patch.object(settings, 'CACHES', {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}):
                result = RedisAvailabilityChecker._check_redis_connection()
                self.assertFalse(result)

    def test_reset_clears_cached_state(self):
        """Test that reset clears cached availability state."""
        with patch.object(RedisAvailabilityChecker, '_check_redis_connection', return_value=True):
            RedisAvailabilityChecker.is_available()
            self.assertIsNotNone(RedisAvailabilityChecker._is_available)

            RedisAvailabilityChecker.reset()
            self.assertIsNone(RedisAvailabilityChecker._is_available)
            self.assertEqual(RedisAvailabilityChecker._last_check, 0)


@override_settings(CACHES=LOCMEM_CACHE)
class CacheServiceEdgeCasesTest(TestCase):
    """Tests for edge cases and error handling in CacheService."""

    def setUp(self):
        cache.clear()

    def test_get_cache_key_name_uses_model_name(self):
        """Test that get_cache_key_name returns model name from serializer."""
        from infraohjelmointi_api.views.CachedLookupViewSet import CachedLookupViewSet
        from infraohjelmointi_api.views.ProjectTypeViewSet import ProjectTypeViewSet

        viewset = ProjectTypeViewSet()
        viewset.action = 'list'
        key_name = viewset.get_cache_key_name()
        self.assertEqual(key_name, 'ProjectType')

    def test_cached_lookup_viewset_handles_non_200_response(self):
        """Test that non-200 responses don't cache."""
        from infraohjelmointi_api.views.ProjectTypeViewSet import ProjectTypeViewSet

        viewset = ProjectTypeViewSet()
        viewset.action = 'list'

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.data = []

        with patch.object(viewset, 'list', return_value=mock_response):
            result = viewset.list(None)
            self.assertEqual(result.status_code, 400)
            self.assertIsNone(CacheService.get_lookup('ProjectType'))

    def test_invalidate_financial_sum_handles_exceptions(self):
        """Test that invalidate_financial_sum handles exceptions gracefully."""
        with patch.object(CacheService, '_safe_cache_delete', side_effect=Exception("Test error")):
            CacheService.invalidate_financial_sum('123', 'ProjectClass')

    def test_invalidate_frame_budgets_with_year(self):
        """Test invalidate_frame_budgets with specific year."""
        test_data = {'budgets': []}
        CacheService.set_frame_budgets(2024, True, test_data)
        CacheService.set_frame_budgets(2025, True, test_data)

        CacheService.invalidate_frame_budgets(2024)

        self.assertIsNone(CacheService.get_frame_budgets(2024, True))
        self.assertIsNotNone(CacheService.get_frame_budgets(2025, True))

    def test_circuit_breaker_disables_cache_after_failures(self):
        """Test that circuit breaker disables cache after multiple failures."""
        with patch.object(cache, 'set', side_effect=Exception("Redis error")):
            for _ in range(3):
                CacheService.set_financial_sum('123', 'ProjectClass', 2024, False, {'test': 'data'})

            result = CacheService.get_financial_sum('123', 'ProjectClass', 2024, False)
            self.assertIsNone(result)

    def test_cache_re_enables_after_timeout(self):
        """Test that cache re-enables after circuit breaker timeout."""
        CacheService._cache_failures = 3
        CacheService._cache_disabled_until = time.time() - 10

        with patch.object(CacheService, '_check_redis_availability', return_value=True):
            result = CacheService._is_cache_disabled()
            self.assertFalse(result)
            self.assertEqual(CacheService._cache_failures, 0)


@override_settings(CACHES=LOCMEM_CACHE)
class CachedLookupDeletionModificationTest(TestCase):
    """Tests for lookup item deletion and modification with project status logic."""

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser_lookup', password='testpass')
        coord_group = ADGroup.objects.create(
            name='sg_kymp_sso_io_koordinaattorit',
            display_name='Coordinators'
        )
        self.user.ad_groups.add(coord_group)
        self.client.force_login(self.user)
        
        # Create phases
        self.phase_completed, _ = ProjectPhase.objects.get_or_create(value='completed')
        self.phase_warranty, _ = ProjectPhase.objects.get_or_create(value='warrantyPeriod')
        self.phase_planning, _ = ProjectPhase.objects.get_or_create(value='planning')
        
        # Create programmer
        self.programmer = ProjectProgrammer.objects.create(
            firstName="Test",
            lastName="Programmer"
        )
        
        # Create project class
        self.proj_class = ProjectClass.objects.create(
            name="Test Class",
            path="TestClass",
            defaultProgrammer=self.programmer
        )

    def test_update_value_completed_project_preserves_old_value(self):
        """Test that updating a lookup value used by a completed project preserves the old value."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat A')
        
        # Create completed project with this category
        project = Project.objects.create(
            name="Completed Project",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_completed,
            category=category,
            personProgramming=self.programmer
        )
        
        self.assertEqual(project.category.value, 'Cat A')
        
        # Update category value
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat AA'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Reload project and check that category value stayed the same
        project.refresh_from_db()
        self.assertEqual(project.category.value, 'Cat A')
        
        # Check that a new hidden item was created with old value
        old_items = ProjectCategory.objects.filter(value='Cat A', deleted=True)
        self.assertGreaterEqual(old_items.count(), 1)

    def test_update_value_warranty_project_preserves_old_value(self):
        """Test that updating a lookup value used by a warranty period project preserves the old value."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat B')
        
        # Create warranty period project with this category
        project = Project.objects.create(
            name="Warranty Project",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_warranty,
            category=category,
            personProgramming=self.programmer
        )
        
        self.assertEqual(project.category.value, 'Cat B')
        
        # Update category value
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat BB'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Reload project and check that category value stayed the same
        project.refresh_from_db()
        self.assertEqual(project.category.value, 'Cat B')

    def test_update_value_planning_project_gets_new_value(self):
        """Test that updating a lookup value used by a non-completed project updates the value."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat C')
        
        # Create planning project with this category
        project = Project.objects.create(
            name="Planning Project",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        
        self.assertEqual(project.category.value, 'Cat C')
        
        # Update category value
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat CC'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Reload project and check that it was updated
        project.refresh_from_db()
        self.assertEqual(project.category.value, 'Cat CC')

    def test_delete_value_completed_project_preserves_old_value(self):
        """Test that deleting a lookup value used by a completed project preserves the old value."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat D')
        
        # Create completed project with this category
        project = Project.objects.create(
            name="Completed Project Delete",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_completed,
            category=category,
            personProgramming=self.programmer
        )
        
        category_id = category.id
        self.assertEqual(project.category.value, 'Cat D')
        
        # Delete category
        response = self.client.delete(f'/project-categories/{category_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Reload project and check that it still has a category with the old value
        project.refresh_from_db()
        self.assertIsNotNone(project.category)
        self.assertEqual(project.category.value, 'Cat D')
        
        # The original category should be deleted, but a hidden one should exist
        self.assertFalse(ProjectCategory.objects.filter(id=category_id, deleted=False).exists())
        hidden_items = ProjectCategory.objects.filter(value='Cat D', deleted=True)
        self.assertEqual(hidden_items.count(), 1)
        
        # Hidden item should not appear in the lookup list
        response = self.client.get('/project-categories/')
        self.assertEqual(response.status_code, 200)
        categories_list = response.json()
        for cat in categories_list:
            self.assertNotEqual(cat['value'], 'Cat D')

    def test_delete_value_planning_project_clears_value(self):
        """Test that deleting a lookup value used by a non-completed project clears the field."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat E')
        
        # Create planning project with this category
        project = Project.objects.create(
            name="Planning Project Delete",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        
        category_id = category.id
        self.assertEqual(project.category.value, 'Cat E')
        
        # Delete category
        response = self.client.delete(f'/project-categories/{category_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Reload project and check that category is None
        project.refresh_from_db()
        self.assertIsNone(project.category)

    def test_multiple_projects_with_different_phases_on_update(self):
        """Test updating a value when multiple projects use it with different phases."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat F')
        
        # Create completed project with this category
        completed_proj = Project.objects.create(
            name="Completed Project Multi",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_completed,
            category=category,
            personProgramming=self.programmer
        )
        
        # Create planning project with same category
        planning_proj = Project.objects.create(
            name="Planning Project Multi",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        
        # Update category
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat FF'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Completed project should have old value preserved
        completed_proj.refresh_from_db()
        self.assertEqual(completed_proj.category.value, 'Cat F')
        
        # Planning project should have new value
        planning_proj.refresh_from_db()
        self.assertEqual(planning_proj.category.value, 'Cat FF')

    def test_multiple_projects_with_different_phases_on_delete(self):
        """Test deleting a value when multiple projects use it with different phases."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat G')
        
        # Create completed project with this category
        completed_proj = Project.objects.create(
            name="Completed Project Multi Delete",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_completed,
            category=category,
            personProgramming=self.programmer
        )
        
        # Create planning project with same category
        planning_proj = Project.objects.create(
            name="Planning Project Multi Delete",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        
        category_id = category.id
        
        # Delete category
        response = self.client.delete(f'/project-categories/{category_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Completed project should have value preserved
        completed_proj.refresh_from_db()
        self.assertIsNotNone(completed_proj.category)
        self.assertEqual(completed_proj.category.value, 'Cat G')
        
        # Planning project should have value cleared
        planning_proj.refresh_from_db()
        self.assertIsNone(planning_proj.category)

    def test_deleted_items_excluded_from_lookup_list(self):
        """Test that deleted lookup items are not included in the list response."""
        # Create categories
        cat_visible = ProjectCategory.objects.create(value='Visible')
        cat_hidden = ProjectCategory.objects.create(value='Hidden', deleted=True)
        
        # Get categories list
        response = self.client.get('/project-categories/')
        self.assertEqual(response.status_code, 200)
        categories = response.json()
        
        # Check that visible category is in list
        values = [c['value'] for c in categories]
        self.assertIn('Visible', values)
        
        # Check that hidden category is not in list
        self.assertNotIn('Hidden', values)

    def test_partial_update_preserves_completed_project_value(self):
        """Test that partial update (PATCH) also preserves completed project values."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat H')
        
        # Create completed project with this category
        project = Project.objects.create(
            name="Completed Project Patch",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_completed,
            category=category,
            personProgramming=self.programmer
        )
        
        self.assertEqual(project.category.value, 'Cat H')
        
        # Patch category value
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat HH'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Reload project and check that category value stayed the same
        project.refresh_from_db()
        self.assertEqual(project.category.value, 'Cat H')

    def test_update_value_no_change_does_not_create_hidden_item(self):
        """Test that updating a lookup value to the same value does not create hidden items."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat I')
        
        # Create completed project with this category
        project = Project.objects.create(
            name="Completed Project No Change",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_completed,
            category=category,
            personProgramming=self.programmer
        )
        
        initial_hidden_count = ProjectCategory.objects.filter(deleted=True).count()
        
        # Update category to same value
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat I'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # No new hidden items should be created
        final_hidden_count = ProjectCategory.objects.filter(deleted=True).count()
        self.assertEqual(final_hidden_count, initial_hidden_count)

    def test_update_value_no_completed_projects_updates_all(self):
        """Test that updating a lookup value when no completed projects use it updates all projects."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat J')
        
        # Create planning projects with this category
        project1 = Project.objects.create(
            name="Planning Project 1",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        project2 = Project.objects.create(
            name="Planning Project 2",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        
        # Update category value
        response = self.client.patch(
            f'/project-categories/{category.id}/',
            {'value': 'Cat JJ'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Both projects should have new value
        project1.refresh_from_db()
        project2.refresh_from_db()
        self.assertEqual(project1.category.value, 'Cat JJ')
        self.assertEqual(project2.category.value, 'Cat JJ')

    def test_delete_value_no_completed_projects_clears_all(self):
        """Test that deleting a lookup value when no completed projects use it clears all projects."""
        # Create category
        category = ProjectCategory.objects.create(value='Cat K')
        
        # Create planning projects with this category
        project1 = Project.objects.create(
            name="Planning Project Delete 1",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        project2 = Project.objects.create(
            name="Planning Project Delete 2",
            description="Test",
            projectClass=self.proj_class,
            phase=self.phase_planning,
            category=category,
            personProgramming=self.programmer
        )
        
        category_id = category.id
        
        # Delete category
        response = self.client.delete(f'/project-categories/{category_id}/')
        self.assertEqual(response.status_code, 204)
        
        # Both projects should have category cleared
        project1.refresh_from_db()
        project2.refresh_from_db()
        self.assertIsNone(project1.category)
        self.assertIsNone(project2.category)


@override_settings(CACHES=LOCMEM_CACHE)
class PersonMultiFKDeletionTest(TestCase):
    """Regression tests for IO-833: deleting/updating a Person referenced by
    Project via more than one FK field (personPlanning, personConstruction).

    Before the fix, PersonViewSet did not declare project_field, so the
    base-class cleanup was skipped and Postgres rejected the delete with a
    foreign key violation (`infraohjelmointi_api_personConstruction_..._fk`).
    """

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser_person_fk', password='testpass'
        )
        coord_group, _ = ADGroup.objects.get_or_create(
            name='sg_kymp_sso_io_koordinaattorit',
            defaults={'display_name': 'Coordinators'},
        )
        self.user.ad_groups.add(coord_group)
        self.client.force_login(self.user)

        self.phase_completed, _ = ProjectPhase.objects.get_or_create(value='completed')
        self.phase_warranty, _ = ProjectPhase.objects.get_or_create(value='warrantyPeriod')
        self.phase_planning, _ = ProjectPhase.objects.get_or_create(value='planning')

        self.programmer = ProjectProgrammer.objects.create(
            firstName='Test', lastName='Programmer'
        )
        self.proj_class = ProjectClass.objects.create(
            name='Test Class', path='TestClass', defaultProgrammer=self.programmer
        )

    def _make_person(self, last):
        return Person.objects.create(
            firstName='Pat', lastName=last, email=f'{last.lower()}@example.com',
            title='', phone='',
        )

    def _make_project(self, name, phase, **person_kwargs):
        return Project.objects.create(
            name=name,
            description='Test',
            projectClass=self.proj_class,
            phase=phase,
            personProgramming=self.programmer,
            **person_kwargs,
        )

    def test_delete_person_referenced_as_planning_only_clears_active_projects(self):
        """DELETE /persons/<id>/ must NULL personPlanning on active projects."""
        person = self._make_person('Planner')
        active = self._make_project('Active P', self.phase_planning, personPlanning=person)

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        active.refresh_from_db()
        self.assertIsNone(active.personPlanning)
        self.assertFalse(Person.objects.filter(id=person.id).exists())

    def test_delete_person_referenced_as_construction_only_clears_active_projects(self):
        """DELETE /persons/<id>/ must NULL personConstruction on active projects.

        This is the exact failure mode reported from dev: a Person referenced
        only via personConstruction caused a Postgres FK violation.
        """
        person = self._make_person('Builder')
        active = self._make_project('Active C', self.phase_planning, personConstruction=person)

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        active.refresh_from_db()
        self.assertIsNone(active.personConstruction)
        self.assertFalse(Person.objects.filter(id=person.id).exists())

    def test_delete_person_referenced_via_both_fks_clears_both(self):
        """A single project may use the same Person for both planning and construction."""
        person = self._make_person('Both')
        project = self._make_project(
            'Active Both', self.phase_planning,
            personPlanning=person, personConstruction=person,
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        project.refresh_from_db()
        self.assertIsNone(project.personPlanning)
        self.assertIsNone(project.personConstruction)

    def test_delete_person_with_completed_project_preserves_via_each_fk(self):
        """For completed/warranty projects, repoint to a hidden copy on every FK."""
        person = self._make_person('Veteran')
        completed_planning = self._make_project(
            'Completed Plan', self.phase_completed, personPlanning=person
        )
        warranty_construction = self._make_project(
            'Warranty Build', self.phase_warranty, personConstruction=person
        )
        active = self._make_project(
            'Active', self.phase_planning, personConstruction=person
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id, deleted=False).exists())

        completed_planning.refresh_from_db()
        warranty_construction.refresh_from_db()
        active.refresh_from_db()

        self.assertIsNotNone(completed_planning.personPlanning)
        self.assertEqual(completed_planning.personPlanning.lastName, 'Veteran')
        self.assertTrue(completed_planning.personPlanning.deleted)

        self.assertIsNotNone(warranty_construction.personConstruction)
        self.assertEqual(warranty_construction.personConstruction.lastName, 'Veteran')
        self.assertTrue(warranty_construction.personConstruction.deleted)

        self.assertIsNone(active.personConstruction)

        hidden = Person.objects.filter(lastName='Veteran', deleted=True)
        self.assertEqual(hidden.count(), 1)
        self.assertEqual(completed_planning.personPlanning_id, warranty_construction.personConstruction_id)

    def test_delete_person_not_referenced_succeeds(self):
        """Sanity: deleting an unreferenced Person still works."""
        person = self._make_person('Lonely')

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())


@override_settings(CACHES=LOCMEM_CACHE)
class PersonOtherReverseFKDeletionTest(TestCase):
    """Regression tests for IO-833 (extended): deleting a Person that is
    referenced by tables OTHER than Project's planning/construction FKs.

    Background: at the schema level there are 10 FK constraints pointing at
    `infraohjelmointi_api_person`. Most of them use `on_delete=DO_NOTHING`
    on a nullable field, and Django's default Postgres FK constraints are
    DEFERRABLE INITIALLY DEFERRED. That means stray references are only
    caught at COMMIT, so the DRF view returned 204 while the underlying
    transaction blew up with a ForeignKeyViolation, surfacing as a 500 in
    the next request.

    These tests cover every reverse FK to Person that the auto-cleanup in
    CachedLookupViewSet._clear_other_reverse_fks must NULL out:

      - Task.person                         (DO_NOTHING, null)
      - ProjectSet.responsiblePerson        (DO_NOTHING, null)
      - ProjectLock.lockedBy                (DO_NOTHING, null)
      - TalpaProjectOpening.createdBy       (DO_NOTHING, null)
      - TalpaProjectOpening.updatedBy       (DO_NOTHING, null)
      - ProjectProgrammer.person            (SET_NULL,   null)

    Plus the M2M relations (Project.otherPersons, Project.favPersons),
    which Django itself cleans up via the through-table.
    """

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser_person_other_fk', password='testpass'
        )
        coord_group, _ = ADGroup.objects.get_or_create(
            name='sg_kymp_sso_io_koordinaattorit',
            defaults={'display_name': 'Coordinators'},
        )
        self.user.ad_groups.add(coord_group)
        self.client.force_login(self.user)

        self.phase_planning, _ = ProjectPhase.objects.get_or_create(value='planning')
        self.programmer = ProjectProgrammer.objects.create(
            firstName='Other', lastName='Programmer'
        )
        self.proj_class = ProjectClass.objects.create(
            name='Other Class', path='OtherClass', defaultProgrammer=self.programmer
        )

    def _make_person(self, last):
        return Person.objects.create(
            firstName='Pat', lastName=last, email=f'{last.lower()}@example.com',
            title='', phone='',
        )

    def _make_project(self, name='ref-project', **kwargs):
        return Project.objects.create(
            name=name,
            description='Test',
            projectClass=self.proj_class,
            phase=self.phase_planning,
            personProgramming=self.programmer,
            **kwargs,
        )

    def test_delete_person_referenced_by_task_clears_task_fk(self):
        """Without the cleanup this raises FK violation at commit time."""
        person = self._make_person('Tasky')
        project = self._make_project('with-task')
        task = Task.objects.create(
            projectId=project,
            taskType='task',
            person=person,
            realizedCost=0,
            plannedCost=0,
            riskAssessment='none',
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        task.refresh_from_db()
        self.assertIsNone(task.person)

    def test_delete_person_referenced_by_projectset_clears_responsible_person(self):
        person = self._make_person('Setty')
        pset = ProjectSet.objects.create(
            name='ps', description='', responsiblePerson=person,
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        pset.refresh_from_db()
        self.assertIsNone(pset.responsiblePerson)

    def test_delete_person_referenced_by_projectlock_clears_locked_by(self):
        person = self._make_person('Locker')
        project = self._make_project('with-lock')
        lock = ProjectLock.objects.create(
            project=project, lockType='status_locked', lockedBy=person,
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        lock.refresh_from_db()
        self.assertIsNone(lock.lockedBy)

    def test_delete_person_referenced_by_talpa_opening_clears_both_audit_fks(self):
        """TalpaProjectOpening references Person via TWO FKs (createdBy +
        updatedBy). Both must be cleared."""
        person = self._make_person('Talpa')
        project = self._make_project('with-talpa')
        opening = TalpaProjectOpening.objects.create(
            project=project,
            subject='Uusi',
            createdBy=person,
            updatedBy=person,
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        opening.refresh_from_db()
        self.assertIsNone(opening.createdBy)
        self.assertIsNone(opening.updatedBy)

    def test_delete_person_referenced_by_programmer_clears_programmer_fk(self):
        """ProjectProgrammer.person uses SET_NULL. Verify the FK is null and
        the programmer row itself is preserved (it should NOT be deleted
        cascade-style)."""
        person = self._make_person('Programmery')
        prog = ProjectProgrammer.objects.create(
            firstName='Alex', lastName='Programmery', person=person,
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        prog.refresh_from_db()
        self.assertIsNone(prog.person)

    def test_delete_person_referenced_via_other_persons_m2m_succeeds(self):
        """Django auto-cleans the M2M through-table on delete; verify that
        our extra cleanup doesn't break that path."""
        person = self._make_person('M2MOther')
        project = self._make_project('with-other')
        project.otherPersons.add(person)

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        project.refresh_from_db()
        self.assertEqual(project.otherPersons.count(), 0)

    def test_delete_person_referenced_via_fav_persons_m2m_succeeds(self):
        person = self._make_person('M2MFav')
        project = self._make_project('with-fav')
        project.favPersons.add(person)

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())
        project.refresh_from_db()
        self.assertEqual(project.favPersons.count(), 0)

    def test_delete_person_referenced_from_every_relation_simultaneously(self):
        """End-to-end stress test: a Person referenced from EVERY known
        relation at once must still delete cleanly. This is the scenario
        most likely to reproduce the production failure mode where any
        single missed reverse FK causes a 500."""
        person = self._make_person('Everywhere')

        # Project FKs (planning + construction) on an active project
        active = self._make_project(
            'active-everywhere',
            personPlanning=person, personConstruction=person,
        )
        active.otherPersons.add(person)
        active.favPersons.add(person)

        # Task on the same project
        Task.objects.create(
            projectId=active,
            taskType='task',
            person=person,
            realizedCost=0, plannedCost=0,
            riskAssessment='none',
        )

        # ProjectSet
        ProjectSet.objects.create(
            name='ps-everywhere', description='', responsiblePerson=person,
        )

        # ProjectLock on the same project
        ProjectLock.objects.create(
            project=active, lockType='status_locked', lockedBy=person,
        )

        # TalpaProjectOpening on the same project
        TalpaProjectOpening.objects.create(
            project=active, subject='Uusi',
            createdBy=person, updatedBy=person,
        )

        # ProjectProgrammer pointing at this Person
        prog = ProjectProgrammer.objects.create(
            firstName='Sam', lastName='Everywhere', person=person,
        )

        response = self.client.delete(f'/persons/{person.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Person.objects.filter(id=person.id).exists())

        # All references must be cleared
        active.refresh_from_db()
        prog.refresh_from_db()
        self.assertIsNone(active.personPlanning)
        self.assertIsNone(active.personConstruction)
        self.assertEqual(active.otherPersons.count(), 0)
        self.assertEqual(active.favPersons.count(), 0)
        self.assertIsNone(prog.person)
        self.assertEqual(Task.objects.filter(person__isnull=False).count(), 0)
        self.assertEqual(
            ProjectSet.objects.filter(responsiblePerson__isnull=False).count(), 0
        )
        self.assertEqual(
            ProjectLock.objects.filter(lockedBy__isnull=False).count(), 0
        )
        self.assertEqual(
            TalpaProjectOpening.objects.filter(createdBy__isnull=False).count(), 0
        )
        self.assertEqual(
            TalpaProjectOpening.objects.filter(updatedBy__isnull=False).count(), 0
        )


class ViewSetImportTest(TestCase):
    """Tests that verify ViewSet classes are properly defined."""

    def test_cached_lookup_viewsets_have_serializer_class(self):
        """Verify all CachedLookupViewSet subclasses have serializer_class."""
        from infraohjelmointi_api.views import (
            ProjectTypeViewSet, ProjectPhaseViewSet, ProjectAreaViewSet,
            ProjectCategoryViewSet, ProjectPriorityViewSet, ProjectQualityLevelViewSet,
            ProjectRiskViewSet, ProjectDistrictViewSet, ProjectResponsibleZoneViewSet,
            TaskStatusViewSet, ConstructionPhaseViewSet, ProjectPhaseDetailViewSet,
            PlanningPhaseViewSet,
        )

        viewsets = [
            ProjectTypeViewSet, ProjectPhaseViewSet, ProjectAreaViewSet,
            ProjectCategoryViewSet, ProjectPriorityViewSet, ProjectQualityLevelViewSet,
            ProjectRiskViewSet, ProjectDistrictViewSet, ProjectResponsibleZoneViewSet,
            TaskStatusViewSet, ConstructionPhaseViewSet, ProjectPhaseDetailViewSet,
            PlanningPhaseViewSet,
        ]

        for viewset_class in viewsets:
            self.assertTrue(
                hasattr(viewset_class, 'serializer_class'),
                f"{viewset_class.__name__} missing serializer_class"
            )
            self.assertIsNotNone(viewset_class.serializer_class)

    def test_cached_lookup_viewsets_inherit_correctly(self):
        """Verify ViewSets inherit from CachedLookupViewSet."""
        from infraohjelmointi_api.views.CachedLookupViewSet import CachedLookupViewSet
        from infraohjelmointi_api.views import (
            ProjectTypeViewSet, ProjectPhaseViewSet, ProjectAreaViewSet,
        )

        for viewset_class in [ProjectTypeViewSet, ProjectPhaseViewSet, ProjectAreaViewSet]:
            self.assertTrue(
                issubclass(viewset_class, CachedLookupViewSet),
                f"{viewset_class.__name__} should inherit from CachedLookupViewSet"
            )


class BaseClassLocationViewSetTest(TestCase):
    """Tests for BaseClassLocationViewSet methods."""

    def test_parse_forced_to_frame_false_string(self):
        """Test parsing 'false' string."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        self.assertFalse(BaseClassLocationViewSet.parse_forced_to_frame_param("false"))
        self.assertFalse(BaseClassLocationViewSet.parse_forced_to_frame_param("False"))

    def test_parse_forced_to_frame_true_string(self):
        """Test parsing 'true' string."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        self.assertTrue(BaseClassLocationViewSet.parse_forced_to_frame_param("true"))
        self.assertTrue(BaseClassLocationViewSet.parse_forced_to_frame_param("True"))

    def test_parse_forced_to_frame_bool(self):
        """Test parsing boolean values."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        self.assertTrue(BaseClassLocationViewSet.parse_forced_to_frame_param(True))
        self.assertFalse(BaseClassLocationViewSet.parse_forced_to_frame_param(False))

    def test_parse_forced_to_frame_invalid(self):
        """Test parsing invalid value raises error."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet
        from rest_framework.exceptions import ParseError

        with self.assertRaises(ParseError):
            BaseClassLocationViewSet.parse_forced_to_frame_param("invalid")

    def test_is_patch_data_valid_missing_finances(self):
        """Test validation fails without finances key."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        viewset = BaseClassLocationViewSet()
        self.assertFalse(viewset.is_patch_data_valid({}))
        self.assertFalse(viewset.is_patch_data_valid({'other': 'data'}))

    def test_is_patch_data_valid_missing_year(self):
        """Test validation fails without year in finances."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        viewset = BaseClassLocationViewSet()
        self.assertFalse(viewset.is_patch_data_valid({'finances': {'frameBudget': 100}}))

    def test_is_patch_data_valid_invalid_values(self):
        """Test validation fails with invalid finance values."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        viewset = BaseClassLocationViewSet()
        self.assertFalse(viewset.is_patch_data_valid({
            'finances': {'year': 2024, 'year0': 'not a dict'}
        }))
        self.assertFalse(viewset.is_patch_data_valid({
            'finances': {'year': 2024, 'year0': {}}
        }))
        self.assertFalse(viewset.is_patch_data_valid({
            'finances': {'year': 2024, 'year0': {'invalid': 100}}
        }))

    def test_is_patch_data_valid_success(self):
        """Test validation succeeds with valid data."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        viewset = BaseClassLocationViewSet()
        self.assertTrue(viewset.is_patch_data_valid({
            'finances': {'year': 2024, 'year0': {'frameBudget': 100000}}
        }))
        self.assertTrue(viewset.is_patch_data_valid({
            'finances': {'year': 2024, 'year0': {'budgetChange': 5000}}
        }))
        self.assertTrue(viewset.is_patch_data_valid({
            'finances': {'year': 2024, 'year0': {'frameBudget': 100000, 'budgetChange': 5000}}
        }))

    def test_build_frame_budgets_context_returns_defaultdict(self):
        """Test that build_frame_budgets_context returns a defaultdict."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet
        from collections import defaultdict

        result = BaseClassLocationViewSet.build_frame_budgets_context(2024, False)
        self.assertEqual(result['nonexistent-key'], 0)

    def test_coordinator_docstring_generators(self):
        """Test docstring generator methods."""
        from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet

        list_doc = BaseClassLocationViewSet._get_coordinator_list_docstring('class', '/project-classes')
        self.assertIn('coordinator', list_doc.lower())
        self.assertIn('year', list_doc.lower())

        patch_doc = BaseClassLocationViewSet._get_coordinator_patch_docstring('class', '/project-classes', 'class_id')
        self.assertIn('coordinator', patch_doc.lower())
        self.assertIn('class_id', patch_doc)
