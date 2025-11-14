from infraohjelmointi_api.models import ProjectClass
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import (
    ProjectProgrammerSerializer,
)
from infraohjelmointi_api.utils.project_class_utils import get_programmer_from_hierarchy
from rest_framework import serializers
import re
import logging

logger = logging.getLogger(__name__)


class ProjectClassSerializer(FinancialSumSerializer):
    defaultProgrammer = ProjectProgrammerSerializer(read_only=True)
    computedDefaultProgrammer = serializers.SerializerMethodField()
    autoSelectSubClass = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta(BaseMeta):
        model = ProjectClass

    def _extract_numbering(self, name, suffix_pattern):
        """Extract numbering prefix from a name (e.g., '8 03 01 01' from '8 03 01 01 Name')."""
        name_clean = re.sub(suffix_pattern, '', name).strip()
        match = re.match(r'^(\d+\s+\d+(?:\s+\d+){0,2})', name_clean)
        return match.group(1) if match else None

    def _get_coordinator_numbering(self, programming_class, suffix_pattern):
        """
        Get numbering from programming class's coordinator hierarchy.
        
        Traverses up coordinator parent chain until numbering is found.
        Returns None if no coordinator or no numbering found.
        """
        try:
            coordinator = programming_class.coordinatorClass
        except (AttributeError, ProjectClass.DoesNotExist):
            return None
        
        if not coordinator:
            return None
        
        current = coordinator
        max_depth = 10
        
        while current and max_depth > 0:
            numbering = self._extract_numbering(current.name, suffix_pattern)
            if numbering:
                return numbering
            current = current.parent
            max_depth -= 1
        
        return None

    def _would_get_numbering_from_coordinator(self, programming_class, suffix_pattern):
        """
        Check if programming class would GET numbering from coordinator.
        
        Returns True only if the class's numbering would change after serialization.
        This distinguishes between:
        - Classes with static numbering that won't change (e.g., "8 03 Kadut...")
        - Classes that will get/update numbering from coordinator
        """
        if programming_class.forCoordinatorOnly:
            return False
        
        raw_numbering = self._extract_numbering(programming_class.name, suffix_pattern)
        coordinator_numbering = self._get_coordinator_numbering(programming_class, suffix_pattern)
        
        if not coordinator_numbering:
            return False
        
        return raw_numbering != coordinator_numbering

    def _any_ancestor_would_get_numbering(self, programming_class, suffix_pattern):
        """Check if any ancestor would get numbering from coordinator."""
        current = programming_class.parent
        max_depth = 10
        
        while current and max_depth > 0:
            if self._would_get_numbering_from_coordinator(current, suffix_pattern):
                return True
            current = current.parent
            max_depth -= 1
        
        return False

    def get_name(self, obj):
        """
        Apply name transformations: suffix removal (IO-758) and numbering addition (IO-455).
        Modifications are applied at serialization only; database remains unchanged.
        """
        name = obj.name

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

        if obj.forCoordinatorOnly:
            return name
        
        if 'suurpiiri' in obj.name.lower():
            return name
        
        if self._any_ancestor_would_get_numbering(obj, suffix_pattern):
            return name
        
        numbering = self._get_coordinator_numbering(obj, suffix_pattern)
        if numbering:
            name_without_numbering = re.sub(r'^(\d+\s+\d+(?:\s+\d+){0,2})\s+', '', name)
            name = f"{numbering} {name_without_numbering}"
        
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
        try:
            programmer = get_programmer_from_hierarchy(obj)
            if programmer:
                return ProjectProgrammerSerializer(programmer).data
            return None
        except ValueError as e:
            logger.error(f"Hierarchy error: {e}")
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
