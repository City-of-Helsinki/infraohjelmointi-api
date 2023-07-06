from infraohjelmointi_api.models import Person
from rest_framework import serializers


class NotePersonSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "firstName", "lastName")
        model = Person
