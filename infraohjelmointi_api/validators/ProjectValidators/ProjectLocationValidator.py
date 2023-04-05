from rest_framework.exceptions import ValidationError


class ProjectLocationValidator:

    requires_context = True

    def _is_projectClass_projectLocation_valid(
        self,
        projectLocation,
        projectClass,
    ) -> bool:
        if projectClass is None or projectLocation is None:
            return True
        if projectClass.parent is None or projectClass.parent.parent is None:
            return True
        if (
            "suurpiiri" in projectClass.name.lower()
            and len(projectClass.name.split()) == 2
            and (
                projectLocation.path.startswith(projectClass.name.split()[0])
                or projectLocation.path.startswith(projectClass.name.split()[0][:-2])
            )
        ):
            return True
        elif "suurpiiri" not in projectClass.name.lower():
            return True
        else:
            return False

    def __call__(self, allFields, serializer) -> None:
        projectLocation = allFields.get("projectLocation", None)
        if projectLocation is None:
            return
        project = serializer.instance
        projectClass = allFields.get("projectClass", None)

        if (
            projectClass is None
            and project is not None
            and project.projectClass is not None
        ):
            projectClass = project.projectClass
        if not self._is_projectClass_projectLocation_valid(
            projectLocation=projectLocation, projectClass=projectClass
        ):
            raise ValidationError(
                "Location: {} with path: {} cannot be under the subClass: {}".format(
                    projectLocation.name,
                    projectLocation.path,
                    projectClass.name,
                ),
                code="projectLocation_invalid_projectClass",
            )
        return projectLocation
