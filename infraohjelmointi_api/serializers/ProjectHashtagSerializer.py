from infraohjelmointi_api.models import ProjectHashTag
from infraohjelmointi_api.serializers import BaseMeta, DynamicFieldsModelSerializer


class ProjectHashtagSerializer(DynamicFieldsModelSerializer):
    class Meta(BaseMeta):
        model = ProjectHashTag
