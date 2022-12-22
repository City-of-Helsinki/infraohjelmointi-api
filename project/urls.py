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
from infraohjelmointi_api import views

router = routers.DefaultRouter()
router.register(r"projects", views.ProjectViewSet, basename="projects")
router.register(r"project-types", views.ProjectTypeViewSet, basename="projectTypes")
router.register(r"projects-mock", views.MockProjectViewSet, basename="projectsMock")
router.register(r"persons", views.PersonViewSet, basename="persons")
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
    views.ConPhaseDetailViewSet,
    basename="constructionPhaseDetails",
)
router.register(
    r"project-categories", views.ProjectCategoryViewSet, basename="projectCategories"
)
router.register(r"project-risks", views.ProjectRiskViewSet, basename="projectRisks")
router.register(r"notes", views.NoteViewSet, basename="notes")
router.register(
    r"construction-phases",
    views.ConstructionPhaseViewSet,
    basename="constructionPhases",
)

urlpatterns = [
    path("", include(router.urls)),
    path("admin/", admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
