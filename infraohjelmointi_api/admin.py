from django.contrib import admin

from .models import *

admin.site.register(Project)
admin.site.register(ProjectArea)
admin.site.register(ProjectSet)
admin.site.register(ProjectType)
admin.site.register(BudgetItem)
admin.site.register(Task)
admin.site.register(Person)
admin.site.register(ProjectPhase)
admin.site.register(ProjectPriority)
admin.site.register(ConstructionPhase)
admin.site.register(ConstructionPhaseDetail)
admin.site.register(Note)
admin.site.register(PlanningPhase)
admin.site.register(ProjectCategory)
admin.site.register(ProjectFinancial)
admin.site.register(ProjectGroup)
admin.site.register(ProjectHashTag)
admin.site.register(ProjectLock)
admin.site.register(ResponsibleZone)
admin.site.register(TaskStatus)
admin.site.register(ProjectQualityLevel)
admin.site.register(ProjectClass)
admin.site.register(ProjectRisk)
admin.site.register(ProjectLocation)


# Register your models here.
