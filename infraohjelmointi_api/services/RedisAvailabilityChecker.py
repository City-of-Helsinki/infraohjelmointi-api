"""
Redis Availability Checker

Checks if Redis is available and caches the result to avoid checking on every operation.
"""

import logging
import socket
import time
from urllib.parse import urlparse
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisAvailabilityChecker:
    """Checks Redis availability and caches the result"""
    
    _is_available = None
    _last_check = 0
    _check_interval = 60  # Check every 60 seconds
    _check_timeout = 2.0  # Socket timeout in seconds (increased for Docker networking)
    
    @classmethod
    def is_available(cls) -> bool:
        """
        Check if Redis is available.
        Caches the result for _check_interval seconds to avoid checking on every operation.
        
        Returns:
            True if Redis is available, False otherwise
        """
        current_time = time.time()
        
        if cls._is_available is not None and current_time < cls._last_check + cls._check_interval:
            return cls._is_available
        
        cls._last_check = current_time
        was_available = cls._is_available
        cls._is_available = cls._check_redis_connection()
        
        if was_available != cls._is_available:
            if cls._is_available:
                logger.info("Redis is now available")
            else:
                logger.info("Redis is not available")
        elif was_available is None:
            if cls._is_available:
                logger.info("Redis is available")
            else:
                logger.info("Redis is not available")
        
        return cls._is_available
    
    @classmethod
    def _check_redis_connection(cls) -> bool:
        """
        Check if Redis is available by testing socket connection.
        Does not use cache operations to avoid circular dependencies.
        
        Returns:
            True if Redis is available, False otherwise
        """
        try:
            REDIS_URL = getattr(settings, 'REDIS_URL', None)
            if not REDIS_URL:
                logger.debug("Redis check: REDIS_URL not configured")
                return False

            cache_backend = settings.CACHES['default']['BACKEND']
            if 'dummy' in cache_backend.lower():
                logger.debug("Redis check: Using DummyCache backend")
                return False

            parsed = urlparse(REDIS_URL)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379

            # Log the full URL being used (mask password)
            if '@' in REDIS_URL:
                # URL has password, show only the part after @
                safe_url = REDIS_URL.split('@')[-1]
                logger.debug(f"Redis check: Using REDIS_URL: redis://***@{safe_url}")
            else:
                # No password, show full URL
                logger.debug(f"Redis check: Using REDIS_URL: {REDIS_URL}")
            logger.debug(f"Redis check: Attempting connection to {host}:{port}")
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(cls._check_timeout)
            result = test_socket.connect_ex((host, port))
            test_socket.close()

            if result == 0:
                logger.debug(f"Redis check: Connection successful to {host}:{port}")
            else:
                logger.debug(f"Redis check: Connection failed to {host}:{port} (error code: {result})")
            
            return result == 0
        except Exception as e:
            logger.debug(f"Redis check: Exception during connection test: {e}")
            return False
    
    @classmethod
    def reset(cls):
        """Reset the cached availability result (force re-check on next call)"""
        cls._is_available = None
        cls._last_check = 0

