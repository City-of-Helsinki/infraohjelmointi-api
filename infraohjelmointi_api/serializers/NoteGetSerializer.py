from infraohjelmointi_api.models import Note
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.NoteImageSerializer import NoteImageSerializer
from infraohjelmointi_api.serializers.NotePersonSerializer import NotePersonSerializer
from rest_framework import serializers


class NoteGetSerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)
    deleted = serializers.ReadOnlyField()
    images = serializers.SerializerMethodField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note

    def get_images(self, obj):
        return NoteImageSerializer(
            obj.images.all(), many=True, context=self.context
        ).data
