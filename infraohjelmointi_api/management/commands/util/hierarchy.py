from django.db.models import Model
from ....models import ProjectGroup, ProjectClass, ProjectLocation
from ....services import (
    ProjectClassService,
    ProjectLocationService,
    ProjectGroupService,
)
import re
from .openpyxl_theme_and_tint_to_rgb import theme_and_tint_to_hex
import string

MAIN_CLASS_COLOR = hex(int("ffff0000", 16))
CLASS_COLOR = hex(int("ffffc000", 16))
SUBCLASS_COLOR = hex(int("ffffff00", 16))
DISTRICT_COLOR = hex(int("ffc9c9c9", 16))
DIVISION_COLOR = hex(int("ffa9d18e", 16))
GROUP_COLOR = hex(int("fff8cbad", 16))
GROUP_PROJECT_COLOR = hex(int("fffbe5d6", 16))
CLASS_GROUP_COLOR = hex(int("ff66ff66", 16))
OTHER_CLASSIFICATION_COLOR = hex(int("ffe6b9b8", 16))
OTHER_CLASSIFICATION_SUBCLASS_COLOR = hex(int("fff2dcdb", 16))
AGGREGATING_SUB_LEVEL = hex(int("fff4faa4", 16))

color_map = {
    "FFFF0000": "MAIN CLASS",
    "FFFFC000": "CLASS",
    "FFFFFF00": "SUBCLASS",
    "FFC9C9C9": "DISTRICT",
    "FFA9D18E": "DIVISION",
    "FFF8CBAD": "GROUP",
    "FFFBE5D6": "GROUP PROJECT",
    "FF66FF66": "CLASS GROUP",
    "FFE6B9B8": "OTHER CLASSIFICATION",
    "FFF2DCDB": "OTHER CLASSIFICATION SUBCLASS",
    "FFF4FAA4": "AGGREGATING SUB LEVEL",
}


def getColor(wb, color_object) -> str:
    try:
        color_in_hex = theme_and_tint_to_hex(
            wb=wb, theme=color_object.theme, tint=color_object.tint
        )
    except:
        color_in_hex = color_object.rgb

    return color_in_hex


def hex_to_rgb(hex_in_string):
    hex = hex_in_string[2:] if len(hex_in_string) > 6 else hex_in_string
    return tuple(int(hex[i : i + 2], 16) for i in (0, 2, 4))


def print_with_bg_color(value, hex_color):
    r, g, b = hex_to_rgb(hex_color)
    print("\033[48;2;{};{};{}m{}\033[0m".format(r, g, b, value))


