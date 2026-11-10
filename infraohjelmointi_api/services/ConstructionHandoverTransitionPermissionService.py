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

        # Rule: stepping back needs the same rights as the forward step into the current status.
        rule_status = requested_status
        if (
            current_status in STATUS_ORDER
            and requested_status in STATUS_ORDER
            and STATUS_ORDER.index(requested_status) < STATUS_ORDER.index(current_status)
        ):
            rule_status = current_status

        # Rule: must be planning person; role gate is handled by endpoint permission classes.
        if rule_status == "SUBMITTED_TO_PROGRAMMER":
            return ProjectPersonAuthorizationService.is_person_planning_for_project(
                user=user,
                project=project,
            )

        # Rule: explicit role-based transition.
        if rule_status == "SUBMITTED_TO_CONSTRUCTION":
            return bool(is_programmer)

        # Rule: explicit role-based transition.
        if rule_status == "PROJECT_MANAGER_NAMED":
            return bool(is_construction_management_lead)

        # Rule: explicit role-based transition.
        if rule_status == "MOVED_TO_CONSTRUCTION_PREPARATION":
            return (
                bool(is_project_manager)
                and ProjectPersonAuthorizationService.is_person_construction_for_project(
                    user=user,
                    project=project,
                )
            )

        return False
