from infraohjelmointi_api.models import Person
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class PersonSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = Person
