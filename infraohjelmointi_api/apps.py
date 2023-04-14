from django.apps import AppConfig
from django.core.serializers import register_serializer


class InfraohjelmointiApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infraohjelmointi_api'

    def ready(self):
        register_serializer('yml', 'django.core.serializers.pyyaml')
