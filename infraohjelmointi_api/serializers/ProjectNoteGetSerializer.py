from infraohjelmointi_api.models import Note
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.NoteHistorySerializer import NoteHistorySerializer
from infraohjelmointi_api.serializers.NotePersonSerializer import NotePersonSerializer
from rest_framework import serializers
from overrides import override


class ProjectNoteGetSerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["history"] = NoteHistorySerializer(instance.history.all(), many=True).data

        return rep
