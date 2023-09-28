from infraohjelmointi_api.models import CoordinatorNote
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers

class CoordinatorNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoordinatorNote
        fields = (
            "id",
            "coordinatorNote",
            "year",
            "planningClass",
            "planningClassId",
            "updatedById",
            "updatedByFirstName",
            "updatedByLastName",
            "createdDate",
        )