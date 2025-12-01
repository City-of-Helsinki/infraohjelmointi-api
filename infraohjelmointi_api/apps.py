import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.serializers import register_serializer

logger = logging.getLogger(__name__)


class InfraohjelmointiApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infraohjelmointi_api"

    def ready(self):
        import infraohjelmointi_api.signals
        from infraohjelmointi_api.services.CacheService import CacheService

        register_serializer("yml", "django.core.serializers.pyyaml")

        if not getattr(settings, 'REDIS_URL', None):
            CacheService.disable_cache_permanently()
            logger.info("Cache disabled - REDIS_URL not configured")
