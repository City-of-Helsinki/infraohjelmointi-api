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
        r"api/hashtags",
        views.ApiHashtagsViewSet,
        basename="apiHashtags"
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

    # Talpa endpoints for Swagger documentation
    router.register(
        r"api/talpa-project-opening",
        views.TalpaProjectOpeningViewSet,
        basename="talpaProjectOpening"
    )

    router.register(
        r"api/talpa-project-types",
        views.TalpaProjectTypeViewSet,
        basename="talpaProjectTypes"
    )

    router.register(
        r"api/talpa-service-classes",
        views.TalpaServiceClassViewSet,
        basename="talpaServiceClasses"
    )

    router.register(
        r"api/talpa-asset-classes",
        views.TalpaAssetClassViewSet,
        basename="talpaAssetClasses"
    )

    router.register(
        r"api/talpa-project-ranges",
        views.TalpaProjectNumberRangeViewSet,
        basename="talpaProjectRanges"
    )

    return router
