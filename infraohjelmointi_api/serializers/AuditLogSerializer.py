from infraohjelmointi_api.models import AuditLog
from rest_framework import serializers


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog entries with related field data for admin UI consumption
    """

    # Related field serializers for better frontend consumption
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    actor_first_name = serializers.CharField(source='actor.first_name', read_only=True)
    actor_last_name = serializers.CharField(source='actor.last_name', read_only=True)

    project_name = serializers.CharField(source='project.name', read_only=True)
    project_hkr_id = serializers.CharField(source='project.hkrId', read_only=True)

    project_group_name = serializers.CharField(source='project_group.name', read_only=True)
    project_class_name = serializers.CharField(source='project_class.name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor', 'actor_username', 'actor_first_name', 'actor_last_name',
            'operation', 'log_level', 'origin', 'status', 'project', 'project_name',
            'project_hkr_id', 'project_group', 'project_group_name', 'project_class',
            'project_class_name', 'old_values', 'new_values', 'endpoint',
            'createdDate', 'updatedDate'
        ]
