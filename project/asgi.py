import os
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django_eventstream

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

urlRouter = URLRouter(
    [
        path(
            "events/",
            AuthMiddlewareStack(URLRouter(django_eventstream.routing.urlpatterns)),
            {"channels": ["finance", "project"]},
        ),
        re_path(r"", get_asgi_application()),
    ]
)
application = ProtocolTypeRouter(
    {
        "http": urlRouter,
    }
)
