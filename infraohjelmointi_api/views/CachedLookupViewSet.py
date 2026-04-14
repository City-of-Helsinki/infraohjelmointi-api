from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.db import transaction
from django.core.exceptions import FieldDoesNotExist

from infraohjelmointi_api.services.CacheService import CacheService
from .BaseViewSet import BaseViewSet


class CachedLookupViewSet(BaseViewSet):
    """ViewSet that caches list() responses for lookup tables."""
    
    def get_cache_key_name(self) -> str:
        return self.get_serializer_class().Meta.model.__name__
    
    def list(self, request, *args, **kwargs):
        cache_key = self.get_cache_key_name()
        
        cached_data = CacheService.get_lookup(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        
        response = super().list(request, *args, **kwargs)
        
        if response.status_code == 200:
            CacheService.set_lookup(cache_key, response.data)
        
        return response
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response
    
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response
    
    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response

    @action(detail=False, methods=["put"], url_path="reorder")
    def reorder(self, request):
        model = self.get_queryset().model

        try:
            model._meta.get_field("order")
        except FieldDoesNotExist:
            return Response(
                {"detail": "This model does not support ordering."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data

        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a list of objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for item in data:
                if "id" not in item or "order" not in item:
                    return Response(
                        {"detail": "Each item must contain 'id' and 'order'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                self.get_queryset().filter(id=item["id"]).update(
                    order=item["order"]
                )

        CacheService.invalidate_lookup(self.get_cache_key_name())

        return Response(
            {"status": "order updated"},
            status=status.HTTP_200_OK
        )


