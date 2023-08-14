from infraohjelmointi_api.models import Project, ProjectGroup
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.DynamicFieldsModelSerializer import (
    DynamicFieldsModelSerializer,
)
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from infraohjelmointi_api.validators.ProjectGroupValidators.ProjectsFieldValidator import (
    ProjectsFieldValidator,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from overrides import override
from rest_framework.exceptions import ValidationError

from django.shortcuts import get_object_or_404


class ProjectGroupSerializer(DynamicFieldsModelSerializer, FinancialSumSerializer):
    projects = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta(BaseMeta):
        model = ProjectGroup
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroup.objects.all(),
                fields=["name", "classRelation", "locationRelation"],
            ),
            ProjectsFieldValidator(),
        ]

    @override
    def update(self, instance, validated_data):
        # new project Ids
        updatedProjectIds = validated_data.pop("projects", [])
        # get all project ids that currently belong to this group
        existingProjectIds = instance.project_set.all().values_list("id", flat=True)
        # project that are to be removed from this group
        removedProjects = list(set(existingProjectIds) - set(updatedProjectIds))
        if len(updatedProjectIds) > 0:
            for projectId in updatedProjectIds:
                if projectId not in existingProjectIds:
                    project = get_object_or_404(Project, pk=projectId)
                    project.projectGroup = instance
                    project.save()

        if len(removedProjects) > 0:
            for projectId in removedProjects:
                project = get_object_or_404(Project, pk=projectId)
                project.projectGroup = None
                project.save()

        return super(ProjectGroupSerializer, self).update(instance, validated_data)

    @override
    def create(self, validated_data):
        projectIds = validated_data.pop("projects", None)
        projectGroup = self.Meta.model.objects.create(**validated_data)
        if projectIds is not None and len(projectIds) > 0:
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                project.projectGroup = projectGroup
                project.save()

        return projectGroup

    @override
    def to_representation(self, instance: ProjectGroup):
        rep = super().to_representation(instance)
        # use context to check if coordinator class/locations are needed
        for_coordinator = self.context.get("for_coordinator", False)
        if for_coordinator == True:
            # if class is suurpiiri then goto its parent and check for coordinationClass since suurpiiri classes have no
            # coordination class
            rep["classRelation"] = (
                instance.classRelation.coordinatorClass.id
                if hasattr(instance.classRelation, "coordinatorClass")
                else instance.classRelation.parent.coordinatorClass.id
                if (
                    instance.classRelation != None
                    and "suurpiiri" in instance.classRelation.name.lower()
                    and hasattr(instance.classRelation.parent, "coordinatorClass")
                )
                else None
            )
            # if project location is division/subdivision then goto its district and get related coordination location else none
            rep["locationRelation"] = (
                instance.locationRelation.coordinatorLocation.id
                if (hasattr(instance.locationRelation, "coordinatorLocation"))
                else instance.locationRelation.parent.coordinatorLocation.id
                if (
                    instance.locationRelation != None
                    and instance.locationRelation.parent != None
                    and instance.locationRelation.parent.parent == None
                    and hasattr(instance.locationRelation.parent, "coordinatorLocation")
                )
                else instance.locationRelation.parent.parent.coordinatorLocation.id
                if (
                    instance.locationRelation != None
                    and instance.locationRelation.parent != None
                    and instance.locationRelation.parent.parent != None
                    and hasattr(
                        instance.locationRelation.parent.parent, "coordinatorLocation"
                    )
                )
                else None
            )
        return rep
