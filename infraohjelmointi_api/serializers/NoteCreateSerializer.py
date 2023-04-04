from infraohjelmointi_api.models import Note
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.NotePersonSerializer import NotePersonSerializer
from rest_framework import serializers
from overrides import override


class NoteCreateSerializer(serializers.ModelSerializer):
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["updatedBy"] = (
            NotePersonSerializer(instance.updatedBy).data
            if instance.updatedBy != None
            else None
        )

        return rep
