from rest_framework import routers
from infraohjelmointi_api import views

router = routers.DefaultRouter()

def api_router():
    router.register(
        r"api",
        views.ApiViewSet,
        basename="api",
    )

    router.register(
        r"api/project",
        views.ApiProjectViewSet,
        basename="apiProject"
    )

    return router
