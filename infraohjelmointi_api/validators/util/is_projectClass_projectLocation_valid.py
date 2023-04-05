def _is_projectClass_projectLocation_valid(
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
