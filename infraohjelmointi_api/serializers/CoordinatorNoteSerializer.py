from infraohjelmointi_api.models import CoordinatorNote
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

class CoordinatorNoteSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = CoordinatorNote
    
