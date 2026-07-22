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
        if requested_status == "SUBMITTED_TO_PROGRAMMER":
            return (
                is_project_manager
                and ProjectPersonAuthorizationService.is_person_planning_for_project(
                    user=user,
                    project=project,
                )
            )

        if requested_status == "SUBMITTED_TO_CONSTRUCTION":
            return is_programmer

        if requested_status == "PROJECT_MANAGER_NAMED":
            return is_construction_management_lead

        if requested_status == "MOVED_TO_CONSTRUCTION_PREPARATION":
            return (
                is_project_manager
                and ProjectPersonAuthorizationService.is_person_construction_for_project(
                    user=user,
                    project=project,
                )
            )

        return True
