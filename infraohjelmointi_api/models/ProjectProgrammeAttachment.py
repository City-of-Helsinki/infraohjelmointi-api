import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ProjectProgrammeAttachment(models.Model):
    """A file attached to a project programme section (IO-914).

    Every section has its own "Liitetiedostot" list, so - like ProjectProgrammeLink -
    the owner is a generic FK to any section model. Each section declares a
    GenericRelation to this model, which makes deleting a programme (and with it its
    sections) cascade here, so the post_delete signal also removes the stored files.

    The file fields mirror ConstructionHandoverAttachment (IO-857); the reusable part
    is validation and file serving in utils/, not a shared base model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Named section* rather than ProjectProgrammeLink's contentType/objectId, because
    # contentType is the file's MIME type here, as in the other attachment models.
    sectionType = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="References to any type of a section (basic info, design criteria, etc.)",
    )
    sectionId = models.UUIDField()
    sectionObject = GenericForeignKey("sectionType", "sectionId")
    file = models.FileField(
        upload_to="project_programme_attachments/%Y/%m/", blank=False, null=False
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
        related_name="uploaded_project_programme_attachments",
    )
    uploadedDate = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        app_label = "infraohjelmointi_api"
        ordering = ["uploadedDate"]
        indexes = [
            models.Index(fields=["sectionType", "sectionId"]),
        ]

    def __str__(self):
        return f"ProjectProgrammeAttachment {self.originalName} for section {self.sectionId}"
