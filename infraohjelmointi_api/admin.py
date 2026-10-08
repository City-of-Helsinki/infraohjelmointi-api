from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from infraohjelmointi_api import models
from infraohjelmointi_api.models.ClassProgrammerAssignment import ClassProgrammerAssignmentAdmin


class NoteImageAdminMixin:
    """Read-only NoteImage display that never renders the raw `file` field.

    Django admin renders a FileField as a link to file.url, and on Azure Blob that
    URL embeds the container SAS token. The download link goes through the API's
    own endpoint instead (session auth works there for admins).
    """

    fields = ("fileName", "contentType", "size", "createdDate", "uploadedBy", "download_link")
    readonly_fields = fields

    @admin.display(description="File")
    def download_link(self, obj):
        if not obj.pk or not obj.file:
            return "-"
        url = reverse("notes-image-file", kwargs={"pk": obj.note_id, "image_id": obj.pk})
        return format_html('<a href="{}">{}</a>', url, obj.fileName)

    def has_add_permission(self, *args, **kwargs):
        # Uploads go through the API, which validates type and size. Varargs because
        # the mixin serves both ModelAdmin.has_add_permission(request) and
        # InlineModelAdmin.has_add_permission(request, obj).
        return False


class NoteImageInline(NoteImageAdminMixin, admin.TabularInline):
    model = models.NoteImage
    extra = 0


class NoteImageAdmin(NoteImageAdminMixin, admin.ModelAdmin):
    list_display = ("fileName", "note", "contentType", "size", "createdDate")


class NoteAdmin(admin.ModelAdmin):
    inlines = [NoteImageInline]
    list_display = ("id", "project", "updatedBy", "updatedDate", "deleted")


admin.site.register(models.Project)
admin.site.register(models.ProjectArea)
admin.site.register(models.ProjectSet)
admin.site.register(models.ProjectType)
admin.site.register(models.ProjectTypeQualifier)
admin.site.register(models.BudgetItem)
admin.site.register(models.Task)
admin.site.register(models.Person)
admin.site.register(models.ProjectPhase)
admin.site.register(models.ProjectPriority)
admin.site.register(models.ConstructionPhase)
admin.site.register(models.ProjectPhaseDetail)
admin.site.register(models.ConstructionProcurementMethod)
admin.site.register(models.StaraProcurementReason)
admin.site.register(models.Note, NoteAdmin)
admin.site.register(models.NoteImage, NoteImageAdmin)
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
admin.site.register(models.AuditLog)
admin.site.register(models.ProjectProgrammer)
admin.site.register(models.ClassProgrammerAssignment, ClassProgrammerAssignmentAdmin)
admin.site.register(models.ConstructionHandover)
admin.site.register(models.ConstructionHandoverFinancing)
admin.site.register(models.ProjectProgramme)
admin.site.register(models.ProjectProgrammeBasicInfo)
admin.site.register(models.ProjectProgrammeDesignCriteria)
admin.site.register(models.ProjectProgrammeTrafficPlanningCriteria)
admin.site.register(models.ProjectProgrammeUrbanSpacingPlanningCriteria)
admin.site.register(models.ProjectProgrammeMaintenanceNeeds)
admin.site.register(models.ProjectProgrammeInteractionAndRelatedProjects)
admin.site.register(models.ProjectProgrammeOtherAttachments)
admin.site.register(models.ProjectProgrammeLink)
admin.site.register(models.ProjectProgrammeAttachment)
admin.site.register(models.ProjectProgrammeLocationMap)
