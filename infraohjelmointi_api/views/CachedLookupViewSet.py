from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from django.db import transaction
from django.core.exceptions import FieldDoesNotExist

from infraohjelmointi_api.services.CacheService import CacheService
from infraohjelmointi_api.models.Project import Project
from infraohjelmointi_api.models.ProjectPhase import ProjectPhase
from .BaseViewSet import BaseViewSet


class CachedLookupViewSet(BaseViewSet):
    """ViewSet that caches list() responses for lookup tables."""
    
    # Subclasses can override this to specify the field name in Project model
    project_field = None

    PRESERVED_PHASES = ('completed', 'warrantyPeriod')
    
    def get_cache_key_name(self) -> str:
        return self.get_serializer_class().Meta.model.__name__
    
    def get_queryset(self):
        queryset = super().get_queryset()
        model = self.get_serializer_class().Meta.model
        if hasattr(model, "deleted"):
            queryset = queryset.exclude(deleted=True)
        return queryset

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
        completed_project_ids = []
        if self.project_field:
            instance = self.get_object()
            old_value = instance.value
            completed_project_ids = list(Project.objects.filter(
                **{self.project_field: instance},
                phase__value__in=self.PRESERVED_PHASES
            ).values_list('id', flat=True))
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200 and self.project_field and completed_project_ids:
            instance.refresh_from_db()
            if old_value != instance.value:
                # Create hidden item with old value for completed/warranty projects
                model = self.get_queryset().model
                new_item = model.objects.create(value=old_value, deleted=True)
                Project.objects.filter(
                    id__in=completed_project_ids
                ).update(**{self.project_field: new_item})
        CacheService.invalidate_lookup(self.get_cache_key_name())
        return response
    
    def partial_update(self, request, *args, **kwargs):
        completed_project_ids = []
        if self.project_field:
            instance = self.get_object()
            old_value = instance.value
            completed_project_ids = list(Project.objects.filter(
                **{self.project_field: instance},
                phase__value__in=self.PRESERVED_PHASES
            ).values_list('id', flat=True))
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200 and self.project_field and completed_project_ids:
            instance.refresh_from_db()
            if old_value != instance.value:
                # Create hidden item with old value for completed/warranty projects
                model = self.get_queryset().model
                new_item = model.objects.create(value=old_value, deleted=True)
                Project.objects.filter(
                    id__in=completed_project_ids
                ).update(**{self.project_field: new_item})
        CacheService.invalidate_lookup(self.get_cache_key_name())
        return response
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        project_ids_to_preserve = []
        model = None
        
        if self.project_field:
            model = self.get_queryset().model
            project_ids_to_preserve = list(Project.objects.filter(
                **{self.project_field: instance},
                phase__value__in=self.PRESERVED_PHASES
            ).values_list('id', flat=True))
            
            # Handle preservation before deletion
            with transaction.atomic():
                if project_ids_to_preserve:
                    new_item = model.objects.create(value=instance.value, deleted=True)
                    Project.objects.filter(
                        id__in=project_ids_to_preserve
                    ).update(**{self.project_field: new_item})
                # Clear field for non-completed projects before deleting
                Project.objects.filter(
                    **{self.project_field: instance}
                ).exclude(id__in=project_ids_to_preserve).update(**{self.project_field: None})
        
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
