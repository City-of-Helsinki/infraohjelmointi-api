from infraohjelmointi_api.models import User
from rest_framework import serializers


class WhoAmISerializer(serializers.ModelSerializer):
    adGroups = serializers.SerializerMethodField()
    groupToUuidMapping = {
        "sg_KYMP_sso_IO_Koordinaattorit": "86b826df-589c-40f9-898f-1584e80b5482",
        "sg_KYMP_sso_IO_Ohjelmoijat": "da48bfe9-6a99-481f-a252-077d31473c4c",
        "sg_KYMP_sso_IO_Projektialueiden_ohjelmoijat": "4d229780-b511-4652-b32b-362ad88a7b55",
        "sg_KYMP_sso_IO_Projektipaallikot": "31f86f09-b674-4c1d-81db-6d5fe2e587f9",
        "sl_dyn_KYMP_sso_IO_Katselijat": "7e39a13e-bd48-43ab-bd23-738e73b5137a",
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
            "adGroups",
        )

    def get_adGroups(self, current_user):
        groups = []
        for group in current_user.ad_groups.all():
            if group.display_name in self.groupToUuidMapping:
                groups.append(
                    {
                        "id": self.groupToUuidMapping.get(group.display_name),
                        "name": group.display_name,
                    }
                )

        return groups