def buildHierarchies(
    wb,
    rows,
):
    # stack for keeping track of class
    pv_class_stack: ProjectClass = []
    cv_class_stack: ProjectClass = []
    cv_color_stack: hex = []

    for row in rows[2:]:
        # programmer view
        pv_cell = row[1]
        pv_code = str(row[0].value).strip() if row[0].value else None
        pv_name = str(pv_cell.value).strip()
        pv_cell_color = (
            getColor(wb, pv_cell.fill.start_color) if pv_cell.fill else "FFFFFFFF"
        )
        pv_cell_color_hex = hex(int(pv_cell_color, 16))
        # coordinator view
        cv_cell = row[6]
        cv_code = str(row[5].value).strip() if row[5].value else None
        cv_name = str(cv_cell.value).strip()
        cv_cell_color = (
            getColor(wb, cv_cell.fill.start_color) if cv_cell.fill else "FFFFFFFF"
        )
        cv_cell_color_hex = hex(int(cv_cell_color, 16))
        cell_colors = [cv_cell_color_hex, pv_cell_color_hex]
        ##############################
        # Handle main class          #
        ##############################
        if MAIN_CLASS_COLOR in cell_colors:
            pv_main_class = None
            if pv_cell_color_hex == MAIN_CLASS_COLOR:
                pv_class_stack.clear()
                pv_main_class = proceedWithMainClass(
                    code=pv_code,
                    name=pv_name,
                    cell_color=pv_cell_color,
                    row_number=pv_cell.row,
                )
                pv_class_stack.append(pv_main_class)

            if cv_cell_color_hex == MAIN_CLASS_COLOR:
                cv_color_stack.clear()
                cv_color_stack.append(cv_cell_color_hex)
                cv_class_stack.clear()
                cv_class_stack.append(
                    proceedWithMainClass(
                        code=cv_code,
                        name=cv_name,
                        for_coordinator_only=True,
                        related_to=pv_main_class,
                        cell_color=cv_cell_color,
                        row_number=cv_cell.row,
                    )
                )

        ##############################
        # Handle class               #
        ##############################
        elif CLASS_COLOR in cell_colors or CLASS_GROUP_COLOR in cell_colors:
            pv_class = None
            if pv_cell_color_hex == CLASS_COLOR:
                pv_class_stack = pv_class_stack[0:1]  # remove siblings
                pv_class = proceedWithClass(
                    code=None,
                    name=pv_name,
                    parent=pv_class_stack[-1],
                    cell_color=pv_cell_color,
                    row_number=pv_cell.row,
                )
                pv_class_stack.append(pv_class)

            # coordinator view only has class group
            if cv_cell_color_hex in [
                CLASS_COLOR,
                CLASS_GROUP_COLOR,
                SUBCLASS_COLOR,
                AGGREGATING_SUB_LEVEL,
            ]:
                # Hierarchy
                # 0 MAIN_COLOR
                # 1  CLASS_COLOR
                # 2   CLASS_GROUP_COLOR (optional, if missing subclass belogs to class)
                # 3     SUBCLASS_COLOR
                # 4       AGGREGATING_SUB_LEVEL (optional, if missing other classification belongs to sublcass)
                # 5         OTHER_CLASSIFICATION_COLOR
                # 6           OTHER_CLASSIFICATION_SUBCLASS_COLOR

                if cv_cell_color_hex == CLASS_COLOR:
                    end_index = 1

                elif cv_cell_color_hex == CLASS_GROUP_COLOR:
                    end_index = 2

                elif cv_cell_color_hex == SUBCLASS_COLOR:
                    end_index = getEndIndex(
                        color_list=cv_color_stack,
                        break_point=SUBCLASS_COLOR,
                        check_point=[CLASS_COLOR, CLASS_GROUP_COLOR],
                    )

                else:  # cv_cell_color_hex == AGGREGATING_SUB_LEVEL:
                    end_index = getEndIndex(
                        color_list=cv_color_stack,
                        break_point=AGGREGATING_SUB_LEVEL,
                        check_point=[SUBCLASS_COLOR],
                    )

                cv_color_stack = cv_color_stack[0:end_index]
                cv_color_stack.append(cv_cell_color_hex)
                cv_class_stack = cv_class_stack[0:end_index]  # remove siblings
                cv_class_stack.append(
                    proceedWithClass(
                        code=cv_code,
                        name=cv_name,
                        parent=cv_class_stack[-1],
                        for_coordinator_only=True,
                        related_to=pv_class,
                        cell_color=cv_cell_color,
                        row_number=cv_cell.row,
                    )
                )

        ##############################
        # Handle sub class           #
        ##############################
        elif SUBCLASS_COLOR in cell_colors:
            pv_class = None
            if pv_cell_color_hex == SUBCLASS_COLOR:
                pv_class_stack = pv_class_stack[0:2]  # remove siblings
                pv_class = proceedWithSubClass(
                    code=None,
                    name=pv_name,
                    parent=pv_class_stack[-1],
                    cell_color=pv_cell_color,
                    row_number=pv_cell.row,
                )
                pv_class_stack.append(pv_class)
                # if subslcass is also a district
                if "suurpiiri" in pv_name.lower() or "östersundom" in pv_name.lower():
                    related_to_district = proceedWithDistrict(
                        name=pv_name,
                        parent_class=pv_class_stack[-1],
                        cell_color=str(DISTRICT_COLOR)[2:].upper(),
                        row_number=pv_cell.row,
                    )

            if cv_cell_color_hex in [
                SUBCLASS_COLOR,
                AGGREGATING_SUB_LEVEL,
                OTHER_CLASSIFICATION_COLOR,
                OTHER_CLASSIFICATION_SUBCLASS_COLOR,
            ]:
                # Hierarchy
                # 0 MAIN_COLOR
                # 1  CLASS_COLOR
                # 2   CLASS_GROUP_COLOR (optional, if missing subclass belogs to class)
                # 3     SUBCLASS_COLOR
                # 4       AGGREGATING_SUB_LEVEL (optional, if missing other classification belongs to sublcass)
                # 5         OTHER_CLASSIFICATION_COLOR
                # 6           OTHER_CLASSIFICATION_SUBCLASS_COLOR

                if cv_cell_color_hex == SUBCLASS_COLOR:
                    end_index = getEndIndex(
                        color_list=cv_color_stack,
                        break_point=SUBCLASS_COLOR,
                        check_point=[CLASS_COLOR, CLASS_GROUP_COLOR],
                    )

                elif cv_cell_color_hex == AGGREGATING_SUB_LEVEL:
                    end_index = getEndIndex(
                        color_list=cv_color_stack,
                        break_point=AGGREGATING_SUB_LEVEL,
                        check_point=[
                            SUBCLASS_COLOR,
                        ],
                    )

                elif cv_cell_color_hex == OTHER_CLASSIFICATION_COLOR:
                    end_index = getEndIndex(
                        color_list=cv_color_stack,
                        break_point=OTHER_CLASSIFICATION_COLOR,
                        check_point=[
                            AGGREGATING_SUB_LEVEL,
                            SUBCLASS_COLOR,
                        ],
                    )

                else:  # cv_cell_color_hex == OTHER_CLASSIFICATION_SUBCLASS_COLOR:
                    end_index = getEndIndex(
                        color_list=cv_color_stack,
                        break_point=OTHER_CLASSIFICATION_SUBCLASS_COLOR,
                        check_point=[
                            OTHER_CLASSIFICATION_COLOR,
                        ],
                    )

                cv_color_stack = cv_color_stack[0:end_index]
                cv_color_stack.append(cv_cell_color_hex)
                cv_class_stack = cv_class_stack[0:end_index]  # remove siblings
                cv_class_stack.append(
                    proceedWithSubClass(
                        code=cv_code,
                        name=cv_name,
                        parent=cv_class_stack[-1],
                        for_coordinator_only=True,
                        related_to=pv_class,
                        cell_color=cv_cell_color,
                        row_number=cv_cell.row,
                    )
                )

            elif cv_cell_color_hex in [DISTRICT_COLOR]:
                proceedWithDistrict(
                    name=pv_name,
                    parent_class=cv_class_stack[-1],
                    related_to=related_to_district,
                    for_coordinator_only=True,
                    cell_color=cv_cell_color,
                    row_number=cv_cell.row,
                )
        #####################################
        # Handle other classification class #
        #####################################
        elif cv_cell_color_hex == OTHER_CLASSIFICATION_COLOR:
            end_index = getEndIndex(
                color_list=cv_color_stack,
                break_point=OTHER_CLASSIFICATION_COLOR,
                check_point=[
                    AGGREGATING_SUB_LEVEL,
                    SUBCLASS_COLOR,
                ],
            )

            cv_color_stack = cv_color_stack[0:end_index]
            cv_color_stack.append(cv_cell_color_hex)
            cv_class_stack = cv_class_stack[0:end_index]  # remove siblings
            cv_class_stack.append(
                proceedWithSubClass(
                    code=cv_code,
                    name=cv_name,
                    parent=cv_class_stack[-1],
                    for_coordinator_only=True,
                    cell_color=cv_cell_color,
                    row_number=cv_cell.row,
                )
            )
        elif DISTRICT_COLOR in cell_colors:
            if pv_cell_color_hex in [DISTRICT_COLOR]:
                related_to_district = proceedWithDistrict(
                    name=pv_name,
                    parent_class=pv_class_stack[-1],
                    cell_color=str(DISTRICT_COLOR)[2:].upper(),
                    row_number=pv_cell.row,
                )
            if cv_cell_color_hex in [DISTRICT_COLOR]:
                end_index = getEndIndex(
                    color_list=cv_color_stack,
                    break_point=OTHER_CLASSIFICATION_COLOR,
                    check_point=[
                        AGGREGATING_SUB_LEVEL,
                        SUBCLASS_COLOR,
                    ],
                )
                cv_color_stack = cv_color_stack[0:end_index]
                cv_color_stack.append(cv_cell_color_hex)
                cv_class_stack = cv_class_stack[0:end_index]  # remove siblings
                proceedWithDistrict(
                    name=pv_name,
                    parent_class=cv_class_stack[-1],
                    related_to=related_to_district,
                    for_coordinator_only=True,
                    cell_color=cv_cell_color,
                    row_number=cv_cell.row,
                )


