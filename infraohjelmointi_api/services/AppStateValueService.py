from ..models import AppStateValueModel


class AppStateValueService:
    @staticmethod
    def get_or_create(
        name: str,
        value: bool
    ) -> AppStateValueModel:
        return AppStateValueModel.objects.get_or_create(name=name, value=value)