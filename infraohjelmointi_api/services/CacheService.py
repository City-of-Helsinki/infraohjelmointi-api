"""
CacheService for Financial Calculations

Provides caching layer for expensive financial calculations to improve performance.
Uses Django's cache framework (can be configured to use Redis in production).

Phase 1 optimization: Simple in-memory caching
Future: Migrate to Redis for distributed caching
"""

from django.core.cache import cache
from django.conf import settings
from datetime import date
import hashlib
import json
from typing import Optional, Any


class CacheService:
    """Service for caching expensive calculations"""
    
    # Cache timeout in seconds (5 minutes default)
    DEFAULT_TIMEOUT = getattr(settings, 'FINANCIAL_CACHE_TIMEOUT', 300)
    
    # Cache key prefixes
    FINANCIAL_SUM_PREFIX = 'financial_sum'
    FRAME_BUDGET_PREFIX = 'frame_budget'
    
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
            dict or None: Cached financial sum data or None if not cached
        """
        cache_key = cls._generate_cache_key(
            cls.FINANCIAL_SUM_PREFIX,
            instance_id=str(instance_id),
            instance_type=instance_type,
            year=year,
            for_frame_view=for_frame_view,
            for_coordinator=for_coordinator
        )
        
        return cache.get(cache_key)
    
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
        
        cache.set(cache_key, data, timeout or cls.DEFAULT_TIMEOUT)
    
    @classmethod
    def get_frame_budgets(cls, year: int, for_frame_view: bool) -> Optional[dict]:
        """
        Get cached frame budgets context
        
        Args:
            year: Year for frame budgets
            for_frame_view: Whether this is for frame view
            
        Returns:
            dict or None: Cached frame budgets or None if not cached
        """
        cache_key = cls._generate_cache_key(
            cls.FRAME_BUDGET_PREFIX,
            year=year,
            for_frame_view=for_frame_view
        )
        
        return cache.get(cache_key)
    
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
        
        cache.set(cache_key, data, timeout or cls.DEFAULT_TIMEOUT)
    
    @classmethod
    def invalidate_financial_sum(cls, instance_id: str, instance_type: str) -> None:
        """
        Invalidate all cached financial sums for a specific instance
        
        Args:
            instance_id: UUID of the instance
            instance_type: Type name
        """
        # Clear all variations of the cache for this instance
        current_year = date.today().year
        
        for year_offset in range(-2, 13):  # Past 2 years + next 11 years
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
                    cache.delete(cache_key)
    
    @classmethod
    def invalidate_frame_budgets(cls, year: Optional[int] = None) -> None:
        """
        Invalidate frame budgets cache
        
        Args:
            year: Specific year to invalidate, or None to invalidate all years
        """
        if year is not None:
            # Invalidate specific year
            for for_frame_view in [True, False]:
                cache_key = cls._generate_cache_key(
                    cls.FRAME_BUDGET_PREFIX,
                    year=year,
                    for_frame_view=for_frame_view
                )
                cache.delete(cache_key)
        else:
            # Invalidate all frame budget caches
            current_year = date.today().year
            for year_offset in range(-2, 13):
                cls.invalidate_frame_budgets(current_year + year_offset)
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all caches (use with caution)"""
        cache.clear()

