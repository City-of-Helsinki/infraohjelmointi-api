from infraohjelmointi_api.models import Note
from infraohjelmointi_api.serializers.NotePersonSerializer import NotePersonSerializer
from rest_framework import serializers


class NoteHistorySerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)

    class Meta:
        model = Note.history.model
        fields = "__all__"
