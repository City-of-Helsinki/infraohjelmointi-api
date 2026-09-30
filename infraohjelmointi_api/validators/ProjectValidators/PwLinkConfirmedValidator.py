from infraohjelmointi_api.services.ProjectWiseService import ProjectWiseService
from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class PwLinkConfirmedValidator(BaseValidator):
    """
    IO-935: refuse to set or change a project's hkrId unless the client has
    confirmed which PW project it points to.

    Every save of a programmed project overwrites PW fields (including
    PROJECT_Kohde), so a mistyped hkrId would silently overwrite another project
    in PW. The UI looks the PW project up with GET /projects/pw-project-name/,
    shows its name and, on OK, sends the same id back as `confirmedHkrId`.

    Runs on the validated values, so ids are compared as the ints they are
    saved as ("0123", "1234.0" and 1234 are all 1234), and on every write path
    through ProjectCreateSerializer (create, PUT, PATCH, bulk update). Clearing
    the hkrId or re-sending the current one needs no confirmation. Skipped when
    PW sync is disabled, since nothing is written to PW then.
    """

    requires_context = True

    def __call__(self, all_fields, serializer) -> None:
        new_hkr_id = all_fields.get("hkrId", None)
        if new_hkr_id is None or not ProjectWiseService.is_sync_enabled():
            return

        # in case of multiple projects being patched at the same time
        # projectId tells which one this is
        project = self.getProjectInstance(all_fields.get("projectId", None), serializer=serializer)
        current_hkr_id = project.hkrId if project is not None else None
        if new_hkr_id == current_hkr_id:
            return

        if all_fields.get("confirmedHkrId", None) != new_hkr_id:
            raise ValidationError({"hkrId": ["PW_LINK_NOT_CONFIRMED"]})
