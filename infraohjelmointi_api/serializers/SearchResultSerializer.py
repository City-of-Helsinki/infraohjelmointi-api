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

    def get_path(self, obj):
        instanceType = obj._meta.model.__name__
        classInstance = None
        locationInstance = None
        path = ""
        if instanceType == "Project":
            classInstance = getattr(obj, "projectClass", None)
            locationInstance = getattr(obj, "projectLocation", None)
        elif instanceType in ["ProjectLocation", "ProjectClass"]:
            classInstance = obj
        elif instanceType == "ProjectGroup":
            classInstance = getattr(obj, "classRelation", None)
            locationInstance = getattr(obj, "districtRelation", None)

        if classInstance is None:
            return path

        if classInstance.parent is not None and classInstance.parent.parent is not None:
            path = "{}/{}/{}".format(
                str(classInstance.parent.parent.id),
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        elif classInstance.parent is not None:
            path = "{}/{}".format(
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        else:
            path = str(classInstance.id)

        if locationInstance is None:
            return path

        if locationInstance.parent is None:
            path = path + "/{}".format(str(locationInstance.id))
        if (
            locationInstance.parent is not None
            and locationInstance.parent.parent is not None
        ):
            path = path + "/{}".format(str(locationInstance.parent.parent.id))
        if (
            locationInstance.parent is not None
            and locationInstance.parent.parent is None
        ):
            path = path + "/{}".format(str(locationInstance.parent.id))

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
