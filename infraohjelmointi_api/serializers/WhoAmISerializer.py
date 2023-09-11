from infraohjelmointi_api.models import User
from rest_framework import serializers


class WhoAmISerializer(serializers.ModelSerializer):
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
        )
