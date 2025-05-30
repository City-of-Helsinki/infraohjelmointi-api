from django.contrib import admin

from infraohjelmointi_api import models

admin.site.register(models.Project)
admin.site.register(models.ProjectArea)
admin.site.register(models.ProjectSet)
admin.site.register(models.ProjectType)
admin.site.register(models.BudgetItem)
admin.site.register(models.Task)
admin.site.register(models.Person)
admin.site.register(models.ProjectPhase)
admin.site.register(models.ProjectPriority)
admin.site.register(models.ConstructionPhase)
admin.site.register(models.ConstructionPhaseDetail)
admin.site.register(models.Note)
admin.site.register(models.PlanningPhase)
admin.site.register(models.ProjectCategory)
admin.site.register(models.ProjectFinancial)
admin.site.register(models.ProjectGroup)
admin.site.register(models.ProjectHashTag)
admin.site.register(models.ProjectLock)
admin.site.register(models.ResponsibleZone)
admin.site.register(models.TaskStatus)
admin.site.register(models.ProjectQualityLevel)
admin.site.register(models.ProjectClass)
admin.site.register(models.ProjectRisk)
admin.site.register(models.ProjectLocation)
admin.site.register(models.AppStateValue)
admin.site.register(models.SapCurrentYear)


# Register your models here.
