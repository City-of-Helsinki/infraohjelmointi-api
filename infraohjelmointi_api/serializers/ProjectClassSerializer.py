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

# Pattern for TA-kohtien suffixes to remove (IO-758)
SUFFIX_PATTERN = re.compile(
    r',\s*(?:Kylkn|kylkn|Kaupunkiympäristölautakunnan|kaupunkiympäristölautakunnan|'
    r'KHN|Khn|khn|Kaupunginhallituksen|kaupunginhallituksen)\s+käytettäväksi'
)

# Pattern for numbering prefix (e.g., "8 03 01 01")
NUMBERING_PATTERN = re.compile(r'^(\d+\s+\d+(?:\s+\d+){0,2})')


class ProjectClassSerializer(FinancialSumSerializer):
    defaultProgrammer = ProjectProgrammerSerializer(read_only=True)
    computedDefaultProgrammer = serializers.SerializerMethodField()
    autoSelectSubClass = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta(BaseMeta):
        model = ProjectClass

    # -------------------------------------------------------------------------
    # Name transformation helpers (IO-455, IO-758)
    # -------------------------------------------------------------------------

    def _extract_numbering(self, name):
        """Extract numbering prefix (e.g., '8 03 01 01' from '8 03 01 01 Name')."""
        clean_name = SUFFIX_PATTERN.sub('', name).strip()
        match = NUMBERING_PATTERN.match(clean_name)
        return match.group(1) if match else None

    def _get_coordinator_numbering(self, obj):
        """
        Get numbering from coordinator hierarchy.
        Traverses up the coordinator parent chain until numbering is found.
        """
        try:
            coord = obj.coordinatorClass
        except (AttributeError, ProjectClass.DoesNotExist):
            return None

        for _ in range(10):  # max depth safety
            if not coord:
                break
            numbering = self._extract_numbering(coord.name)
            if numbering:
                return numbering
            coord = coord.parent

        return None

    def _find_ancestor_numbering(self, obj):
        """
        Find numbering that would be applied to the nearest ancestor.
        Returns None if no ancestor's name would change.
        """
        parent = obj.parent
        for _ in range(10):  # max depth safety
            if not parent or parent.forCoordinatorOnly:
                break

            raw = self._extract_numbering(parent.name)
            coord = self._get_coordinator_numbering(parent)

            # If parent's numbering would change, return what it would become
            if coord and raw != coord:
                return coord

            parent = parent.parent

        return None

    def _is_more_specific(self, child_num, ancestor_num):
        """Check if child numbering extends ancestor's (e.g., '8 08 01 01' extends '8 08 01')."""
        return child_num.startswith(ancestor_num) and len(child_num) > len(ancestor_num)

    def _get_numbering_to_apply(self, obj):
        """
        Determine what numbering (if any) should be applied to this class.
        
        Rules:
        - No numbering for coordinator-only classes or suurpiiri classes
        - No numbering if it would duplicate an ancestor's
        - Allow numbering if it's more specific than ancestor's
        """
        if obj.forCoordinatorOnly or 'suurpiiri' in obj.name.lower():
            return None

        my_numbering = self._get_coordinator_numbering(obj)
        if not my_numbering:
            return None

        ancestor_numbering = self._find_ancestor_numbering(obj)
        if not ancestor_numbering:
            return my_numbering

        # Allow if more specific (e.g., "8 08 01 01" extends "8 08 01")
        if self._is_more_specific(my_numbering, ancestor_numbering):
            return my_numbering

        return None  # Block: same or unrelated numbering

    def get_name(self, obj):
        """
        Transform name for display (IO-758, IO-455).
        - Removes TA-kohtien suffixes
        - Adds numbering from coordinator (for programming view)
        """
        name = SUFFIX_PATTERN.sub('', obj.name).strip()

        numbering = self._get_numbering_to_apply(obj)
        if numbering:
            name_without_num = NUMBERING_PATTERN.sub('', name).strip()
            return f"{numbering} {name_without_num}"

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
