import logging
import uuid
from datetime import date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from infraohjelmointi_api.models import AuditLog, Project, User
from infraohjelmointi_api.permissions import IsPersonalDataRetentionAdmin
from infraohjelmointi_api.services.PersonalDataRetentionService import (
    clear_personal_data,
    is_past_retention,
    overdue_projects,
    retention_due_date,
)

audit_logger = logging.getLogger("audit")
AUDIT_ORIGIN = "infrahankkeiden_ohjelmointi"


class PersonalDataRetentionViewSet(viewsets.ViewSet):
    """
    Admin view of projects whose personal data is past the five-year retention
    period. Nothing is removed until an admin confirms it per project.
    """

    permission_classes = [IsAuthenticated & IsPersonalDataRetentionAdmin]

    def list(self, request):
        today = date.today()
        return Response([
            {
                "projectId": str(project.id),
                "projectName": project.name,
                "warrantyPhaseEnd": project.estWarrantyPhaseEnd.isoformat(),
                "retentionDueDate": retention_due_date(project).isoformat(),
                "personalData": summary,
            }
            for project, summary in overdue_projects(today)
        ])

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        try:
            uuid.UUID(str(pk))
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

        project = Project.objects.filter(pk=pk).first()
        if project is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not is_past_retention(project):
            return Response(
                data={"message": "Project is not past its personal data retention period"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = clear_personal_data(project)
        if any(result["removed"].values()) or result["anonymizedPersons"]:
            self._audit(request, project, result)
        return Response(
            {"projectId": str(project.id), **result},
            status=status.HTTP_200_OK,
        )

    def _audit(self, request, project, result):
        """Record the removal with counts only, never the removed names."""
        new_values = {"personalDataRetention": result}
        endpoint = request.build_absolute_uri()
        user = request.user if isinstance(request.user, User) else None

        AuditLog.objects.create(
            actor=user,
            operation="UPDATE",
            log_level="INFO",
            origin=AUDIT_ORIGIN,
            status="SUCCESS",
            project=project,
            old_values=None,
            new_values=new_values,
            endpoint=endpoint,
        )
        actor_data = {}
        if user is not None:
            actor_data = {
                "name": f"{user.first_name} {user.last_name}".strip() or user.username,
                "email": user.email,
            }
        audit_logger.info(
            f"PERSONAL_DATA_RETENTION on {project.name}",
            extra={
                "actor": actor_data,
                "operation": "UPDATE",
                "target": {"type": "project", "id": str(project.id), "name": project.name},
                "status": "SUCCESS",
                "old_values": None,
                "new_values": new_values,
                "endpoint": endpoint,
            },
        )
