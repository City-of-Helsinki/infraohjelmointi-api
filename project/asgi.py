import os
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from . import consumers


urlRouter = URLRouter(
    [
        path(
            "events/",
            AuthMiddlewareStack(
                URLRouter([path("", consumers.CostomEventConsumer.as_asgi())])
            ),
            {"channels": ["finance", "project"]},
        ),
        re_path(r"", get_asgi_application()),
    ]
)
application = ProtocolTypeRouter(
    {
        "http": urlRouter,
        "https": urlRouter,
    }
)
