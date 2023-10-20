from infraohjelmointi_api.models import CoordinatorNote
from rest_framework import serializers

class CoordinatorNoteSerializer(serializers.ModelSerializer):
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
