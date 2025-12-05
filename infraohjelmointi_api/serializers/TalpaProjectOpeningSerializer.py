from infraohjelmointi_api.models import TalpaProjectOpening, TalpaProjectType, TalpaServiceClass, TalpaAssetClass, TalpaProjectNumberRange
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.PersonSerializer import PersonSerializer
from rest_framework import serializers
from overrides import override
from rest_framework.exceptions import ValidationError


class TalpaProjectTypeSerializer(serializers.ModelSerializer):
    """Serializer for TalpaProjectType in dropdowns"""
    class Meta:
        model = TalpaProjectType
        fields = ["id", "code", "name", "category", "priority", "description", "isActive", "notes"]


class TalpaServiceClassSerializer(serializers.ModelSerializer):
    """Serializer for TalpaServiceClass in dropdowns"""
    class Meta:
        model = TalpaServiceClass
        fields = ["id", "code", "name", "description", "projectTypePrefix", "isActive"]


class TalpaAssetClassSerializer(serializers.ModelSerializer):
    """Serializer for TalpaAssetClass in dropdowns"""
    class Meta:
        model = TalpaAssetClass
        fields = ["id", "componentClass", "account", "name", "holdingPeriodYears", "hasHoldingPeriod", "category", "isActive"]


class TalpaProjectNumberRangeSerializer(serializers.ModelSerializer):
    """Serializer for TalpaProjectNumberRange in dropdowns"""
    class Meta:
        model = TalpaProjectNumberRange
        fields = ["id", "projectTypePrefix", "budgetAccount", "budgetAccountNumber", "rangeStart", "rangeEnd",
                  "majorDistrict", "majorDistrictName", "area", "unit", "isActive"]
        ref_name = "TalpaProjectNumberRangeNested"


class TalpaProjectOpeningSerializer(serializers.ModelSerializer):
    """
    Serializer for TalpaProjectOpening with lock checking.

    Deprecated Fields (accepted but not used in Excel export):
    - projectDescription
    - responsiblePersonEmail
    - responsiblePersonPhone
    """

    # =========================================================================
    # Foreign Key Fields - Read with nested serializer, write with ID
    # =========================================================================
    projectType = TalpaProjectTypeSerializer(read_only=True)
    projectTypeId = serializers.PrimaryKeyRelatedField(
        queryset=TalpaProjectType.objects.all(), source="projectType", write_only=True, required=False, allow_null=True
    )
    serviceClass = TalpaServiceClassSerializer(read_only=True)
    serviceClassId = serializers.PrimaryKeyRelatedField(
        queryset=TalpaServiceClass.objects.all(), source="serviceClass", write_only=True, required=False, allow_null=True
    )
    assetClass = TalpaAssetClassSerializer(read_only=True)
    assetClassId = serializers.PrimaryKeyRelatedField(
        queryset=TalpaAssetClass.objects.all(), source="assetClass", write_only=True, required=False, allow_null=True
    )

    # Project number range - replaces individual projectNumber
    projectNumberRange = TalpaProjectNumberRangeSerializer(read_only=True)
    projectNumberRangeId = serializers.PrimaryKeyRelatedField(
        queryset=TalpaProjectNumberRange.objects.all(), source="projectNumberRange", write_only=True, required=False, allow_null=True
    )

    # =========================================================================
    # Metadata Fields
    # =========================================================================
    createdBy = PersonSerializer(read_only=True)
    updatedBy = PersonSerializer(read_only=True)
    isLocked = serializers.SerializerMethodField()

    # Holding time derived from assetClass (read-only computed field)
    holdingTime = serializers.SerializerMethodField(
        help_text="Holding period in years, derived from assetClass.holdingPeriodYears"
    )

    class Meta(BaseMeta):
        model = TalpaProjectOpening
        # BaseMeta already excludes "createdDate", so we don't need to set exclude again
        # Note: We don't need to explicitly list deprecated fields - they're accepted via the model

    # =========================================================================
    # Computed Fields
    # =========================================================================
    def get_isLocked(self, obj):
        """Check if the form is locked (status = sent_to_talpa or project_number_opened)"""
        return obj.is_locked

    def get_holdingTime(self, obj):
        """Get holding period from asset class"""
        if obj.assetClass and obj.assetClass.holdingPeriodYears:
            return obj.assetClass.holdingPeriodYears
        return None

    # =========================================================================
    # Validation
    # =========================================================================
    @override
    def validate(self, attrs):
        """Validate that locked forms cannot be updated"""
        # Check lock status
        instance = self.instance
        if instance and instance.is_locked:
            # Check if trying to update any field (except status which can be changed by system)
            if self.context.get("request") and self.context["request"].method in ["PUT", "PATCH"]:
                # Allow status updates only if coming from system (signal)
                if not self.context.get("from_signal", False):
                    raise ValidationError(
                        {"detail": "Form is locked. Cannot update when status is 'sent_to_talpa' or 'project_number_opened'."}
                    )
        return attrs

    @override
    def update(self, instance, validated_data):
        """Override update to prevent changes when locked"""
        if instance.is_locked and not self.context.get("from_signal", False):
            raise ValidationError(
                {"detail": "Form is locked. Cannot update when status is 'sent_to_talpa' or 'project_number_opened'."}
            )
        return super().update(instance, validated_data)
