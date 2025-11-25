from infraohjelmointi_api.models import TalpaProjectOpening, TalpaProjectType, TalpaServiceClass, TalpaAssetClass
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


class TalpaProjectOpeningSerializer(serializers.ModelSerializer):
    """
    Serializer for TalpaProjectOpening with lock checking.
    
    Field Aliases (UI compatibility):
    - projectStart -> projectStartDate
    - projectEnd -> projectEndDate
    - assetClassesId -> assetClassId (UI uses plural)
    
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
    # UI uses plural "assetClassesId" - accept both
    assetClassesId = serializers.PrimaryKeyRelatedField(
        queryset=TalpaAssetClass.objects.all(), source="assetClass", write_only=True, required=False, allow_null=True
    )
    
    # =========================================================================
    # Metadata Fields
    # =========================================================================
    createdBy = PersonSerializer(read_only=True)
    updatedBy = PersonSerializer(read_only=True)
    isLocked = serializers.SerializerMethodField()
    
    # =========================================================================
    # UI Field Aliases - Accept UI field names, map to model fields
    # These allow the UI to use its preferred field names while the API
    # uses the model field names internally.
    # =========================================================================
    # Schedule field aliases (UI uses projectStart/projectEnd, model uses projectStartDate/projectEndDate)
    projectStart = serializers.DateField(
        source="projectStartDate", required=False, allow_null=True,
        help_text="Alias for projectStartDate - UI compatibility"
    )
    projectEnd = serializers.DateField(
        source="projectEndDate", required=False, allow_null=True,
        help_text="Alias for projectEndDate - UI compatibility"
    )
    
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
        """Check if the form is locked (status = sent_to_talpa)"""
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
        instance = self.instance
        if instance and instance.is_locked:
            # Check if trying to update any field (except status which can be changed by system)
            if self.context.get("request") and self.context["request"].method in ["PUT", "PATCH"]:
                # Allow status updates only if coming from system (signal)
                if not self.context.get("from_signal", False):
                    raise ValidationError(
                        {"detail": "Form is locked. Cannot update when status is 'sent_to_talpa'."}
                    )
        return attrs

    @override
    def update(self, instance, validated_data):
        """Override update to prevent changes when locked"""
        if instance.is_locked and not self.context.get("from_signal", False):
            raise ValidationError(
                {"detail": "Form is locked. Cannot update when status is 'sent_to_talpa'."}
            )
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        """
        Include both model field names and UI aliases in the response.
        This ensures UI can read using its preferred field names.
        """
        data = super().to_representation(instance)
        
        # Add UI aliases for date fields (in addition to model field names)
        data['projectStart'] = data.get('projectStartDate')
        data['projectEnd'] = data.get('projectEndDate')
        
        return data

