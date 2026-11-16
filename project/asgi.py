import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

# Plain Django ASGI app: django-eventstream 5 serves /events/ as an ordinary
# async-streaming view (see project/urls.py), so Channels is no longer needed.
application = get_asgi_application()
