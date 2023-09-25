from infraohjelmointi_api.models import User
from rest_framework import serializers


class NotePersonSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("uuid", "first_name", "last_name")
        model = User
