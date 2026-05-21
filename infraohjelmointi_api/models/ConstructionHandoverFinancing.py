import uuid
from django.db import models


class FinancingParty(models.TextChoices):
    KYMP = "KYMP", "KYMP-rahoitus"
    GLOBAL_CONNECT = "GLOBAL_CONNECT", "GlobalConnect Oy"
    HELEN = "HELEN", "Helen Oy"
    HELEN_SAHKO = "HELEN_SAHKO", "Helen Sähköverkko Oy"
    HSY = "HSY", "Helsingin seudun ympäristöpalvelut-kuntayhtymä HSY"
    ELISA = "ELISA", "Elisa Oyj"
    DNA = "DNA", "DNA Oyj"
    TELIA = "TELIA", "Telia Finland Oyj"
    AURIS = "AURIS", "Auris Kaasunjakelu Oy"
    CINIA = "CINIA", "Cinia Cloud Oy"
    KAUPUNKILIIKENNE = "KAUPUNKILIIKENNE", "Pääkaupunkiseudun Kaupunkiliikenne Oy"
    OTHER = "OTHER", "Muu rahoitus"


class ConstructionHandoverFinancing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handover = models.ForeignKey(
        "infraohjelmointi_api.ConstructionHandover",
        on_delete=models.CASCADE,
        related_name="financing",
    )
    financingParty = models.CharField(
        max_length=50,
        choices=FinancingParty.choices,
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        default="",
    )
    budgetItem = models.ForeignKey(
        "infraohjelmointi_api.BudgetItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="construction_handover_financings",
    )
    projectNumber = models.CharField(max_length=100, blank=True, default="")
    budget = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label = "infraohjelmointi_api"
