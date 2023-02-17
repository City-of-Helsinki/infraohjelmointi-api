import pandas as pd
import numpy as np
from django.db.models import Model
from ....models import Project


def buildHierarchyWithExcelRow(modelClass, row, stdout, style):
    """
    Function used to populate the DB by looping through each row of excel data
    """
    # DB populated in the following order
    # Master Hierarchy Model -> Hierarchy Model -> Sub Hierarchy Model
    # Each -> above tells that the next model has the previous model as parent

    child = "childClass" if modelClass.__name__ == "ProjectClass" else "childLocation"

    masterModelName, modelName, subModelName = row

    # no master class given
    if pd.isna(masterModelName):
        return

    # get or create master model
    masterModel, masterCreated = modelClass.objects.get_or_create(
        name=masterModelName, parent=None, path=masterModelName
    )
    if masterCreated:
        stdout.write(
            style.SUCCESS(
                "Created master {}: {}".format(modelClass.__name__, masterModelName)
            )
        )
    else:
        stdout.write(
            style.NOTICE(
                "Master {} already exists: {}".format(
                    modelClass.__name__, masterModelName
                )
            )
        )
    # no class given
    if pd.isna(modelName):
        return  # don't go further

    # get or create class
    model, classCreated = getattr(masterModel, child).get_or_create(
        name=modelName,
        parent=masterModel,
        path="{}/{}".format(masterModelName, modelName),
    )
    if classCreated:
        stdout.write(
            style.SUCCESS(
                "Created {}: {} with Master {}: {}".format(
                    modelClass.__name__,
                    modelName,
                    modelClass.__name__,
                    masterModelName,
                )
            )
        )
    else:
        stdout.write(
            style.NOTICE("{} already exists: {}".format(modelClass.__name__, modelName))
        )
    # no subclass given
    if pd.isna(subModelName):
        return  # don't go further

    # get or create subclass
    _, subModelCreated = getattr(model, child).get_or_create(
        name=subModelName,
        parent=model,
        path="{}/{}/{}".format(masterModelName, modelName, subModelName),
    )
    if subModelCreated:
        stdout.write(
            style.SUCCESS(
                "Created Sub {}: {} with {}: {} and Master {}: {} ".format(
                    modelClass.__name__,
                    subModelName,
                    modelClass.__name__,
                    modelName,
                    modelClass.__name__,
                    masterModelName,
                )
            )
        )
    else:
        stdout.write(
            style.NOTICE(
                "Sub {} already exists: {}".format(modelClass.__name__, subModelName)
            )
        )


def getMasterHierarchyModel(
    projectProperties, masterHierarchyModelName, modelClass, stdout, style
) -> Model:
    # if master hierarchy model is not present in project properties, then do go further
    if (
        not masterHierarchyModelName in projectProperties
        or projectProperties[masterHierarchyModelName] == ""
    ):
        return None

    # Try getting the same Masterc Hierarchy Model from local DB
    try:
        return modelClass.objects.get(
            name=projectProperties[masterHierarchyModelName],
            parent=None,
        )
    except modelClass.DoesNotExist:
        stdout.write(
            style.ERROR(
                "Master Hierarchy Model with name: {} does not exist in local DB".format(
                    projectProperties[masterHierarchyModelName]
                )
            )
        )

    return None


def setSubHierarchyModelToProject(
    projectProperties,
    hierarchyModelName,
    subHierarchyModelName,
    modelClass,
    parent: Model,
    project: Project,
    stdout,
    style,
):
    """
    Helper function to handle sub hierarchy model for project.
    Will return true if sub hierarchy model read from properties and set successfully to
    project and stored to DB
    """
    # If sub hierarchy model name not present, don't go further
    if (
        not subHierarchyModelName in projectProperties
        or not hierarchyModelName in projectProperties
        or projectProperties[subHierarchyModelName] == ""
    ):
        return False

    # Sub hierarchy model name present so hierarchy model (sub's parent) should exists in local DB to move forward
    try:
        hierarchyModel = modelClass.objects.get(
            name=projectProperties[hierarchyModelName],
            parent=parent,
        )
    except modelClass.DoesNotExist:
        stdout.write(
            style.ERROR(
                "Hierarchy model with name: {} and Master Class: {} does not exist in local DB".format(
                    projectProperties[hierarchyModelName],
                    parent.name,
                )
            )
        )
        # no hierarchy model found in DB, so don't proceed
        return False
    # Hierarchy model exists and now the child sub hierarchy model can be fetched from DB and assigned to project
    try:
        projectAttribute = (
            "projectClass"
            if modelClass.__name__ == "ProjectClass"
            else "projectLocation"
        )
        setattr(
            project,
            projectAttribute,
            modelClass.objects.get(
                name=projectProperties[subHierarchyModelName],
                parent=hierarchyModel,
            ),
        )

        project.save()
        stdout.write(
            style.SUCCESS(
                "Updated {} to {} for Project with Id: {}".format(
                    projectAttribute,
                    projectProperties[subHierarchyModelName],
                    project.id,
                )
            )
        )
    except modelClass.DoesNotExist:
        stdout.write(
            style.ERROR(
                "Sub Class with name: {} and Parent Class: {} does not exist in local DB".format(
                    projectProperties[subHierarchyModelName],
                    projectProperties[hierarchyModelName],
                )
            )
        )
        return False
    # sub hierarchy mode set successfully to project and stored to DB
    return True


def setHierarchyModelToProject(
    projectProperties,
    hierarchyModelName,
    modelClass,
    parent: Model,
    project: Project,
    stdout,
    style,
):
    """
    Helper function to set hierarchy model to project.
    Returns true if class read from properties and set successfully to project
    and stored to DB.
    """
    # if hierarchy model name not present, do go further
    if (
        not hierarchyModelName in projectProperties
        or projectProperties[hierarchyModelName] == ""
    ):
        return False

    # Fetch hierarchy model from local DB with given master hierarchy model as parent
    try:
        projectAttribute = (
            "projectClass"
            if modelClass.__name__ == "ProjectClass"
            else "projectLocation"
        )
        setattr(
            project,
            projectAttribute,
            modelClass.objects.get(
                name=projectProperties[hierarchyModelName],
                parent=parent,
            ),
        )

        project.save()

        stdout.write(
            style.SUCCESS(
                "Updated {} to {} for Project with Id: {}".format(
                    projectAttribute,
                    projectProperties[hierarchyModelName],
                    project.id,
                )
            )
        )
    except modelClass.DoesNotExist:
        stdout.write(
            style.ERROR(
                "Hierarchy model with name: {} and Master Hierarchy Model: {} does not exist in local DB".format(
                    projectProperties[hierarchyModelName],
                    parent.name,
                )
            )
        )
        return False
    # hierarchy model set successfullt to project and stored to DB
    return True
