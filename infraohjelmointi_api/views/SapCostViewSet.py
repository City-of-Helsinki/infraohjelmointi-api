from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.SapCostSerializer import SapCostSerializer
from rest_framework.decorators import action
import logging
from overrides import override
from rest_framework.response import Response

logger = logging.getLogger("infraohjelmointi_api")


class SapCostViewSet(BaseViewSet):
    """
    API endpoint that allows Tasks to be viewed or edited.
    """

    serializer_class = SapCostSerializer
    http_method_names = ["get"]

    @override
    def list(self, request, *args, **kwargs):
        return self.retrieve(request=request, args=args, kwargs=kwargs)