def getEndIndex(color_list: list, break_point: hex, check_point: list):
    for i in range(0, len(color_list)):
        end_index = i
        if color_list[i] == break_point:
            break

    if color_list[end_index] in check_point:
        end_index += 1

    return end_index


def proceedWithMainClass(
    code: str,
    name: str,
    cell_color: str,
    row_number: int,
    for_coordinator_only: bool = False,
    related_to: ProjectClass = None,
) -> ProjectClass:
    name = (
        # remove first spaces between numbers and then remove all numbers from name
        re.sub("^[\d.-]+\s*", "", re.sub("(?<=\d) (?=\d)", "", str(name).lower()))
        .capitalize()
        .strip()
    )
    name = string.capwords(name, "-")
    name = "{} {}".format(
        re.sub(
            "(?<=\d) (?=\d)", "", str(code).lower()
        ),  # remove spaces between numbers
        name,
    ).strip()
    print_with_bg_color(
        "'{}' is a {} ({}) at line {}. Its class path is '{}'. It is related to '{}' and is for coordinator '{}'".format(
            name,
            color_map[cell_color],
            cell_color,
            row_number,
            name,
            related_to.id if related_to else None,
            for_coordinator_only,
        ),
        cell_color,
    )
    return ProjectClassService.get_or_create(
        name=name,
        parent=None,
        path=name,
        forCoordinatorOnly=for_coordinator_only,
        relatedTo=related_to,
    )[0]


