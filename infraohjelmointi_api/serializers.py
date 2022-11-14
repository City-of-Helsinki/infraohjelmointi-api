from infraohjelmointi_api.models import ProjectType, Project
from rest_framework import serializers


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    options = serializers.HyperlinkedRelatedField(
        view_name='projecttype-detail',
        lookup_field='type',
        many=True,
        read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'HKRprojectID', 'type', 'created_date', 'updated_date', 'options']

        lookup_field = 'type'
        extra_kwargs = {
            'url': {'lookup_field': 'type'}
        }


class ProjectTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProjectType
        fields = ['id', 'value']