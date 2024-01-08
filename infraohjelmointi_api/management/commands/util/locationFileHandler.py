from infraohjelmointi_api.services import ProjectDistrictService


def addLocations(rows):
    for row in rows[1:]:
        district = row[1].value
        subDistrict = row[2].value
        subSubDistrict = row[3].value

        # creating the path of the division and getting it's parent path
        # if it has that
        path = row[1].value
        subClassParentPath = None
        subSubClassParentPath = None
        if district != subDistrict:
            path += " / " + subDistrict
            subClassParentPath = path
            if subDistrict != subSubDistrict:
                path += " / " + subSubDistrict
                subSubClassParentPath = path


        district = ProjectDistrictService.get_or_create(
            name=district,
            parent=None, 
            path=district,
            level="district",
            )[0]
        print(district.name)
        if subClassParentPath:
            subDistrict = ProjectDistrictService.get_or_create(
                name=subDistrict, 
                parent=district, 
                path=subClassParentPath,
                level="subDistrict",
                )[0]
            print(subDistrict.name)
            if subSubClassParentPath:
                subsubDistrict = ProjectDistrictService.get_or_create(
                    name=subSubDistrict, 
                    parent=subDistrict, 
                    path=path,
                    level="subSubDistrict",
                    )[0]
                print(subsubDistrict.name)