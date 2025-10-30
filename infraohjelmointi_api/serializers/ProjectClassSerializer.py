from infraohjelmointi_api.models import ProjectClass
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import (
    ProjectProgrammerSerializer,
)
from rest_framework import serializers
import re


class ProjectClassSerializer(FinancialSumSerializer):
    defaultProgrammer = ProjectProgrammerSerializer(read_only=True)
    computedDefaultProgrammer = serializers.SerializerMethodField()
    autoSelectSubClass = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta(BaseMeta):
        model = ProjectClass

    def get_name(self, obj):
        """
        Handle both IO-758 (suffix removal) and IO-455 (numbering addition) at the serializer level.
        This approach is easily reversible and doesn't modify the database.
        """
        name = obj.name

        # IO-758: Remove TA-kohtien suffixes
        # Use regex pattern to catch all variations more comprehensively
        suffix_pattern = (r',\s*('
                          r'Kylkn|'
                          r'kylkn|'
                          r'Kaupunkiympäristölautakunnan|'
                          r'kaupunkiympäristölautakunnan|'
                          r'KHN|'
                          r'Khn|'
                          r'khn|'
                          r'Kaupunginhallituksen|'
                          r'kaupunginhallituksen'
                          r')\s+käytettäväksi')
        name = re.sub(suffix_pattern, '', name).strip()

        # IO-455: Add numbering to programming view classes
        if not obj.forCoordinatorOnly and hasattr(obj, 'coordinatorClass') and obj.coordinatorClass:
            coordinator_name = obj.coordinatorClass.name

            # Extract full numbering from coordinator class name (up to 4 digits)
            match = re.match(r'^(\d+\s+\d+(?:\s+\d+){0,2})', coordinator_name)
            if match:
                numbering = match.group(1)

                # Check if programming class name already starts with numbering
                programming_match = re.match(r'^(\d+\s+\d+(?:\s+\d+){0,2})\s+(.+)', name)
                if programming_match:
                    # Use the coordinator numbering and the rest of the programming name
                    name = f"{numbering} {programming_match.group(2)}"
                else:
                    # Programming name doesn't start with numbering, just add it
                    name = f"{numbering} {name}"

        return name

    def get_computedDefaultProgrammer(self, obj):
        """
        Compute default programmer with hierarchical fallback logic.

        This method traverses up the class hierarchy to find a default programmer:
        1. Check if current class has default programmer
        2. If not, check parent class
        3. Continue up the hierarchy until found or root reached

        This solves the issue where users select specific sub-classes that don't
        have default programmers, but their parent classes do.
        """
        # 1. Check if current class has default programmer
        if obj.defaultProgrammer_id:
            return ProjectProgrammerSerializer(obj.defaultProgrammer).data

        # 2. Traverse up the parent hierarchy
        current = obj.parent
        while current:
            if current.defaultProgrammer_id:
                return ProjectProgrammerSerializer(current.defaultProgrammer).data
            current = current.parent

        # 3. No default programmer found in hierarchy
        return None

    def get_autoSelectSubClass(self, obj):
        """
        Determine if this class should auto-select a sub-class based on location.

        This replaces the hardcoded frontend logic for "suurpiiri", "östersundom" matching.
        """
        # Check if this class name contains location keywords that should trigger auto-selection
        location_keywords = ['suurpiiri', 'östersundom']

        for keyword in location_keywords:
            if keyword in obj.name.lower():
                return True

        return False
