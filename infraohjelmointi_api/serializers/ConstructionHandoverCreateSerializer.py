from rest_framework import serializers
from django.db import transaction
from infraohjelmointi_api.models import ConstructionHandover, ConstructionHandoverFinancing
from infraohjelmointi_api.models.ConstructionHandoverFinancing import FinancingParty


class ConstructionHandoverCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionHandover
        fields = "__all__"
        read_only_fields = [
            "createdDate",
            "updatedDate",
            "createdBy",
            "updatedBy",
            "name",
            "description",
            "constructionStart",
            "constructionEnd",
            "personPlanning",
            "personFinancing",
            "constructionProcurementMethod",
            "constructionProjectManager",
        ]

    def create(self, validated_data):
        project = validated_data["project"]
        validated_data.update(
            {
                "name": project.name,
                "description": project.description,
                "constructionStart": project.estConstructionStart,
                "constructionEnd": project.estConstructionEnd,
                "personPlanning": project.personPlanning,
                "personFinancing": project.personProgramming,
                "constructionProcurementMethod": project.constructionProcurementMethod,
                "constructionProjectManager": project.personConstruction,
            }
        )

        with transaction.atomic():
            handover = super().create(validated_data)
            ConstructionHandoverFinancing.objects.create(
                handover=handover,
                financingParty=FinancingParty.KYMP,
                projectNumber=project.sapProject if project.sapProject else "",
                budget=project.costForecast,
                # TODO: budgetItem specification still unclear, will be added later when clarified
            )

        return handover