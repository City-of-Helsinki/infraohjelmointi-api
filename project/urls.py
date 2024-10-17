"""infraohjelmointi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework import permissions
from infraohjelmointi_api import views, admin_views

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from .urls_api import api_router
apirouter = api_router()

router = routers.DefaultRouter()
router.register(r"projects", views.ProjectViewSet, basename="projects")
router.register(r"project-types", views.ProjectTypeViewSet, basename="projectTypes")
router.register(r"projects-mock", views.MockProjectViewSet, basename="projectsMock")
router.register(r"persons", views.PersonViewSet, basename="persons")
router.register(r"project-districts", views.ProjectDistrictViewSet, basename="projectDistricts")
router.register(r"project-sets", views.ProjectSetViewSet, basename="projectSets")
router.register(r"project-areas", views.ProjectAreaViewSet, basename="personsAreas")
router.register(r"budgets", views.BudgetItemViewSet, basename="budgetItems")
router.register(r"tasks", views.TaskViewSet, basename="tasks")
router.register(
    r"project-priority", views.ProjectPriorityViewSet, basename="projectPriorities"
)
router.register(r"project-phases", views.ProjectPhaseViewSet, basename="projectPhases")
router.register(r"task-status", views.TaskStatusViewSet, basename="taskStatuses")
router.register(
    r"construction-phase-details",
    views.ConstructionPhaseDetailViewSet,
    basename="constructionPhaseDetails",
)
router.register(
    r"project-categories", views.ProjectCategoryViewSet, basename="projectCategories"
)
router.register(r"project-risks", views.ProjectRiskViewSet, basename="projectRisks")
router.register(r"notes", views.NoteViewSet, basename="notes")
router.register(r"coordinator-notes", views.CoordinatorNoteViewSet, basename="coordinatorNotes")
router.register(
    r"construction-phases",
    views.ConstructionPhaseViewSet,
    basename="constructionPhases",
)
router.register(
    r"planning-phases",
    views.PlanningPhaseViewSet,
    basename="planningPhases",
)

router.register(
    r"project-quality-levels",
    views.ProjectQualityLevelViewSet,
    basename="projectQualityLevels",
)
router.register(
    r"project-classes",
    views.ProjectClassViewSet,
    basename="projectClasses",
)
router.register(
    r"project-locations",
    views.ProjectLocationViewSet,
    basename="projectLocations",
)

router.register(
    r"responsible-zones",
    views.ProjectResponsibleZoneViewSet,
    basename="responsibleZones",
)

router.register(
    r"project-hashtags",
    views.ProjectHashtagViewSet,
    basename="projectHashTags",
)
router.register(
    r"project-groups",
    views.ProjectGroupViewSet,
    basename="projectGroups",
)
router.register(
    r"project-locks",
    views.ProjectLockViewSet,
    basename="projectLock",
)
router.register(
    r"project-financials",
    views.ProjectFinancialViewSet,
    basename="projectFinancials",
)
router.register(
    r"class-financials",
    views.ClassFinancialViewSet,
    basename="classFinancials",
)

router.register(
    r"location-financials",
    views.LocationFinancialViewSet,
    basename="locationFinancials",
)
router.register(
    r"who-am-i",
    views.WhoAmIViewSet,
    basename="whoAmI",
)

router.register(
    r"sap-costs",
    views.SapCostViewSet,
    basename="sapCosts",
)

router.register(
    r"app-state-value",
    views.AppStateValueViewSet,
    basename="appStateValue",
)

schema_view = get_schema_view(
    openapi.Info(
        title="Infraohjelmointi API",
        description="API documentation for Infrahankkeiden ohjelmointi",
        default_version="v1"
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[path("", include((apirouter.urls, "api")))],
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(apirouter.urls)),
    path("admin/planning-excel-uploader", admin_views.ExcelFormView.as_view()),
    path("admin/budget-excel-uploader", admin_views.ExcelFormView.as_view()),
    path("admin/class-location-excel-uploader", admin_views.ExcelFormView.as_view()),
    path("admin/", admin.site.urls),
    path("pysocial/", include("social_django.urls", namespace="social")),
    path("helauth/", include("helusers.urls")),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
