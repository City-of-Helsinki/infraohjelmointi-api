from django.shortcuts import get_object_or_404
from ..models import CoordinatorNote
class CoordinatorNoteService:

    def create(self, request):
        planningClassId = request.get("planningClassId")
        updatedById = request.get("updatedById")
        CoordinatorNote.create(
            coordinatorNote=request.get("coordinatorNote"),
            planningClass=request.get("planningClass"),
            planningClassId=get_object_or_404(CoordinatorNote, pk=planningClassId),
            updatedByFirstName=request.get("updatedByFirstName"),
            updatedById=get_object_or_404(CoordinatorNote, pk=updatedById.id),
            updatedByLastName=request.get("updatedByLastName"),
        )

    def list_all_notes(classId) -> list[CoordinatorNote]:
        """List all coordinator notes of a project"""
        return (
            CoordinatorNote.objects.all()
            .filter(planningClassId=classId)
            .order_by("createdDate")
        )