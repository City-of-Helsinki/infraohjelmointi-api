import pandas as pd
import numpy as np

from ....models import Project, Person, ProjectCategory, Note


def defaultProjectPerson():
    person, _ = Person.objects.get_or_create(
        firstName="Command Line",
        lastName="User",
        email="placeholder@blank.com",
        title="Placeholder",
        phone="000000",
    )
    person.save()
    return person


def loadProjectCategories():
    return {pc.value: pc for pc in ProjectCategory.objects.all()}


def proceedWithBudjetFile(excelPath, stdout, style):
    stdout.write(
        style.NOTICE("Reading project data from budjet file {}".format(excelPath))
    )
    # Reading all sheets, header starting from row 10,11
    budgetExcel = pd.concat(
        pd.read_excel(excelPath, sheet_name=None, header=[10, 11]),
        ignore_index=True,
    )
    # making sure all sheets have data in same format
    if len(budgetExcel.columns) != 31:
        raise Exception("Sheets don't follow the same pattern")
    # Dropping columns we don't need
    budgetExcel = budgetExcel.drop(
        budgetExcel.columns[[3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]],
        axis=1,
    )
    # replace E/K with Boolean in the Effects Housing column
    budgetExcel.iloc[:, 2] = budgetExcel.iloc[:, 2].map({"K": True, "E": False})

    # Filtering only project rows out of the dataframe
    budgetExcel = budgetExcel[
        budgetExcel[budgetExcel.columns[15]].notna()
        | budgetExcel[budgetExcel.columns[1]].notna()
        | budgetExcel[budgetExcel.columns[2]].notna()
        | budgetExcel[budgetExcel.columns[14]].notna()
    ]
    # Removing rows without project name
    budgetExcel = budgetExcel[budgetExcel[budgetExcel.columns[0]].notna()]

    # Replacing all NaN values in financial columns with 0.0
    budgetExcel.update(budgetExcel[budgetExcel.columns[3:14]].fillna(0.0))

    # Replace NaN and other arbitrary values with python None
    budgetExcel.iloc[:, 2] = budgetExcel.iloc[:, 2].replace({np.nan: False})
    budgetExcel = budgetExcel.replace({np.nan: None, "?": None})

    # Transforming data from dataframes to python lists
    projects = [
        project + ("Kuvaus puuttuu",)
        for project in zip(
            budgetExcel.iloc[:, 0],
            budgetExcel.iloc[:, 1],
            budgetExcel.iloc[:, 2],
            budgetExcel.iloc[:, 3],
            budgetExcel.iloc[:, 4],
            budgetExcel.iloc[:, 5],
            budgetExcel.iloc[:, 6],
            budgetExcel.iloc[:, 7],
            budgetExcel.iloc[:, 8],
            budgetExcel.iloc[:, 9],
            budgetExcel.iloc[:, 10],
            budgetExcel.iloc[:, 11],
            budgetExcel.iloc[:, 12],
            budgetExcel.iloc[:, 13],
            budgetExcel.iloc[:, 14],
            budgetExcel.iloc[:, 15],
        )
    ]
    # we need to use default person to set as project updater
    defaultPerson = defaultProjectPerson()
    projectCategories = loadProjectCategories()

    for (
        name,
        category,
        effectHousing,
        costForecast,
        bpCPlus1,
        bpCPlus2,
        pcyPlus3,
        pcyPlus4,
        pcyPlus5,
        pcyPlus6,
        pcyPlus7,
        pcyPlus8,
        pcyPlus9,
        pcyPlus10,
        note_content,
        hkrId,
        description,
    ) in projects:
        try:
            stdout.write(
                style.NOTICE(
                    (
                        "-----------------------------------------------------------------------"
                        + "\nHandling project '{}' with description '{}', category '{}', "
                        + "effectHousing '{}', costForecat '{}', bpCPlus1 '{}', bpCPlus2 '{}', "
                        + "pcyPlus3 '{}', pcyPlus4 '{}', pcyPlus5 '{}', pcyPlus6 '{}', "
                        + "pcyPlus7 '{}', pcyPlus8 '{}', pcyPlus9 '{}', pcyPlus10 '{}', "
                        + "note_content '{}', hkrId '{}'"
                    ).format(
                        name,
                        description,
                        category,
                        effectHousing,
                        costForecast,
                        bpCPlus1,
                        bpCPlus2,
                        pcyPlus3,
                        pcyPlus4,
                        pcyPlus5,
                        pcyPlus6,
                        pcyPlus7,
                        pcyPlus8,
                        pcyPlus9,
                        pcyPlus10,
                        note_content,
                        hkrId,
                    )
                )
            )
            try:
                project = Project.objects.get(name=name.strip())
            except Project.DoesNotExist as e:
                stdout.write(
                    style.ERROR(
                        "Project with name '{}' was not found, creating new one".format(
                            name.strip()
                        )
                    )
                )

                project = Project.objects.create(name=name, description=description)

            project.name = name.strip()
            if category:
                project.category = (
                    projectCategories[category]
                    if category[-1] != "."
                    else projectCategories[category[-1]]
                )
            project.effectHousing = effectHousing
            project.costForecast = costForecast
            project.budgetProposalCurrentYearPlus1 = bpCPlus1
            project.budgetProposalCurrentYearPlus2 = bpCPlus2
            project.preliminaryCurrentYearPlus3 = pcyPlus3
            project.preliminaryCurrentYearPlus4 = pcyPlus4
            project.preliminaryCurrentYearPlus5 = pcyPlus5
            project.preliminaryCurrentYearPlus6 = pcyPlus6
            project.preliminaryCurrentYearPlus7 = pcyPlus7
            project.preliminaryCurrentYearPlus8 = pcyPlus8
            project.preliminaryCurrentYearPlus9 = pcyPlus9
            project.preliminaryCurrentYearPlus10 = pcyPlus10
            project.hkrId = hkrId
            project.description = description
            project.save()

            if note_content:
                Note.objects.get_or_create(
                    project=project, content=note_content, updatedBy=defaultPerson
                )
        except Exception as e:
            stdout.write(
                style.ERROR(
                    "Error occurred while handling project '{}'. Error: {}".format(
                        name, e
                    )
                )
            )

    stdout.write(style.SUCCESS("Budjet file import done"))
