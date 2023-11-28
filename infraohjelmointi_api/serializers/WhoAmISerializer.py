from infraohjelmointi_api.models import User
from rest_framework import serializers


class WhoAmISerializer(serializers.ModelSerializer):
    ad_groups = serializers.SerializerMethodField()

    group_to_uuid_mapping = {
        "sg_kymp_sso_io_koordinaattorit": "86b826df-589c-40f9-898f-1584e80b5482",
        "sg_kymp_sso_io_ohjelmoijat": "da48bfe9-6a99-481f-a252-077d31473c4c",
        "sg_kymp_sso_io_projektialueiden_ohjelmoijat": "4d229780-b511-4652-b32b-362ad88a7b55",
        "sg_kymp_sso_io_projektipaallikot": "31f86f09-b674-4c1d-81db-6d5fe2e587f9",
        "sl_dyn_kymp_sso_io_katselijat": "7e39a13e-bd48-43ab-bd23-738e73b5137a",
        "sg_kymp_sso_io_admin": "sg_kymp_sso_io_admin",
    }

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
            if group.name in self.group_to_uuid_mapping:
                groups.append(
                    {
                        "id": self.group_to_uuid_mapping.get(group.name),
                        "name": group.name,
                        "display_name": group.display_name,
                    }
                )

        return groups
