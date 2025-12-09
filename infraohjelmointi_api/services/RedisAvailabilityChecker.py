"""Redis availability checker with cached results."""

import concurrent.futures
import logging
import socket
import sys
import time
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger(__name__)


class RedisAvailabilityChecker:
    """Checks Redis availability and caches the result."""
    
    _is_available = None
    _last_check = 0
    _check_interval = 60
    _check_timeout = 2.0
    
    @classmethod
    def _is_test_environment(cls) -> bool:
        return 'test' in sys.argv or ('pytest' in sys.argv[0] if sys.argv else False)
    
    @classmethod
    def is_available(cls) -> bool:
        current_time = time.time()
        
        if cls._is_available is not None and current_time < cls._last_check + cls._check_interval:
            return cls._is_available
        
        cls._last_check = current_time
        was_available = cls._is_available
        cls._is_available = cls._check_redis_connection()
        
        if was_available != cls._is_available:
            logger.info(f"Redis is {'now available' if cls._is_available else 'not available'}")
        elif was_available is None:
            logger.info(f"Redis is {'available' if cls._is_available else 'not available'}")
        
        return cls._is_available
    
    @classmethod
    def _check_redis_connection(cls) -> bool:
        try:
            REDIS_URL = getattr(settings, 'REDIS_URL', None)
            if not REDIS_URL:
                return False

            cache_backend = settings.CACHES['default']['BACKEND']
            if 'dummy' in cache_backend.lower():
                return False

            parsed = urlparse(REDIS_URL)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379

            if cls._is_test_environment():
                return cls._check_with_timeout(host, port)

            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(cls._check_timeout)
            result = test_socket.connect_ex((host, port))
            test_socket.close()
            return result == 0
        except Exception:
            return False
    
    @classmethod
    def _check_with_timeout(cls, host: str, port: int) -> bool:
        """Check connection with thread-based timeout to handle DNS hanging."""
        def try_connect():
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(0.5)
                result = test_socket.connect_ex((host, port))
                test_socket.close()
                return result == 0
            except Exception:
                return False
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(try_connect)
                return future.result(timeout=1.0)
        except (concurrent.futures.TimeoutError, Exception):
            return False
    
    @classmethod
    def reset(cls):
        cls._is_available = None
        cls._last_check = 0
