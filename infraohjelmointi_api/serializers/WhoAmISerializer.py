from django.db.models import Q
from infraohjelmointi_api.models import ProjectClass, User
from infraohjelmointi_api.permissions import (
    get_restricted_programmer_group_name,
    get_restricted_user_assigned_class_paths,
    is_restricted_programmer,
)
from rest_framework import serializers


class WhoAmISerializer(serializers.ModelSerializer):
    ad_groups = serializers.SerializerMethodField()
    is_restricted_programmer = serializers.SerializerMethodField()
    restricted_class_paths = serializers.SerializerMethodField()
    restricted_class_ids = serializers.SerializerMethodField()

    group_to_uuid_mapping = {
        "sg_kymp_sso_io_koordinaattorit": "86b826df-589c-40f9-898f-1584e80b5482",
        "sg_kymp_sso_io_ohjelmoijat": "da48bfe9-6a99-481f-a252-077d31473c4c",
        "sg_kymp_sso_io_projektialueiden_ohjelmoijat": "4d229780-b511-4652-b32b-362ad88a7b55",
        "sg_kymp_sso_io_projektipaallikot": "31f86f09-b674-4c1d-81db-6d5fe2e587f9",
        "sl_dyn_kymp_sso_io_katselijat": "7e39a13e-bd48-43ab-bd23-738e73b5137a",
        "sg_kymp_sso_io_katselijat_muut": "61336d5e-4b74-400f-a1d6-c9f96d3f1d4d",
        "az_kymp_asgd_u_infraohjelmointi_ulkopuoliset": "952da398-75b3-404a-b274-c8f351d7f5a7",
        "952da398-75b3-404a-b274-c8f351d7f5a7": "952da398-75b3-404a-b274-c8f351d7f5a7",
        "sg_kymp_sso_io_admin": "sg_kymp_sso_io_admin",
        "sg_kymp_sso_io_rakennuttamisen_esihenkilot": "9d22d98e-5cc6-4a91-9fec-1a288a67290e"
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
            "is_restricted_programmer",
            "restricted_class_paths",
            "restricted_class_ids",
        )

    def get_ad_groups(self, current_user):
        groups = []
        restricted_group_name = get_restricted_programmer_group_name()
        for group in current_user.ad_groups.all():
            if group.name in self.group_to_uuid_mapping:
                groups.append(
                    {
                        "id": self.group_to_uuid_mapping.get(group.name),
                        "name": group.name,
                        "display_name": group.display_name,
                    }
                )
            elif group.name == restricted_group_name:
                # IO-756: the group name is configurable, so it is not in the map
                groups.append(
                    {
                        "id": group.name,
                        "name": group.name,
                        "display_name": group.display_name,
                    }
                )

        return groups

    def get_is_restricted_programmer(self, current_user):
        """IO-756: lets the UI apply the restriction without knowing the
        configurable group name."""
        return is_restricted_programmer(current_user)

    def get_restricted_class_paths(self, current_user):
        """Class paths a restricted programmer may edit (IO-756), else empty."""
        if not is_restricted_programmer(current_user):
            return []
        return sorted(get_restricted_user_assigned_class_paths(current_user))

    def get_restricted_class_ids(self, current_user):
        """IDs of the classes a restricted programmer may edit, sub classes
        included, so the UI can check a project without loading the classes."""
        paths = self.get_restricted_class_paths(current_user)
        if not paths:
            return []
        in_scope = Q()
        for path in paths:
            in_scope |= Q(path=path) | Q(path__startswith=f"{path}/")
        return sorted(
            str(class_id)
            for class_id in ProjectClass.objects.filter(in_scope).values_list("id", flat=True)
        )
