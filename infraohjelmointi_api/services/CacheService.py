"""
CacheService for caching expensive calculations.
Uses Django's cache framework with Redis in production.
"""

import hashlib
import json
import logging
import sys
import time
from datetime import date
from typing import Optional, Any, List

from django.conf import settings
from django.core.cache import cache

from .RedisAvailabilityChecker import RedisAvailabilityChecker

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching expensive calculations with circuit breaker pattern."""

    DEFAULT_TIMEOUT = getattr(settings, 'FINANCIAL_CACHE_TIMEOUT', 43200)
    LOOKUP_TIMEOUT = 3600  # 1 hour for lookup tables
    FINANCIAL_SUM_PREFIX = 'financial_sum'
    FRAME_BUDGET_PREFIX = 'frame_budget'
    LOOKUP_PREFIX = 'lookup'

    _cache_failures = 0
    _cache_disabled_until = 0
    _max_failures = 3
    _disable_duration = 300
    _cache_permanently_disabled = False
    _last_redis_check = 0
    _redis_check_interval = 60
    _last_redis_availability_check = 0
    _redis_availability_check_interval = 5

    @staticmethod
    def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
        key_data = {'args': args, 'kwargs': sorted(kwargs.items())}
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]
        return f"{prefix}:{key_hash}"

    @staticmethod
    def _is_test_environment() -> bool:
        return 'test' in sys.argv or (sys.argv and 'pytest' in sys.argv[0])

    @classmethod
    def _is_cache_disabled(cls) -> bool:
        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            return True

        if cls._is_test_environment() and 'redis' in cache_backend.lower():
            if not getattr(settings, 'REDIS_AVAILABLE', False):
                return True

        if cls._cache_permanently_disabled:
            cls._try_re_enable_cache()
            if cls._cache_permanently_disabled:
                return True

        if cls._cache_disabled_until > 0:
            if time.time() < cls._cache_disabled_until:
                cls._try_re_enable_cache()
                return True
            else:
                cls._cache_failures = 0
                cls._cache_disabled_until = 0
        return False

    @classmethod
    def disable_cache_permanently(cls):
        cls._cache_permanently_disabled = True
        cls._last_redis_check = time.time()
        logger.warning("Cache permanently disabled - Redis unavailable")

    @classmethod
    def _check_redis_availability(cls) -> bool:
        return RedisAvailabilityChecker.is_available()

    @classmethod
    def _try_re_enable_cache(cls):
        current_time = time.time()
        if current_time - cls._last_redis_check < cls._redis_check_interval:
            return

        cls._last_redis_check = current_time

        if cls._check_redis_availability():
            cache_backend = settings.CACHES['default']['BACKEND']
            if 'dummy' in cache_backend.lower():
                return

            if cls._cache_permanently_disabled or cls._cache_disabled_until > 0:
                cls._cache_permanently_disabled = False
                cls._cache_failures = 0
                cls._cache_disabled_until = 0
                logger.debug("Redis is back online - cache re-enabled")

    @classmethod
    def _record_cache_failure(cls):
        cls._cache_failures += 1
        if cls._cache_failures >= cls._max_failures:
            cls._cache_disabled_until = time.time() + cls._disable_duration
            logger.warning(f"Cache circuit breaker triggered after {cls._cache_failures} failures")

    @classmethod
    def _record_cache_success(cls):
        if cls._cache_failures > 0:
            cls._cache_failures = 0

    @classmethod
    def _safe_cache_get(cls, cache_key: str) -> Optional[Any]:
        if cls._is_cache_disabled():
            return None

        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            return None

        try:
            result = cache.get(cache_key)
            if result is not None:
                cls._record_cache_success()
            return result
        except Exception as e:
            cls._record_cache_failure()
            logger.warning(f"Cache get failed: {e}")
            return None

    @classmethod
    def _safe_cache_set(cls, cache_key: str, data: Any, timeout: int):
        if cls._is_cache_disabled():
            return

        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            return

        try:
            result = cache.set(cache_key, data, timeout)
            if result:
                cls._record_cache_success()
            else:
                ignore_exceptions = settings.CACHES['default'].get('OPTIONS', {}).get('IGNORE_EXCEPTIONS', False)
                is_redis = 'redis' in cache_backend.lower()

                if is_redis and ignore_exceptions:
                    current_time = time.time()
                    if (current_time - cls._last_redis_availability_check) >= cls._redis_availability_check_interval:
                        cls._last_redis_availability_check = current_time
                        if not cls._check_redis_availability():
                            cls._record_cache_failure()
                elif 'locmem' not in cache_backend.lower():
                    cls._record_cache_failure()
        except Exception as e:
            cls._record_cache_failure()
            logger.warning(f"Cache set failed: {e}")

    @classmethod
    def _safe_cache_delete(cls, cache_key: str) -> None:
        if cls._is_cache_disabled():
            return

        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            return

        try:
            cache.delete(cache_key)
        except Exception:
            pass

    @classmethod
    def get_financial_sum(cls, instance_id: str, instance_type: str, year: int,
                          for_frame_view: bool, for_coordinator: bool = False) -> Optional[dict]:
        cache_key = cls._generate_cache_key(
            cls.FINANCIAL_SUM_PREFIX,
            instance_id=str(instance_id),
            instance_type=instance_type,
            year=year,
            for_frame_view=for_frame_view,
            for_coordinator=for_coordinator
        )
        return cls._safe_cache_get(cache_key)

    @classmethod
    def set_financial_sum(cls, instance_id: str, instance_type: str, year: int,
                          for_frame_view: bool, data: dict,
                          for_coordinator: bool = False, timeout: Optional[int] = None) -> None:
        cache_key = cls._generate_cache_key(
            cls.FINANCIAL_SUM_PREFIX,
            instance_id=str(instance_id),
            instance_type=instance_type,
            year=year,
            for_frame_view=for_frame_view,
            for_coordinator=for_coordinator
        )
        cls._safe_cache_set(cache_key, data, timeout or cls.DEFAULT_TIMEOUT)

    @classmethod
    def get_frame_budgets(cls, year: int, for_frame_view: bool) -> Optional[dict]:
        cache_key = cls._generate_cache_key(
            cls.FRAME_BUDGET_PREFIX,
            year=year,
            for_frame_view=for_frame_view
        )
        return cls._safe_cache_get(cache_key)

    @classmethod
    def set_frame_budgets(cls, year: int, for_frame_view: bool,
                          data: dict, timeout: Optional[int] = None) -> None:
        cache_key = cls._generate_cache_key(
            cls.FRAME_BUDGET_PREFIX,
            year=year,
            for_frame_view=for_frame_view
        )
        cls._safe_cache_set(cache_key, data, timeout or cls.DEFAULT_TIMEOUT)

    @classmethod
    def invalidate_financial_sum(cls, instance_id: str, instance_type: str) -> None:
        if cls._is_cache_disabled():
            return

        try:
            current_year = date.today().year
            for year_offset in range(-2, 13):
                year = current_year + year_offset
                for for_frame_view in [True, False]:
                    for for_coordinator in [True, False]:
                        cache_key = cls._generate_cache_key(
                            cls.FINANCIAL_SUM_PREFIX,
                            instance_id=str(instance_id),
                            instance_type=instance_type,
                            year=year,
                            for_frame_view=for_frame_view,
                            for_coordinator=for_coordinator
                        )
                        cls._safe_cache_delete(cache_key)
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

    @classmethod
    def invalidate_frame_budgets(cls, year: Optional[int] = None) -> None:
        if cls._is_cache_disabled():
            return

        try:
            if year is not None:
                for for_frame_view in [True, False]:
                    cache_key = cls._generate_cache_key(
                        cls.FRAME_BUDGET_PREFIX,
                        year=year,
                        for_frame_view=for_frame_view
                    )
                    cls._safe_cache_delete(cache_key)
            else:
                current_year = date.today().year
                for year_offset in range(-2, 13):
                    cls.invalidate_frame_budgets(current_year + year_offset)
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

    @classmethod
    def clear_all(cls) -> None:
        if cls._is_cache_disabled():
            return

        try:
            cache.clear()
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

    # Lookup table caching
    @classmethod
    def get_lookup(cls, table_name: str) -> Optional[List[dict]]:
        cache_key = f"{cls.LOOKUP_PREFIX}:{table_name}"
        return cls._safe_cache_get(cache_key)

    @classmethod
    def set_lookup(cls, table_name: str, data: List[dict]) -> None:
        cache_key = f"{cls.LOOKUP_PREFIX}:{table_name}"
        cls._safe_cache_set(cache_key, data, cls.LOOKUP_TIMEOUT)

    @classmethod
    def invalidate_lookup(cls, table_name: str) -> None:
        cache_key = f"{cls.LOOKUP_PREFIX}:{table_name}"
        cls._safe_cache_delete(cache_key)
