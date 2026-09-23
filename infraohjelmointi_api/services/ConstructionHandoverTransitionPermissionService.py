from .ProjectPersonAuthorizationService import ProjectPersonAuthorizationService


class ConstructionHandoverTransitionPermissionService:
    @staticmethod
    def is_transition_allowed(
        requested_status,
        user,
        project,
        is_project_manager,
        is_programmer,
        is_construction_management_lead,
    ):
        # Rule: must be planning person; role gate is handled by endpoint permission classes.
        if requested_status == "SUBMITTED_TO_PROGRAMMER":
            return ProjectPersonAuthorizationService.is_person_planning_for_project(
                user=user,
                project=project,
            )

        # Rule: explicit role-based transition.
        if requested_status == "SUBMITTED_TO_CONSTRUCTION":
            return bool(is_programmer)

        # Rule: explicit role-based transition.
        if requested_status == "PROJECT_MANAGER_NAMED":
            return bool(is_construction_management_lead)

        # Rule: explicit role-based transition.
        if requested_status == "MOVED_TO_CONSTRUCTION_PREPARATION":
            return (
                bool(is_project_manager)
                and ProjectPersonAuthorizationService.is_person_construction_for_project(
                    user=user,
                    project=project,
                )
            )

        return False
