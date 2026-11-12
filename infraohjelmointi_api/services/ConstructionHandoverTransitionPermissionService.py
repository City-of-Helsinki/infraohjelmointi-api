from ..models import ConstructionHandover
from .ProjectPersonAuthorizationService import ProjectPersonAuthorizationService


STATUS_ORDER = [choice[0] for choice in ConstructionHandover.STATUS_CHOICES]


class ConstructionHandoverTransitionPermissionService:
    @staticmethod
    def is_transition_allowed(
        requested_status,
        current_status,
        user,
        project,
        is_project_manager,
        is_programmer,
        is_construction_management_lead,
    ):
        # Rule: any handover editor may return to draft; role gate is handled by endpoint permission classes.
        if requested_status == "DRAFT":
            return True

        def can_step_into(status):
            return ConstructionHandoverTransitionPermissionService._can_step_into(
                status,
                user=user,
                project=project,
                is_project_manager=is_project_manager,
                is_programmer=is_programmer,
                is_construction_management_lead=is_construction_management_lead,
            )

        is_step_back = (
            current_status in STATUS_ORDER
            and requested_status in STATUS_ORDER
            and STATUS_ORDER.index(requested_status) < STATUS_ORDER.index(current_status)
        )
        if not is_step_back:
            return can_step_into(requested_status)

        # Rule: stepping back is allowed for whoever can step forward into or out of the current status.
        current_index = STATUS_ORDER.index(current_status)
        next_status = STATUS_ORDER[current_index + 1] if current_index + 1 < len(STATUS_ORDER) else None
        return can_step_into(current_status) or (
            next_status is not None and can_step_into(next_status)
        )

    @staticmethod
    def _can_step_into(
        status,
        user,
        project,
        is_project_manager,
        is_programmer,
        is_construction_management_lead,
    ):
        # Rule: must be planning person; role gate is handled by endpoint permission classes.
        if status == "SUBMITTED_TO_PROGRAMMER":
            return ProjectPersonAuthorizationService.is_person_planning_for_project(
                user=user,
                project=project,
            )

        # Rule: explicit role-based transition.
        if status == "SUBMITTED_TO_CONSTRUCTION":
            return bool(is_programmer)

        # Rule: explicit role-based transition.
        if status == "PROJECT_MANAGER_NAMED":
            return bool(is_construction_management_lead)

        # Rule: explicit role-based transition.
        if status == "MOVED_TO_CONSTRUCTION_PREPARATION":
            return (
                bool(is_project_manager)
                and ProjectPersonAuthorizationService.is_person_construction_for_project(
                    user=user,
                    project=project,
                )
            )

        return False
