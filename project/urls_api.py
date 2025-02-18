from rest_framework import routers
from infraohjelmointi_api import views

router = routers.DefaultRouter()

def api_router():
    router.register(
        r"api/classes",
        views.ApiClassesViewSet,
        basename="apiClasses"
    )

    router.register(
        r"api/districts",
        views.ApiDistrictsViewSet,
        basename="apiDistricts"
    )

    router.register(
        r"api/groups",
        views.ApiGroupsViewSet,
        basename="apiGroups"
    )

    router.register(
        r"api/locations",
        views.ApiLocationsViewSet,
        basename="apiLocations"
    )

    router.register(
        r"api/projects",
        views.ApiProjectsViewSet,
        basename="apiProject"
    )

    return router
