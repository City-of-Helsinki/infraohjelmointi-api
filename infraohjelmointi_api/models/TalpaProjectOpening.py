import uuid
from django.db import models
from .Project import Project
from .Person import Person
from .TalpaProjectType import TalpaProjectType
from .TalpaServiceClass import TalpaServiceClass
from .TalpaAssetClass import TalpaAssetClass
from .TalpaProjectNumberRange import TalpaProjectNumberRange


class TalpaProjectOpening(models.Model):
    """
    Model for Talpa project opening data.

    This stores all fields needed for the Talpa Excel export form
    ("Projektin avauslomake Infra").

    Field Reference (from Excel form):
    - Section 1: Budget item selection (2814I/2814E) - derived from projectType
    - Section 2: Project identifiers (budgetAccount, projectNumber, templateProject, etc.)
    - Section 3: Schedule (projectStartDate, projectEndDate)
    - Section 4: Address & contacts (streetAddress, postalCode, responsiblePerson)
    - Section 5: Classes (serviceClass, assetClass, profileName, investmentProfile, readiness)
    """

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

    UNIT_CHOICES = [
        ("Tontit", "Tontit - Plots"),
        ("Mao", "Mao - Land Use"),
        ("Geo", "Geo - Geotechnical"),
    ]

    READINESS_CHOICES = [
        ("Kesken", "Kesken - In Progress"),
        ("Valmis", "Valmis - Ready"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="talpaProjectOpening"
    )

    # =========================================================================
    # Contact Information for Talpa Portal (Yhteydenoton tiedot)
    # These are used when submitting to the Talpa service portal
    # =========================================================================
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, blank=False, null=False, default="excel_generated"
    )
    servicePackage = models.CharField(
        max_length=100, default="Taloushallinnon palvelut", blank=False, null=False
    )  # Financial Administration Services - Talpa portal default
    service = models.CharField(
        max_length=100, default="SAP-projektinumeron avauspyyntö", blank=False, null=False
    )  # SAP project number opening request - Talpa portal default
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, blank=False, null=False, default="Normaali")
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, blank=False, null=False)
    organization = models.CharField(max_length=50, default="2800 Kymp", blank=False, null=False)
    additionalInformation = models.TextField(blank=True, null=True)  # "Lisätietoja" - Talpa portal notes

    # =========================================================================
    # Project Basic Information (Projektin perustiedot) - Excel Form Fields
    # These map directly to columns in "Projektin avauslomake Infra" Excel
    # =========================================================================
    projectName = models.CharField(max_length=24, blank=True, null=True)  # "SAP nimi" - max 24 chars including spaces
    
    projectType = models.ForeignKey(
        TalpaProjectType, on_delete=models.SET_NULL, blank=True, null=True
    )  # "Laji" - Project type selection
    
    budgetAccount = models.CharField(
        max_length=150, blank=True, null=True
    )  # "Talousarviokohdan numero" - e.g., "8 03 01 02 Perusparantaminen ja liikennejärjestelyt"
    majorDistrict = models.CharField(max_length=50, blank=True, null=True)  # "Suurpiiri" - used for validation
    area = models.CharField(max_length=100, blank=True, null=True)  # "Alue" - used for validation
    
    projectNumberRange = models.ForeignKey(
        TalpaProjectNumberRange, on_delete=models.SET_NULL, blank=True, null=True
    )  # "Projektinumeroväli" - Selected project number range (replaces individual projectNumber)

    # Address fields - Excel column "Osoite+postinumero=Työmaa-avain"
    streetAddress = models.CharField(
        max_length=200, blank=True, null=True
    )  # "Osoite" - Street address
    postalCode = models.CharField(
        max_length=10, blank=True, null=True
    )  # "Postinumero" - Postal code

    # Schedule fields - Excel column "Projekti alkaa - päättyy, huom.takuuaika"
    projectStartDate = models.DateField(
        blank=True, null=True
    )  # "Projekti alkaa" - Project start date
    projectEndDate = models.DateField(
        blank=True, null=True
    )  # "Projekti päättyy" - Project end date (note: include warranty period +6 years)

    responsiblePerson = models.CharField(max_length=200, blank=True, null=True)  # "Vastuuhenkilö"
    responsiblePersonEmail = models.EmailField(blank=True, null=True)  # Email for internal use (not sent to Talpa Excel)
    excelFile = models.FileField(upload_to="talpa_excel/", blank=True, null=True)  # Generated Excel file

    # =========================================================================
    # DEPRECATED FIELDS - Kept for backward compatibility
    # These fields are NOT in the Talpa Excel form but may be sent by older UI versions.
    # They are accepted but not used in Excel export.
    # =========================================================================
    projectDescription = models.TextField(blank=True, null=True)  # DEPRECATED: Not in Excel form
    responsiblePersonPhone = models.CharField(max_length=50, blank=True, null=True)  # DEPRECATED: Not in Excel form

    # =========================================================================
    # Classification Fields (Hankkeen luokat) - Excel Form Fields
    # =========================================================================
    serviceClass = models.ForeignKey(
        TalpaServiceClass, on_delete=models.SET_NULL, blank=True, null=True
    )  # "Palveluluokka" - e.g., 4601, 4701, 3551, 5361
    assetClass = models.ForeignKey(
        TalpaAssetClass, on_delete=models.SET_NULL, blank=True, null=True
    )  # "Käyttöomaisuusluokat" - Asset class with holding period
    
    unit = models.CharField(
        max_length=50, choices=UNIT_CHOICES, blank=True, null=True
    )  # "Yksikkö" - REQUIRED for 2814E projects: Tontit, Mao, Geo
    investmentProfile = models.CharField(
        max_length=50, blank=True, null=True
    )  # "Invest. profiili" - e.g., "Z12550" (2814I) or "Z12525" (2814E)
    profileName = models.CharField(
        max_length=200, blank=True, null=True
    )  # "Profiilin nimi" - e.g., "Kiinteät rakenteet ja laitteet"
    templateProject = models.CharField(
        max_length=50, blank=True, null=True
    )  # "Malliprojekti" - e.g., "2814I00000" or "2814E00013"
    readiness = models.CharField(
        max_length=50, choices=READINESS_CHOICES, blank=True, null=True
    )  # "Valmius" - e.g., "Kesken"

    # =========================================================================
    # Metadata
    # =========================================================================
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
        """Check if the form is locked (status = sent_to_talpa or project_number_opened)"""
        return self.status in ("sent_to_talpa", "project_number_opened")
