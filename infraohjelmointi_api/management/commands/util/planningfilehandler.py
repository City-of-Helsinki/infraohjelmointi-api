import pandas as pd
import numpy as np
import openpyxl
from openpyxl import load_workbook

from ....models import Project, Person, ProjectCategory, Note
from .openpyxl_theme_and_tint_to_rgb import theme_and_tint_to_hex

MAIN_CLASS_COLOR = "FFFF0000"
CLASS_COLOR = "FFFFC000"
SUBCLASS_COLOR = "FFFFFF00"
BIG_AREA_COLOR = "C9C9C9"
CITY_PART_COLOR = "A9D18E"
GROUP_COLOR = "F8CBAD"
GROUP_PROJECT_COLOR = "FBE5D6"


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


def getColor(wb, color_object):
    try:
        color_in_hex = theme_and_tint_to_hex(
            wb=wb, theme=color_object.theme, tint=color_object.tint
        )
    except:
        color_in_hex = color_object.rgb

    return color_in_hex


def loadProjectCategories():
    return {pc.value: pc for pc in ProjectCategory.objects.all()}


def proceedWithPlanningFile(excelPath, stdout, style):
    stdout.write(
        style.NOTICE("Reading project data from planning file {}".format(excelPath))
    )

    # TODO: to identify the main class, you can use index range from 3-8 and match it

    wb = load_workbook(excelPath, data_only=True)
    sh = wb.worksheets[1]
    rows = list(sh.rows)
    for row in rows[3:]:
        cell = row[0]

        if cell.value == None:
            continue

        cell_color = getColor(wb, cell.fill.start_color)
        if cell_color == MAIN_CLASS_COLOR:
            print("{} is main class ({})".format(cell.value, cell_color))
        elif cell_color == CLASS_COLOR:
            print("{} is class ({})".format(cell.value, cell_color))
        elif cell_color == SUBCLASS_COLOR:
            print("{} is sub class ({})".format(cell.value, cell_color))
        elif cell_color == BIG_AREA_COLOR:
            print("{} is big area ({})".format(cell.value, cell_color))
        elif cell_color == CITY_PART_COLOR:
            print("{} is city part class ({})".format(cell.value, cell_color))
        elif cell_color == GROUP_COLOR:
            print("{} is group ({})".format(cell.value, cell_color))
        elif cell_color == GROUP_PROJECT_COLOR:
            print("{} is group project ({})".format(cell.value, cell_color))
        else:  # project without group
            print("{} is project ({})".format(cell.value, cell_color))

    stdout.write(style.SUCCESS("Planning file import done"))
