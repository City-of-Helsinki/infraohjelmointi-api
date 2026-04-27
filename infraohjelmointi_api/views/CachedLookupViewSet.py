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
    When project_field is set and a referenced item is updated or deleted,
    a hidden copy of the old item is created for completed/warranty projects.

    Model shapes:
        ['value']                                  — simple lookup (default)
        ['firstName', 'lastName']                  — project programmer model
        ['firstName', 'lastName', 'email', 'phone', 'title']  — person model

    project_field can be either a single string (one Project FK referencing
    this lookup) or an iterable of strings (multiple FKs, e.g. Person is
    referenced by both `personPlanning` and `personConstruction`).
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

    def _project_field_names(self) -> tuple:
        """Normalize project_field (str | iterable | None) to a tuple of field names."""
        if not self.project_field:
            return ()
        if isinstance(self.project_field, str):
            return (self.project_field,)
        return tuple(self.project_field)

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
        """Return (old_snapshot, ids_by_field) if project_field is set, else (None, {}).

        ids_by_field maps each FK field name to the list of completed/warranty
        project IDs that reference this instance via that field.
        """
        fields = self._project_field_names()
        if not fields:
            return None, {}
        old_snapshot = self._snapshot_fields(instance)
        ids_by_field = {
            field: list(Project.objects.filter(
                **{field: instance},
                phase__value__in=self.PRESERVED_PHASES,
            ).values_list('id', flat=True))
            for field in fields
        }
        return old_snapshot, ids_by_field

    def _apply_preservation(self, instance, old_snapshot, ids_by_field):
        """Create a hidden copy with old field values and repoint completed projects to it."""
        if not ids_by_field or not any(ids_by_field.values()):
            return
        instance.refresh_from_db()
        if not self._has_changed(old_snapshot, instance):
            return
        model = self.get_queryset().model
        new_item = model.objects.create(**old_snapshot, deleted=True)
        for field, project_ids in ids_by_field.items():
            if project_ids:
                Project.objects.filter(id__in=project_ids).update(**{field: new_item})

    def update(self, request, *args, **kwargs):
        old_snapshot, ids_by_field = self._preserve_for_completed_projects(
            self.get_object()
        )
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            self._apply_preservation(self.get_object(), old_snapshot, ids_by_field)
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response

    def partial_update(self, request, *args, **kwargs):
        old_snapshot, ids_by_field = self._preserve_for_completed_projects(
            self.get_object()
        )
        response = super().partial_update(request, *args, **kwargs)
        if response.status_code == 200:
            self._apply_preservation(self.get_object(), old_snapshot, ids_by_field)
            CacheService.invalidate_lookup(self.get_cache_key_name())
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        fields = self._project_field_names()

        if fields:
            model = self.get_queryset().model
            snapshot = self._snapshot_fields(instance)
            ids_to_preserve_by_field = {
                field: list(Project.objects.filter(
                    **{field: instance},
                    phase__value__in=self.PRESERVED_PHASES,
                ).values_list('id', flat=True))
                for field in fields
            }
            any_to_preserve = any(ids_to_preserve_by_field.values())

            with transaction.atomic():
                preserved_copy = (
                    model.objects.create(**snapshot, deleted=True)
                    if any_to_preserve else None
                )
                for field, preserve_ids in ids_to_preserve_by_field.items():
                    if preserve_ids:
                        Project.objects.filter(id__in=preserve_ids).update(
                            **{field: preserved_copy}
                        )
                    Project.objects.filter(**{field: instance}).exclude(
                        id__in=preserve_ids
                    ).update(**{field: None})

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
