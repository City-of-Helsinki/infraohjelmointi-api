from infraohjelmointi_api.models import User
from rest_framework import serializers
from infraohjelmointi_api.services.ADGroupService import ADGroupService


class WhoAmISerializer(serializers.ModelSerializer):
    ad_groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "last_login",
            "is_superuser",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "date_joined",
            "department_name",
            "uuid",
            "ad_groups",
        )

    def get_ad_groups(self, current_user):
        groups = []
        for group in current_user.ad_groups.all():
            if group.name in ADGroupService().get_group_to_uuid_dict():
                groups.append(
                    {
                        "id": self.group_to_uuid_mapping.get(group.name),
                        "name": group.name,
                        "display_name": group.display_name,
                    }
                )

        return groups