def proceedWithClass(
    code: str,
    name: str,
    cell_color: str,
    row_number: int,
    parent: ProjectClass,
    for_coordinator_only: bool = False,
    related_to: ProjectClass = None,
) -> ProjectClass:
    name = (
        # remove first spaces between numbers and then remove all numbers from name
        re.sub("^[\d.-]+\s*", "", re.sub("(?<=\d) (?=\d)", "", str(name).lower()))
        .capitalize()
        .strip()
    )
    name = string.capwords(name, "-")
    name = "{} {}".format(
        # replace multiply spaces with one
        re.sub("\s\s+", " ", code).strip() if code else "",
        name,
    ).strip()

    print_with_bg_color(
        "'{}' is a {} ({}) at line {}. Its class path is '{}'. It is related to '{}' and is for coordinator '{}'".format(
            name,
            color_map[cell_color],
            cell_color,
            row_number,
            "/".join([parent.path, name]),
            related_to.id if related_to else None,
            for_coordinator_only,
        ),
        cell_color,
    )
    return ProjectClassService.get_or_create(
        name=name,
        parent=parent,
        path="/".join([parent.path, name]),
        forCoordinatorOnly=for_coordinator_only,
        relatedTo=related_to,
    )[0]


def proceedWithSubClass(
    code: str,
    name: str,
    cell_color: str,
    row_number: int,
    parent: ProjectClass,
    for_coordinator_only: bool = False,
    related_to: ProjectClass = None,
) -> ProjectClass:
    name = (
        # remove first spaces between numbers and then remove all numbers from name
        re.sub("^[\d.-]+\s*", "", re.sub("(?<=\d) (?=\d)", "", str(name).lower()))
        .capitalize()
        .strip()
    )
    name = string.capwords(name, "-")
    name = "{} {}".format(
        # replace multiply spaces with one
        re.sub("\s\s+", " ", code).strip() if code else "",
        name,
    ).strip()
    print_with_bg_color(
        "'{}' is a {} ({}) at line {}. Its class path is '{}'. It is related to '{}' and is for coordinator '{}'".format(
            name,
            color_map[cell_color],
            cell_color,
            row_number,
            "/".join([parent.path, name]),
            related_to.id if related_to else None,
            for_coordinator_only,
        ),
        cell_color,
    )
    return ProjectClassService.get_or_create(
        name=name,
        parent=parent,
        path="/".join([parent.path, name]),
        forCoordinatorOnly=for_coordinator_only,
        relatedTo=related_to,
    )[0]


def proceedWithDistrict(
    name: str,
    parent_class: ProjectClass,
    cell_color: str,
    row_number: int,
    for_coordinator_only: bool = False,
    related_to: ProjectLocation = None,
) -> ProjectLocation:
    district = name.split(" ")[0].strip()
    # exceptional case for Östersundom which can be Östersundomin
    district = "Östersundom" if "östersundom" in district.lower() else district
    print_with_bg_color(
        "'{}' is a {} ({}) at line {}. Its class path is '{}'. It is related to '{}' and is for coordinator '{}'".format(
            district,
            color_map[cell_color],
            cell_color,
            row_number,
            district,
            related_to.id if related_to else None,
            for_coordinator_only,
        ),
        cell_color,
    )
    # make this district as related to class for districts in coordinator view
    return ProjectLocationService.get_or_create(
        name=district,
        parentClass=parent_class,
        parent=None,
        path=district,
        forCoordinatorOnly=for_coordinator_only,
        relatedTo=related_to,
    )[0]


