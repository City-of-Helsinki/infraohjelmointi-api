from ..models import ProjectDistrict


class ProjectDistrictService:
    @staticmethod
    def get_or_create(
        name: str,
        parent: ProjectDistrict | None,
        path: str,
        level: str,
    ) -> ProjectDistrict:
        return ProjectDistrict.objects.get_or_create(
            name=name,
            parent=parent,
            path=path,
            level=level,
        )

    @staticmethod
    def list_all() -> list[ProjectDistrict]:
        return ProjectDistrict.objects.all()

    @staticmethod
    def get_by_path(path: str) -> ProjectDistrict:
        """Gets project's district, subdistrict or sub-subdistrict"""
        try:
            return ProjectDistrict.objects.get(path=path)
        except (Exception):
            return None

    @staticmethod
    def get_by_parent(parent: ProjectDistrict):
        """Gets project's districts, subdistricts and subsubdistricts by parent"""
        try:
            return ProjectDistrict.objects.get(parent=parent)
        except (Exception):
            return None
