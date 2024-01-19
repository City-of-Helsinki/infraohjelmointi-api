from infraohjelmointi_api.services import ProjectDistrictService


def add_locations(rows):
    for row in rows[1:]:
        district = row[1].value
        division = row[2].value
        subDivision = row[3].value

        # creating the path of the division and getting it's parent path
        # if it has that
        path = row[1].value
        subClassParentPath = None
        subSubClassParentPath = None
        if district != division:
            path += "/" + division
            subClassParentPath = path
            if division != subDivision:
                path += "/" + subDivision
                subSubClassParentPath = path


        district = ProjectDistrictService.get_or_create(
            name=district,
            parent=None,
            path=district,
            level="district",
            )[0]
        print(district.name)
        if subClassParentPath is not None:
            division = ProjectDistrictService.get_or_create(
                name=division,
                parent=district,
                path=subClassParentPath,
                level="division",
                )[0]
            print(division.name)
            if subSubClassParentPath is not None:
                subsubDistrict = ProjectDistrictService.get_or_create(
                    name=subDivision,
                    parent=division,
                    path=path,
                    level="subDivision",
                    )[0]
                print(subsubDistrict.name)
