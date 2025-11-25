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
        from infraohjelmointi_api.services.CacheService import CacheService

        register_serializer("yml", "django.core.serializers.pyyaml")

        REDIS_URL = getattr(settings, 'REDIS_URL', None)
        REDIS_AVAILABLE = getattr(settings, 'REDIS_AVAILABLE', False)

        if not REDIS_URL:
            CacheService.disable_cache_permanently()
            logger.info("Cache disabled - REDIS_URL not configured")
        elif not REDIS_AVAILABLE:
            logger.debug("Redis not immediately available at startup - cache will attempt connection on first use")
