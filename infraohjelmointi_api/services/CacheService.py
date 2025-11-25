"""
CacheService for Financial Calculations

Provides caching layer for expensive financial calculations to improve performance.
Uses Django's cache framework (configured to use Redis in production).

IMPORTANT: Cache is ONLY enabled when Redis is available. If Redis is unavailable at startup,
cache is permanently disabled (using DummyCache backend) to ensure consistency across pods
and prevent any cache-related issues. The application will work without caching, but without
performance benefits.

All cache operations are wrapped in try-except with timeouts to ensure the application continues
to work even if Redis fails at runtime. Circuit breaker disables cache after failures to prevent
blocking.
"""

from django.core.cache import cache
from django.conf import settings
from datetime import date
import hashlib
import json
import logging
import time
from typing import Optional, Any
from .RedisAvailabilityChecker import RedisAvailabilityChecker

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching expensive calculations"""
    
    # Cache timeout in seconds (5 minutes default)
    DEFAULT_TIMEOUT = getattr(settings, 'FINANCIAL_CACHE_TIMEOUT', 300)
    
    # Cache key prefixes
    FINANCIAL_SUM_PREFIX = 'financial_sum'
    FRAME_BUDGET_PREFIX = 'frame_budget'
    
    # Circuit breaker: disable cache after consecutive failures
    _cache_failures = 0
    _cache_disabled_until = 0
    _max_failures = 3  # Allow 3 failures before disabling (was 1 - too aggressive)
    _disable_duration = 300  # Disable for 5 minutes after failures
    _cache_permanently_disabled = False  # Set to True if Redis is unavailable at startup
    _last_redis_check = 0  # Timestamp of last Redis availability check
    _redis_check_interval = 60  # Check Redis availability every 60 seconds
    
    @staticmethod
    def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key based on prefix and parameters
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            str: Unique cache key
        """
        # Create a deterministic string from all arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())  # Sort for consistency
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        
        # Hash to keep key length manageable
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    @classmethod
    def _is_cache_disabled(cls) -> bool:
        """Check if cache should be disabled due to circuit breaker"""
        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            return True

        if cls._cache_permanently_disabled:
            cls._try_re_enable_cache()
            if cls._cache_permanently_disabled:
                logger.debug("Cache disabled: permanently disabled")
                return True

        if cls._cache_disabled_until > 0:
            current_time = time.time()
            if current_time < cls._cache_disabled_until:
                remaining = int(cls._cache_disabled_until - current_time)
                logger.debug(f"Cache disabled: disabled until {cls._cache_disabled_until} ({remaining}s remaining)")
                cls._try_re_enable_cache()
                return True
            else:
                cls._cache_failures = 0
                cls._cache_disabled_until = 0
                logger.debug("Cache circuit breaker timeout expired, re-enabling cache")
        return False
    
    @classmethod
    def disable_cache_permanently(cls):
        """Permanently disable cache (call when Redis is unavailable at startup)"""
        cls._cache_permanently_disabled = True
        cls._last_redis_check = time.time()
        logger.warning("Cache permanently disabled - Redis unavailable")
    
    @classmethod
    def _check_redis_availability(cls) -> bool:
        """
        Check if Redis is available using RedisAvailabilityChecker.
        Returns True if Redis is available, False otherwise.
        """
        return RedisAvailabilityChecker.is_available()
    
    @classmethod
    def _try_re_enable_cache(cls):
        """
        Periodically check if Redis is back online and re-enable cache if available.
        This allows cache to recover without app restart.
        """
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
        """Record a cache failure and disable cache if threshold reached"""
        cls._cache_failures += 1
        if cls._cache_failures >= cls._max_failures:
            cls._cache_disabled_until = time.time() + cls._disable_duration
            logger.warning(f"Cache disabled: circuit breaker triggered after {cls._cache_failures} consecutive failures (disabled for {cls._disable_duration}s)")
    
    @classmethod
    def _record_cache_success(cls):
        """Reset failure counter on successful cache operation"""
        if cls._cache_failures > 0:
            cls._cache_failures = 0
    
    @classmethod
    def _safe_cache_get(cls, cache_key: str, timeout: float = 0.5) -> Optional[Any]:
        """
        Safely get from cache with timeout to prevent blocking

        Args:
            cache_key: Cache key to get
            timeout: Maximum time to wait in seconds (not used, Redis has built-in timeouts)

        Returns:
            Cached value or None
        """
        if cls._is_cache_disabled():
            logger.debug(f"Cache get skipped: cache disabled (circuit breaker)")
            return None

        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            logger.debug(f"Cache get skipped: using DummyCache backend")
            return None

        # Don't check Redis availability here - let django-redis handle it with IGNORE_EXCEPTIONS
        # This allows cache to work even if Redis is temporarily unavailable
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
        """
        Safely set cache with timeout to prevent blocking

        Args:
            cache_key: Cache key to set
            data: Data to cache
            timeout: Cache timeout in seconds
        """
        if cls._is_cache_disabled():
            logger.debug(f"Cache set skipped: cache disabled (circuit breaker)")
            return

        cache_backend = settings.CACHES['default']['BACKEND']
        if 'dummy' in cache_backend.lower():
            logger.debug(f"Cache set skipped: using DummyCache backend")
            return

        # Don't check Redis availability here - let django-redis handle it with IGNORE_EXCEPTIONS
        # This allows cache to work even if Redis is temporarily unavailable
        try:
            result = cache.set(cache_key, data, timeout)
            if result:
                cls._record_cache_success()
                logger.debug(f"Cache set successful: {cache_key[:60]}...")
            else:
                # With IGNORE_EXCEPTIONS=True, False is expected when Redis is unavailable
                # Don't treat it as a failure - it's graceful degradation
                # Also, LocMemCache and other backends might return False in edge cases
                ignore_exceptions = settings.CACHES['default'].get('OPTIONS', {}).get('IGNORE_EXCEPTIONS', False)
                is_locmem = 'locmem' in cache_backend.lower()
                if ignore_exceptions or is_locmem:
                    # For Redis with IGNORE_EXCEPTIONS or LocMemCache, False is acceptable
                    logger.debug(f"Cache set returned False (backend: {cache_backend.split('.')[-1]}): {cache_key[:60]}...")
                else:
                    logger.warning(f"Cache set returned False: {cache_key[:60]}...")
                    cls._record_cache_failure()
        except Exception as e:
            cls._record_cache_failure()
            logger.warning(f"Cache set failed: {cache_key[:60]}... - {e}", exc_info=False)
    
    @classmethod
    def get_financial_sum(cls, instance_id: str, instance_type: str, year: int, 
                          for_frame_view: bool, for_coordinator: bool = False) -> Optional[dict]:
        """
        Get cached financial sum calculation
        
        Args:
            instance_id: UUID of the instance (ProjectClass, ProjectLocation, or ProjectGroup)
            instance_type: Type name ('ProjectClass', 'ProjectLocation', 'ProjectGroup')
            year: Starting year for calculations
            for_frame_view: Whether this is for frame view
            for_coordinator: Whether this is for coordinator view
            
        Returns:
            dict or None: Cached financial sum data or None if not cached or on error
        """
        cache_key = cls._generate_cache_key(
            cls.FINANCIAL_SUM_PREFIX,
            instance_id=str(instance_id),
            instance_type=instance_type,
            year=year,
            for_frame_view=for_frame_view,
            for_coordinator=for_coordinator
        )
        result = cls._safe_cache_get(cache_key)
        if result is not None:
            logger.info(f"Cache HIT: financial_sum for {instance_type} {instance_id} (year={year}, frame={for_frame_view}, coordinator={for_coordinator})")
        else:
            logger.debug(f"Cache MISS: financial_sum for {instance_type} {instance_id} (year={year}, frame={for_frame_view}, coordinator={for_coordinator})")
        return result
    
    @classmethod
    def set_financial_sum(cls, instance_id: str, instance_type: str, year: int,
                          for_frame_view: bool, data: dict, 
                          for_coordinator: bool = False, timeout: Optional[int] = None) -> None:
        """
        Cache financial sum calculation
        
        Args:
            instance_id: UUID of the instance
            instance_type: Type name
            year: Starting year
            for_frame_view: Whether this is for frame view
            data: Financial sum data to cache
            for_coordinator: Whether this is for coordinator view
            timeout: Cache timeout in seconds (uses DEFAULT_TIMEOUT if None)
        """
        cache_key = cls._generate_cache_key(
            cls.FINANCIAL_SUM_PREFIX,
            instance_id=str(instance_id),
            instance_type=instance_type,
            year=year,
            for_frame_view=for_frame_view,
            for_coordinator=for_coordinator
        )
        cls._safe_cache_set(cache_key, data, timeout or cls.DEFAULT_TIMEOUT)
        logger.info(f"Cache SET: financial_sum for {instance_type} {instance_id} (year={year}, frame={for_frame_view}, coordinator={for_coordinator})")
    
    @classmethod
    def get_frame_budgets(cls, year: int, for_frame_view: bool) -> Optional[dict]:
        """
        Get cached frame budgets context
        
        Args:
            year: Year for frame budgets
            for_frame_view: Whether this is for frame view
            
        Returns:
            dict or None: Cached frame budgets or None if not cached or on error
        """
        cache_key = cls._generate_cache_key(
            cls.FRAME_BUDGET_PREFIX,
            year=year,
            for_frame_view=for_frame_view
        )
        result = cls._safe_cache_get(cache_key)
        if result is not None:
            logger.info(f"Cache HIT: frame_budgets (year={year}, frame={for_frame_view})")
        else:
            logger.debug(f"Cache MISS: frame_budgets (year={year}, frame={for_frame_view})")
        return result
    
    @classmethod
    def set_frame_budgets(cls, year: int, for_frame_view: bool, 
                          data: dict, timeout: Optional[int] = None) -> None:
        """
        Cache frame budgets context
        
        Args:
            year: Year for frame budgets
            for_frame_view: Whether this is for frame view
            data: Frame budgets data to cache
            timeout: Cache timeout in seconds
        """
        cache_key = cls._generate_cache_key(
            cls.FRAME_BUDGET_PREFIX,
            year=year,
            for_frame_view=for_frame_view
        )
        cls._safe_cache_set(cache_key, data, timeout or cls.DEFAULT_TIMEOUT)
        logger.info(f"Cache SET: frame_budgets (year={year}, frame={for_frame_view})")
    
    @classmethod
    def invalidate_financial_sum(cls, instance_id: str, instance_type: str) -> None:
        """
        Invalidate all cached financial sums for a specific instance
        
        Args:
            instance_id: UUID of the instance
            instance_type: Type name
        """
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
                        try:
                            cache.delete(cache_key)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Cache invalidation failed for financial_sum: {e}")
    
    @classmethod
    def invalidate_frame_budgets(cls, year: Optional[int] = None) -> None:
        """
        Invalidate frame budgets cache
        
        Args:
            year: Specific year to invalidate, or None to invalidate all years
        """
        try:
            if year is not None:
                for for_frame_view in [True, False]:
                    cache_key = cls._generate_cache_key(
                        cls.FRAME_BUDGET_PREFIX,
                        year=year,
                        for_frame_view=for_frame_view
                    )
                    try:
                        cache.delete(cache_key)
                    except Exception:
                        pass
            else:
                current_year = date.today().year
                for year_offset in range(-2, 13):
                    cls.invalidate_frame_budgets(current_year + year_offset)
        except Exception as e:
            logger.warning(f"Cache invalidation failed for frame_budgets: {e}")
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all caches (use with caution)"""
        try:
            cache.clear()
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")

