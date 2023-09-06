from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.WhoAmISerializer import WhoAmISerializer
from rest_framework.decorators import action
import logging
from overrides import override
from rest_framework.response import Response

logger = logging.getLogger("infraohjelmointi_api")


class WhoAmIViewSet(BaseViewSet):
    """
    API endpoint that allows Tasks to be viewed or edited.
    """

    serializer_class = WhoAmISerializer
    http_method_names = ["get"]

    @override
    def list(self, request, *args, **kwargs):
        return self.retrieve(request=request, args=args, kwargs=kwargs)

    @override
    def retrieve(self, request, *args, **kwargs):
        logger.debug("Retrieve Current user {}".format(request.user))

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
