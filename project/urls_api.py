from rest_framework import routers
from infraohjelmointi_api import views

router = routers.DefaultRouter()

def api_router():
    router.register(
        r"api/projects",
        views.ApiProjectsViewSet,
        basename="apiProject"
    )

    router.register(
        r"api",
        views.ApiViewSet,
        basename="api",
    )

    return router
