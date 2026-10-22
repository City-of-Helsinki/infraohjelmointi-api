import uuid
from django.db import models


class ProjectProgrammeLocationMap(models.Model):
    """The location map image of a project programme (IO-936).

    One per programme, shown on the programme's main page. A separate row rather
    than a FileField on ProjectProgramme keeps the file's metadata together and lets
    the same post_delete signal as the other uploads remove the stored file.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        "ProjectProgramme", on_delete=models.CASCADE, related_name="locationMap"
    )
    file = models.FileField(
        upload_to="project_programme_location_maps/%Y/%m/", blank=False, null=False
    )
    originalName = models.CharField(max_length=255, blank=False, null=False)
    contentType = models.CharField(max_length=100, blank=False, null=False)
    size = models.PositiveIntegerField(null=False, default=0)
    uploadedBy = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        to_field="uuid",
        related_name="uploaded_project_programme_location_maps",
    )
    uploadedDate = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        app_label = "infraohjelmointi_api"

    def __str__(self):
        return f"ProjectProgrammeLocationMap {self.originalName} for programme {self.project_programme_id}"
