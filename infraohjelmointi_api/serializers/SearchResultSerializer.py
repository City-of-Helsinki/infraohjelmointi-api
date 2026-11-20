from uuid import UUID
from infraohjelmointi_api.models import ProjectHashTag
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .ProjectHashtagSerializer import ProjectHashtagSerializer
from .ProjectPhaseSerializer import ProjectPhaseSerializer
from .serializer_utils import get_planning_path

class SearchResultSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    hashTags = serializers.SerializerMethodField()
    phase = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    programmed = serializers.SerializerMethodField()

    def get_path(self, obj):
        return get_planning_path(obj)

    def get_phase(self, obj):
        if not hasattr(obj, "phase") or obj.phase is None:
            return None
        return ProjectPhaseSerializer(obj.phase).data

    def get_name(self, obj):
        return obj.name

    def get_id(self, obj):
        return obj.id

    def get_type(self, obj):
        instanceType = obj._meta.model.__name__
        if instanceType == "ProjectLocation":
            return "locations"
        elif instanceType == "ProjectClass":
            return "classes"
        elif instanceType == "Project":
            return "projects"
        elif instanceType == "ProjectGroup":
            return "groups"
        else:
            raise ValidationError(detail={"type": "Invalid value"}, code="invalid")

    def get_hashTags(self, obj):
        if not hasattr(obj, "hashTags") or obj.hashTags is None:
            return []

        include_hashtags_list = self.context.get("hashtags_include", [])
        projectHashtags = ProjectHashtagSerializer(obj.hashTags, many=True).data
        projectHashtags = list(
            filter(
                lambda hashtag: hashtag["id"] in include_hashtags_list,
                projectHashtags,
            )
        )
        return projectHashtags

    def get_programmed(self, obj):
        """
        Gets the field `programmed` from a Project instance
        This function only concerns instances of Project
        """
        # Checking if programmed exists on obj
        # Only exists on Project
        if hasattr(obj, "programmed"):
            return obj.programmed
        return None
    
