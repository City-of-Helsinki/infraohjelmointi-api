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