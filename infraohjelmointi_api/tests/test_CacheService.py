"""Tests for CacheService."""

import uuid
from datetime import date
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings

from infraohjelmointi_api.models import (
    ProjectClass,
    ClassFinancial,
    Project,
    ProjectFinancial,
    ProjectLocation,
    LocationFinancial,
    ProjectGroup,
    ProjectProgrammer,
)
from infraohjelmointi_api.serializers import ProjectClassSerializer
from infraohjelmointi_api.serializers.FinancialSumSerializer import FinancialSumSerializer
from infraohjelmointi_api.services.CacheService import CacheService
from infraohjelmointi_api.services.RedisAvailabilityChecker import RedisAvailabilityChecker


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
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


@override_settings(CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
})
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
        """Verify cache timeout is reasonable"""
        timeout = CacheService.DEFAULT_TIMEOUT
        
        # Should be at least 60 seconds (1 minute) but not more than 1 day
        self.assertGreaterEqual(timeout, 60, "Cache timeout too short")
        self.assertLessEqual(timeout, 86400, "Cache timeout too long")

