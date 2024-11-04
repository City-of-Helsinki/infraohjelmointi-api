from ..models import AppStateValue


class AppStateValueService:
    @staticmethod
    def get_or_create(
        name: str,
        value: bool
    ) -> AppStateValue:
        return AppStateValue.objects.get_or_create(name=name, value=value)
    
    @staticmethod
    def update_or_create(
        name: str,
        value: bool
    ) -> AppStateValue:
        return AppStateValue.objects.update_or_create(name=name, value=value)
    
    @staticmethod
    def get_or_create_by_name(
        name: str
    ) -> AppStateValue:
        return AppStateValue.objects.get_or_create(name=name)