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
import signal
from typing import Optional, Any

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Timeout exception for cache operations"""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout"""
    raise TimeoutError("Cache operation timed out")


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
    _max_failures = 1  # Disable immediately on first failure
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
        # Try to re-enable cache if Redis is back online
        if cls._cache_permanently_disabled:
            cls._try_re_enable_cache()
            if cls._cache_permanently_disabled:
                return True
        
        if time.time() < cls._cache_disabled_until:
            return True
        if cls._cache_disabled_until > 0:
            cls._cache_failures = 0
            cls._cache_disabled_until = 0
            logger.info("Cache circuit breaker reset, re-enabling cache")
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
        Check if Redis is available by testing connection directly.
        Returns True if Redis is available, False otherwise.
        
        Note: If Redis was unavailable at startup, we're using DummyCache backend
        and cannot switch to Redis without app restart. This check is mainly useful
        for detecting when Redis comes back after runtime failures.
        """
        try:
            from django.conf import settings
            REDIS_URL = getattr(settings, 'REDIS_URL', None)
            if not REDIS_URL:
                return False
            
            # Check if we're using Redis backend (not DummyCache)
            cache_backend = settings.CACHES['default']['BACKEND']
            if 'dummy' in cache_backend.lower():
                # We're using DummyCache - Redis was unavailable at startup
                # We can detect if Redis is back, but can't use it without restart
                # So we'll still return False to keep cache disabled
                # (User needs to restart app to actually use Redis)
                return False
            
            # We're using Redis backend - test if it's actually available
            # Test Redis connection directly
            import socket
            from urllib.parse import urlparse
            
            parsed = urlparse(REDIS_URL)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
            
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(0.3)
            result = test_socket.connect_ex((host, port))
            
            if result == 0:
                # Test if Redis actually responds to commands
                try:
                    test_socket.settimeout(0.2)
                    test_socket.sendall(b'PING\r\n')
                    response = test_socket.recv(1024)
                    test_socket.close()
                    if b'PONG' in response or b'+PONG' in response:
                        return True
                except Exception:
                    test_socket.close()
                    return False
            else:
                test_socket.close()
                return False
            
            return False
        except Exception:
            return False
    
    @classmethod
    def _try_re_enable_cache(cls):
        """
        Periodically check if Redis is back online and re-enable cache if available.
        
        This allows cache to recover without app restart in these scenarios:
        - Redis was available at startup but failed at runtime (circuit breaker)
        - Redis comes back after temporary outage
        
        Note: If Redis was unavailable at startup, we're using DummyCache backend
        and cannot switch to Redis without app restart. Cache will remain disabled.
        """
        current_time = time.time()
        if current_time - cls._last_redis_check < cls._redis_check_interval:
            return False  # Don't check too frequently
        
        cls._last_redis_check = current_time
        
        if cls._cache_permanently_disabled:
            if cls._check_redis_availability():
                # Check if we're actually using Redis backend (not DummyCache)
                from django.conf import settings
                cache_backend = settings.CACHES['default']['BACKEND']
                if 'dummy' in cache_backend.lower():
                    # Redis is back but we're using DummyCache - need app restart
                    logger.warning("Redis is back online but app is using DummyCache backend. "
                                  "Restart app to enable Redis cache.")
                    return False
                
                # Redis is back and we're using Redis backend - re-enable cache
                cls._cache_permanently_disabled = False
                cls._cache_failures = 0
                cls._cache_disabled_until = 0
                logger.info("Redis is back online - cache re-enabled")
                return True
        return False
    
    @classmethod
    def _record_cache_failure(cls):
        """Record a cache failure and disable cache if threshold reached"""
        cls._cache_failures += 1
        if cls._cache_failures >= cls._max_failures:
            cls._cache_disabled_until = time.time() + cls._disable_duration
            logger.warning(f"Cache disabled for {cls._disable_duration}s after {cls._cache_failures} failures")
    
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
            timeout: Maximum time to wait in seconds
            
        Returns:
            Cached value or None
        """
        if cls._is_cache_disabled():
            return None
        
        try:
            # Try signal-based timeout (Unix/Docker)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(int(timeout) + 1)
                try:
                    result = cache.get(cache_key)
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                    cls._record_cache_success()
                    return result
                except TimeoutError:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                    cls._record_cache_failure()
                    logger.warning(f"Cache get timed out, disabling cache")
                    return None
            else:
                # Windows or signal not available - fall back to try-except
                result = cache.get(cache_key)
                cls._record_cache_success()
                return result
        except Exception as e:
            cls._record_cache_failure()
            logger.warning(f"Cache get failed: {e}, disabling cache")
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
            return
        
        try:
            # Try signal-based timeout (Unix/Docker)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(1)
                try:
                    cache.set(cache_key, data, timeout)
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                    cls._record_cache_success()
                except TimeoutError:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                    cls._record_cache_failure()
                    logger.warning(f"Cache set timed out, disabling cache")
            else:
                # Windows or signal not available - fall back to try-except
                cache.set(cache_key, data, timeout)
                cls._record_cache_success()
        except Exception as e:
            cls._record_cache_failure()
            logger.warning(f"Cache set failed: {e}, disabling cache")
    
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
        return cls._safe_cache_get(cache_key)
    
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
        return cls._safe_cache_get(cache_key)
    
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

