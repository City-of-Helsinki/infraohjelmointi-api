import uuid
from django.db import models
from .Project import Project
from .Person import Person
from .TalpaProjectType import TalpaProjectType
from .TalpaServiceClass import TalpaServiceClass
from .TalpaAssetClass import TalpaAssetClass


class TalpaProjectOpening(models.Model):
    STATUS_CHOICES = [
        ("excel_generated", "Avauspyyntö-Excel muodostettu"),
        ("sent_to_talpa", "Avauspyyntö lähetetty Talpaan"),
        ("project_number_opened", "Projektinumero avattu"),
    ]

    PRIORITY_CHOICES = [
        ("Normaali", "Normaali - Normal"),
        ("Korkea", "Korkea - High"),
    ]

    SUBJECT_CHOICES = [
        ("Uusi", "Uusi - New"),
        ("Muutos", "Muutos - Change"),
        ("Lukitus", "Lukitus - Lock"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="talpaProjectOpening"
    )

    # Contact Information (Yhteydenoton tiedot)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, blank=False, null=False, default="excel_generated"
    )
    servicePackage = models.CharField(
        max_length=100, default="Taloushallinnon palvelut", blank=False, null=False
    )  # Financial Administration Services
    service = models.CharField(
        max_length=100, default="SAP-projektinumeron avauspyyntö", blank=False, null=False
    )  # SAP project number opening request
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, blank=False, null=False)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, blank=False, null=False)
    organization = models.CharField(max_length=50, default="2800 Kymp", blank=False, null=False)
    additionalInformation = models.TextField(blank=True, null=True)  # Free-form text area for contact details

    # Project Basic Information (Projektin perustiedot)
    projectName = models.CharField(max_length=200, blank=True, null=True)  # "Projektin nimi"
    projectType = models.ForeignKey(
        TalpaProjectType, on_delete=models.DO_NOTHING, blank=True, null=True
    )  # "Projektin tyyppi"
    budgetAccount = models.CharField(
        max_length=50, blank=True, null=True
    )  # "TA-kohta", can be alphanumeric like "8030101A"
    majorDistrict = models.CharField(max_length=50, blank=True, null=True)  # "Suurpiiri", e.g., "01 Eteläinen"
    area = models.CharField(max_length=100, blank=True, null=True)  # "Alue", e.g., "011 Keskusta"
    projectNumber = models.CharField(max_length=20, blank=True, null=True)  # "Projektinumero" - validated against ranges
    projectDescription = models.TextField(blank=True, null=True)  # "Projektin kuvaus"
    responsiblePerson = models.CharField(max_length=200, blank=True, null=True)  # "Vastuuhenkilö"
    responsiblePersonEmail = models.EmailField(blank=True, null=True)  # "Vastuuhenkilön sähköposti"
    responsiblePersonPhone = models.CharField(max_length=50, blank=True, null=True)  # "Vastuuhenkilön puhelin"
    excelFile = models.FileField(upload_to="talpa_excel/", blank=True, null=True)  # Optional, for storing generated Excel

    # Additional fields from Excel form
    serviceClass = models.ForeignKey(
        TalpaServiceClass, on_delete=models.DO_NOTHING, blank=True, null=True
    )  # "Palveluluokka"
    assetClass = models.ForeignKey(
        TalpaAssetClass, on_delete=models.DO_NOTHING, blank=True, null=True
    )  # "Käyttöomaisuusluokka"
    unit = models.CharField(
        max_length=50, blank=True, null=True
    )  # "Yksikkö" - Required for 2814E projects: "Tontit", "Mao", "Geo"
    investmentProfile = models.CharField(
        max_length=50, blank=True, null=True
    )  # "Invest. profiili", e.g., "Z12550"
    profileName = models.CharField(
        max_length=200, blank=True, null=True
    )  # "Profiilin nimi", e.g., "Kiinteät rakenteet ja laitteet"
    templateProject = models.CharField(
        max_length=50, blank=True, null=True
    )  # "Malliprojekti", e.g., "2814I00000"

    # Metadata
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    createdBy = models.ForeignKey(
        Person, on_delete=models.DO_NOTHING, related_name="talpaProjectOpeningsCreated", blank=True, null=True
    )
    updatedBy = models.ForeignKey(
        Person, on_delete=models.DO_NOTHING, related_name="talpaProjectOpeningsUpdated", blank=True, null=True
    )

    class Meta:
        ordering = ["-createdDate"]

    def __str__(self):
        return f"Talpa Opening for {self.project.name if self.project else 'Unknown Project'} - {self.status}"

    @property
    def is_locked(self):
        """Check if the form is locked (status = sent_to_talpa)"""
        return self.status == "sent_to_talpa"

