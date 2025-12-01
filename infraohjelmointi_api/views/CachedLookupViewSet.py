from rest_framework.response import Response

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




