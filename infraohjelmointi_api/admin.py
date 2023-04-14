from django.contrib import admin
from .models import ProjectPhase
from .models import Project
from .models import ProjectArea
from .models import Task
from .models import BudgetItem
from .models import ProjectSet
from .models import ProjectPriority
from .models import ProjectType
from .models import Person

admin.site.register(Project)
admin.site.register(ProjectArea)
admin.site.register(ProjectSet)
admin.site.register(ProjectType)
admin.site.register(BudgetItem)
admin.site.register(Task)
admin.site.register(Person)
admin.site.register(ProjectPhase)
admin.site.register(ProjectPriority)


# Register your models here.
