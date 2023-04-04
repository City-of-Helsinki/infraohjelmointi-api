from infraohjelmointi_api.models import Note
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.NotePersonSerializer import NotePersonSerializer
from rest_framework import serializers


class NoteGetSerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note
