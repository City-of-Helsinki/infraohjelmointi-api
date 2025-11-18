from django.apps import AppConfig
from django.core.serializers import register_serializer
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class InfraohjelmointiApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infraohjelmointi_api"

    def ready(self):
        import infraohjelmointi_api.signals

        register_serializer("yml", "django.core.serializers.pyyaml")
        
        # Disable cache permanently if Redis is unavailable
        # This runs after Django apps are loaded, so imports are safe
        REDIS_URL = getattr(settings, 'REDIS_URL', None)
        if REDIS_URL and not getattr(settings, 'REDIS_AVAILABLE', False):
            from infraohjelmointi_api.services.CacheService import CacheService
            CacheService.disable_cache_permanently()
            logger.warning("Cache permanently disabled - Redis unavailable at startup")
        elif not REDIS_URL:
            from infraohjelmointi_api.services.CacheService import CacheService
            CacheService.disable_cache_permanently()
            logger.info("Cache permanently disabled - Redis not configured")
