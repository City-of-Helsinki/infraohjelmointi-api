from infraohjelmointi_api.models import CoordinatorNote, ProjectClass
from rest_framework import serializers
from infraohjelmointi_api.validators.ClassFinancialValidators import (
    ClassRelationFieldValidator,
)

class CoordinatorNoteSerializer(serializers.ModelSerializer):
    coordinatorClass = serializers.PrimaryKeyRelatedField(
        many=False,
        validators=[ClassRelationFieldValidator()],
        queryset=ProjectClass.objects.all(),
    )
    class Meta:
        model = CoordinatorNote
        fields = (
            "id",
            "coordinatorNote",
            "year",
            "coordinatorClassName",
            "coordinatorClass",
            "updatedBy",
            "updatedByFirstName",
            "updatedByLastName",
            "createdDate",
            "updatedDate"
        )