def buildHierarchiesAndProjects(
    wb,
    rows,
    skipables,
    name_column_index=0,
    main_class=None,
    for_coordinator_only=False,
    project_handler=None,
):
    # stack for keeping track of location
    location_stack: ProjectLocation = []
    # group object to map project to (particular groupped project)
    project_group: ProjectGroup = None
    # stack for keeping track of class
    class_stack: ProjectClass = []

    # if main class give
    if main_class:
        # remove spaces between numbers
        main_class = re.sub("(?<=\d) (?=\d)", "", str(main_class).lower())
        class_code = main_class.split(" ")[0]
        # capitalize the alpha part
        main_class = "{} {}".format(
            class_code, re.sub("^[\d.-]+\s*", "", main_class).strip().capitalize()
        ).strip()
        main_class = string.capwords(main_class, "-")
        class_stack.append(
            ProjectClassService.get_or_create(
                name=main_class,
                parent=None,
                path=main_class,
                forCoordinatorOnly=for_coordinator_only,
            )[0]
        )

    indention = 0
    type = "MAIN CLASS"

    for row in rows[2:]:
        cell = row[name_column_index]
        # read class/district name
        name = str(cell.value).strip()
        if name == "None" or name == "" or name.lower() in skipables:
            continue

        cell_color = getColor(wb, cell.fill.start_color)
        cell_color_hex = hex(int(cell_color, 16))

        class_code = (
            re.sub(
                "(?<=\d) (?=\d)",
                "",
                row[name_column_index - 1 if name_column_index > 0 else 0].value,
            ).split(" ")[0]
            if cell_color_hex == MAIN_CLASS_COLOR
            else str(row[name_column_index - 1].value).strip()
            if for_coordinator_only and row[name_column_index - 1].value
            else ""
        ).strip()

        # remove all numbers from name
        name = (
            # remove first spaces between numbers and then remove all numbers from name
            re.sub("^[\d.-]+\s*", "", re.sub("(?<=\d) (?=\d)", "", str(name).lower()))
            .capitalize()
            .strip()
        )
        name = string.capwords(name, "-")
        name = "{} {}".format(
            class_code,
            name,
        ).strip()

        if cell_color_hex == MAIN_CLASS_COLOR:
            # if there is no main class in stack or existing main class in stack is not as current
            if len(class_stack) == 0 or class_stack[-1].name != name:
                class_stack.clear()  # remove all
                type = "MAIN CLASS"
                indention = 0
                class_stack.append(
                    ProjectClassService.get_or_create(
                        name=name,
                        parent=None,
                        path=name,
                        forCoordinatorOnly=for_coordinator_only,
                    )[0]
                )

        elif cell_color_hex == CLASS_COLOR:
            class_stack = class_stack[0:1]  # remove all but main class
            type = "CLASS"
            indention = 1
            class_stack.append(
                ProjectClassService.get_or_create(
                    name=name,
                    path="/".join([class_stack[-1].path] + [name]),
                    parent=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )
        elif cell_color_hex == SUBCLASS_COLOR:
            location_stack.clear()  # clear location stack as subclass have no location stack
            class_stack = class_stack[0:2]  # remove sibling class
            type = "SUB CLASS"
            indention = 2

            class_stack.append(
                ProjectClassService.get_or_create(
                    name=name,
                    path="/".join([class_stack[-1].path] + [name]).strip(),
                    parent=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )

            # if subslcass is also a district
            if "suurpiiri" in name.lower():
                location_stack.clear()  # remove all
                district = name.split(" ")[0].strip()
                # exceptional case for Östersundom which can be Östersundomin
                district = (
                    "Östersundom" if "östersundom" in district.lower() else district
                )
                location_stack.append(
                    ProjectLocationService.get_or_create(
                        name=district,
                        parentClass=class_stack[-1],
                        parent=None,
                        path=district,
                        forCoordinatorOnly=for_coordinator_only,
                    )[0]
                )
        elif cell_color_hex == DISTRICT_COLOR:
            location_stack.clear()  # remove all
            type = "DISTRICT"
            indention = 3
            district = (
                name.split(" ")[0].strip() if "suurpiiri" in name.lower() else name
            )

            # exceptional case for Östersundom which can be Östersundomin
            district = "Östersundom" if "östersundom" in district.lower() else district
            location_stack.append(
                ProjectLocationService.get_or_create(
                    name=district,
                    parent=None,
                    path=district,
                    parentClass=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )
        elif cell_color_hex == DIVISION_COLOR:
            location_stack = location_stack[0:1]  # remove all but root distriction
            type = "DIVISION"
            indention = 3
            location_stack.append(
                ProjectLocationService.get_or_create(
                    # keepe number in front of division
                    name="{} {}".format(
                        re.sub("[^\d.-]+\s*$", "", str(cell.value).strip()).strip(),
                        name,
                    ),
                    parent=location_stack[-1],
                    path="/".join([location_stack[-1].path] + [name]),
                    parentClass=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )
        elif cell_color_hex == GROUP_COLOR:
            type = "GROUP"
            indention = 4
            location = location_stack[-1] if len(location_stack) > 0 else None
            # group with name Varaus or Varaukset belong only to district, not to division (city part)
            if (
                ("varaus" in name.lower() or "varaukset" in name.lower())
                and location
                and location.parent != None
            ):
                location = location.parent

            project_group = ProjectGroupService.get_or_create(
                name=name,
                locationRelation=location,
                classRelation=class_stack[-1],
            )[0]

        elif cell_color_hex == GROUP_PROJECT_COLOR:
            type = "GROUP PROJECT"
            indention = 5
            if project_handler:
                project_handler(
                    row=row,
                    name=name,
                    project_class=class_stack[-1],
                    project_location=project_group.locationRelation,
                    project_group=project_group,
                )
        # for coordinator data
        elif cell_color_hex == OTHER_CLASSIFICATION_COLOR:
            class_stack = class_stack[0:3]  # remove sibling class
            type = "OTHER CLASSIFICATION"
            indention = 5
            class_stack.append(
                ProjectClassService.get_or_create(
                    name=name,
                    path="/".join([class_stack[-1].path] + [name]).strip(),
                    parent=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )

        # for coordinator data
        elif cell_color_hex == OTHER_CLASSIFICATION_SUBCLASS_COLOR:
            class_stack = class_stack[0:4]  # remove sibling class
            type = "OTHER CLASSIFICATION SUBCLASS"
            indention = 5
            class_stack.append(
                ProjectClassService.get_or_create(
                    name=name,
                    path="/".join([class_stack[-1].path] + [name]).strip(),
                    parent=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )
        # for coordinator data
        elif cell_color_hex == AGGREGATING_SUB_LEVEL:
            class_stack = class_stack[0:3]  # remove sibling class
            type = "AGGREGATING SUB LEVEL"
            indention = 5
            class_stack.append(
                ProjectClassService.get_or_create(
                    name=name,
                    path="/".join([class_stack[-1].path] + [name]).strip(),
                    parent=class_stack[-1],
                    forCoordinatorOnly=for_coordinator_only,
                )[0]
            )
        # for project data
        else:
            indention = 4
            type = "PROJECT"
            cell_color = "FFFFFF"
            if name and project_handler:
                project_handler(
                    row=row,
                    name=name,
                    project_class=class_stack[-1],
                    project_location=location_stack[-1]
                    if len(location_stack) > 0
                    else None,
                    project_group=None,
                )

        print_with_bg_color(
            "{}'{}' is a {} ({}) at line {}. Its class path is '{}', and location path is '{}'.".format(
                " " * indention,
                name,
                type,
                cell_color_hex,
                cell.row,
                class_stack[-1].path if len(class_stack) > 0 else "",
                location_stack[-1].path if len(location_stack) > 0 else "",
            ),
            cell_color,
        )

        if type == "SUB CLASS" and "suurpiiri" in name:
            print_with_bg_color(
                "{}'{}' will be used as '{}' ({}) too at line {}. Its class path is '{}', and location path is '{}'.".format(
                    " " * indention,
                    name,
                    "DISTRICT",
                    DISTRICT_COLOR,
                    cell.row,
                    class_stack[-1].path,
                    location_stack[-1].path if len(location_stack) > 0 else "",
                ),
                DISTRICT_COLOR,
            )
