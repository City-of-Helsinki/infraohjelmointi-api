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
        suffixes_to_remove = [
            ', Kylkn käytettäväksi',
            ', kylkn käytettäväksi', 
            ', Kaupunkiympäristölautakunnan käytettäväksi',
            ', KHN käytettäväksi',
            ', khn käytettäväksi',
            ', kaupunginhallituksen käytettäväksi'  # Full form, if it exists
        ]
        
        # Remove the first matching suffix
        for suffix in suffixes_to_remove:
            if suffix in name:
                name = name.replace(suffix, '').strip()
                break
        
        # IO-455: Add numbering to programming view classes
        if not obj.forCoordinatorOnly and hasattr(obj, 'coordinatorClass') and obj.coordinatorClass:
            coordinator_name = obj.coordinatorClass.name
            
            # Extract numbering from coordinator class name
            match = re.match(r'^(\d+\s+\d+(?:\s+\d+)?)', coordinator_name)
            if match:
                numbering = match.group(1)
                
                # Check if programming class name already starts with numbering
                programming_match = re.match(r'^(\d+\s+\d+(?:\s+\d+)?)\s+(.+)', name)
                if programming_match:
                    # Use the coordinator numbering and the rest of the programming name
                    name = f"{numbering} {programming_match.group(2)}"
                else:
                    # Programming name doesn't start with numbering, just add it
                    name = f"{numbering} {name}"
        
        return name
