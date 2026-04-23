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
    """ViewSet that caches list() responses for lookup tables.

    Supports three model shapes via the `preserved_fields` class attribute.
    When a project_field is set and a referenced item is updated or deleted,
    a hidden copy of the old item is created for completed/warranty projects.

    Model shapes:
        ['value']                                  — simple lookup (default)
        ['firstName', 'lastName']                  — project programmer model
        ['firstName', 'lastName', 'email', 'phone', 'title']  — person model
    """

    preserved_fields = ['value']
    PRESERVED_PHASES = ('completed', 'warrantyPeriod')
    project_field = None

    def get_cache_key_name(self) -> str:
        return self.get_serializer_class().Meta.model.__name__

    def get_queryset(self):
        queryset = super().get_queryset()
        model = self.get_serializer_class().Meta.model
        if hasattr(model, "deleted"):
            queryset = queryset.exclude(deleted=True)
        return queryset

    def _snapshot_fields(self, instance) -> dict:
        return {field: getattr(instance, field) for field in self.preserved_fields}

    def _has_changed(self, old_snapshot: dict, instance) -> bool:
        return any(old_snapshot[field] != getattr(instance, field) for field in self.preserved_fields)

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

    def _preserve_for_completed_projects(self, instance):
        """Return (old_snapshot, completed_project_ids) if project_field is set, else (None, [])."""
        if not self.project_field:
            return None, []
        old_snapshot = self._snapshot_fields(instance)
        completed_project_ids = list(Project.objects.filter(
            **{self.project_field: instance},
            phase__value__in=self.PRESERVED_PHASES
        ).values_list('id', flat=True))
        return old_snapshot, completed_project_ids

    def _apply_preservation(self, instance, old_snapshot, completed_project_ids):
        """Create a hidden copy with old field values and repoint completed projects to it."""
        if not (self.project_field and completed_project_ids):
            return
        instance.refresh_from_db()
        if self._has_changed(old_snapshot, instance):
            model = self.get_queryset().model
            new_item = model.objects.create(**old_snapshot, deleted=True)
            Project.objects.filter(id__in=completed_project_ids).update(
                **{self.project_field: new_item}
            )

    def update(self, request, *args, **kwargs):
        old_snapshot, completed_project_ids = self._preserve_for_completed_projects(
            self.get_object()
        )
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            self._apply_preservation(self.get_object(), old_snapshot, completed_project_ids)
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response

    def partial_update(self, request, *args, **kwargs):
        old_snapshot, completed_project_ids = self._preserve_for_completed_projects(
            self.get_object()
        )
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            self._apply_preservation(self.get_object(), old_snapshot, completed_project_ids)
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if self.project_field:
            model = self.get_queryset().model
            snapshot = self._snapshot_fields(instance)
            project_ids_to_preserve = list(Project.objects.filter(
                **{self.project_field: instance},
                phase__value__in=self.PRESERVED_PHASES
            ).values_list('id', flat=True))

            with transaction.atomic():
                if project_ids_to_preserve:
                    new_item = model.objects.create(**snapshot, deleted=True)
                    Project.objects.filter(
                        id__in=project_ids_to_preserve
                    ).update(**{self.project_field: new_item})
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
                self.get_queryset().filter(id=item["id"]).update(order=item["order"])

        CacheService.invalidate_lookup(self.get_cache_key_name())
        return Response({"status": "order updated"}, status=status.HTTP_200_OK)
