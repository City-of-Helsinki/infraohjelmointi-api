from uuid import UUID
from infraohjelmointi_api.models import ProjectHashTag
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .ProjectHashtagSerializer import ProjectHashtagSerializer
from .ProjectPhaseSerializer import ProjectPhaseSerializer

class SearchResultSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    hashTags = serializers.SerializerMethodField()
    phase = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    programmed = serializers.SerializerMethodField()

    def get_path(self, obj):
        instanceType = obj._meta.model.__name__
        classInstance = None
        locationInstance = None
        path = ""
        group = None
        group_has_location = False
        if instanceType == "Project":
            classInstance = getattr(obj, "projectClass", None)
            locationInstance = getattr(obj, "projectLocation", None)
            group = getattr(obj, "projectGroup", None)

            if group:
                group_location = getattr(group, "locationRelation", None)
                group_has_location = group_location is not None

        elif instanceType == "ProjectClass":
            classInstance = obj
        elif instanceType == "ProjectLocation":
            classInstance = obj.parentClass
            locationInstance = obj
        elif instanceType == "ProjectGroup":
            classInstance = getattr(obj, "classRelation", None)
            locationInstance = getattr(obj, "locationRelation", None)

        if classInstance is None:
            return path

        if classInstance.parent is not None and classInstance.parent.parent is not None:
            path = "masterClass={}&class={}&subClass={}".format(
                str(classInstance.parent.parent.id),
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        elif classInstance.parent is not None:
            path = "masterClass={}&class={}".format(
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        else:
            path = "masterClass={}".format(str(classInstance.id))

        if "suurpiiri" in classInstance.name.lower():
            return path

        if locationInstance is None:
            return path

        if locationInstance.parent is None and (group is None or group_has_location):
            path = path + "&district={}".format(str(locationInstance.id))
        if (
            locationInstance.parent is not None 
            and locationInstance.parent.parent is not None
            and (group is None or group_has_location)
        ):
            path = path + "&district={}".format(str(locationInstance.parent.parent.id))
        if (
            locationInstance.parent is not None
            and locationInstance.parent.parent is None
            and (group is None or group_has_location)
        ):
            path = path + "&district={}".format(str(locationInstance.parent.id))

        return path

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
    
