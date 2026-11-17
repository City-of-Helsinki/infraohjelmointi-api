from datetime import date

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.db.models import Q

from ..models import (
    ConstructionHandover,
    Person,
    Project,
    ProjectProgrammeBasicInfo,
    TalpaProjectOpening,
    Task,
)
from .CacheService import CacheService

RETENTION_YEARS = 5

# Only projects that have reached the warranty phase or are completed are due.
# A stale estWarrantyPhaseEnd on a project still in an earlier phase is not.
RETENTION_PHASES = ("warrantyPeriod", "completed")

PROGRAMME_NAME_FIELDS = ("personsInvolved", "projectProgrammeCompiler", "inspector")
HANDOVER_PERSON_FIELDS = ("personPlanning", "personFinancing", "constructionProjectManager")
TALPA_CONTACT_FIELDS = ("responsiblePerson", "responsiblePersonEmail", "responsiblePersonPhone")
TALPA_PERSON_FIELDS = ("createdBy", "updatedBy")
ANONYMIZED_PERSON_VALUES = {
    "firstName": "",
    "lastName": "",
    "email": "",
    "title": "",
    "phone": "",
    "deleted": True,
}


def retention_due_date(project: Project) -> date:
    return project.estWarrantyPhaseEnd + relativedelta(years=RETENTION_YEARS)


def _talpa_personal_data_filter() -> Q:
    talpa_filter = Q(excelFile__gt="")
    for field in TALPA_CONTACT_FIELDS:
        talpa_filter |= Q(**{f"{field}__gt": ""})
    for field in TALPA_PERSON_FIELDS:
        talpa_filter |= Q(**{f"{field}__isnull": False})
    return talpa_filter


def personal_data_summary(project: Project) -> dict:
    """Counts of personal data still attached to a project, keyed by category."""
    handovers = ConstructionHandover.objects.filter(project=project)
    handover_person_filter = Q()
    for field in HANDOVER_PERSON_FIELDS:
        handover_person_filter |= Q(**{f"{field}__isnull": False})

    programme_name_filter = Q()
    for field in PROGRAMME_NAME_FIELDS:
        programme_name_filter |= Q(**{f"{field}__gt": ""})

    return {
        "projectPersons": (
            int(project.personPlanning_id is not None)
            + int(project.personConstruction_id is not None)
            + project.otherPersons.count()
            + project.favPersons.count()
        ),
        # The project's link to a programmer; the programmer list entry itself is kept
        "programmers": int(project.personProgramming_id is not None),
        "handovers": handovers.filter(handover_person_filter).count(),
        "taskPersons": Task.objects.filter(projectId=project, person__isnull=False).count(),
        "programmeNames": ProjectProgrammeBasicInfo.objects.filter(
            project_programme__project=project
        ).filter(programme_name_filter).count(),
        "talpaContacts": TalpaProjectOpening.objects.filter(project=project)
        .filter(_talpa_personal_data_filter())
        .count(),
    }


def overdue_projects(today: date | None = None) -> list[tuple[Project, dict]]:
    """Projects whose retention period has passed and that still hold personal data."""
    today = today or date.today()
    cutoff = today - relativedelta(years=RETENTION_YEARS)
    candidates = (
        Project.objects.filter(
            estWarrantyPhaseEnd__isnull=False,
            estWarrantyPhaseEnd__lte=cutoff,
            phase__value__in=RETENTION_PHASES,
        )
        .order_by("estWarrantyPhaseEnd", "name")
    )

    overdue = []
    for project in candidates:
        summary = personal_data_summary(project)
        if any(summary.values()):
            overdue.append((project, summary))
    return overdue


def is_past_retention(project: Project, today: date | None = None) -> bool:
    if project.estWarrantyPhaseEnd is None:
        return False
    if project.phase is None or project.phase.value not in RETENTION_PHASES:
        return False
    return retention_due_date(project) <= (today or date.today())


def _is_person_referenced(person: Person) -> bool:
    for relation in Person._meta.related_objects:
        if relation.related_model._base_manager.filter(**{relation.field.name: person}).exists():
            return True
    return False


def _collect_person_ids(project: Project) -> set:
    handovers = ConstructionHandover.objects.filter(project=project)
    handover_history = ConstructionHandover.history.model.objects.filter(id__in=handovers.values("id"))
    talpa_openings = TalpaProjectOpening.objects.filter(project=project)

    person_ids = {project.personPlanning_id, project.personConstruction_id}
    person_ids.update(project.otherPersons.values_list("id", flat=True))
    person_ids.update(project.favPersons.values_list("id", flat=True))
    person_ids.update(Task.objects.filter(projectId=project).values_list("person_id", flat=True))
    for rows in (handovers, handover_history):
        person_ids.update(rows.values_list("personPlanning_id", flat=True))
        person_ids.update(rows.values_list("constructionProjectManager_id", flat=True))
    for field in TALPA_PERSON_FIELDS:
        person_ids.update(talpa_openings.values_list(f"{field}_id", flat=True))
    person_ids.discard(None)
    return person_ids


def clear_personal_data(project: Project) -> dict:
    """
    Remove personal data from one project and anonymize persons nothing else uses.

    The project's programmer link is removed, but the programmer list entry
    (ProjectProgrammer) and its linked Person are kept: that list is the shared
    directory of programmers, not contact data owned by this project. Free-text
    fields outside the structured person links are not touched.

    Runs in a transaction; callers that write an audit entry should wrap both
    in one outer transaction so neither is committed without the other.
    """
    with transaction.atomic():
        removed = personal_data_summary(project)
        person_ids = _collect_person_ids(project)

        Project.objects.filter(pk=project.pk).update(
            personPlanning=None,
            personConstruction=None,
            personProgramming=None,
        )
        project.otherPersons.clear()
        project.favPersons.clear()

        handover_clear = dict.fromkeys(HANDOVER_PERSON_FIELDS, None)
        handovers = ConstructionHandover.objects.filter(project=project)
        handovers.update(**handover_clear)
        ConstructionHandover.history.model.objects.filter(id__in=handovers.values("id")).update(**handover_clear)

        Task.objects.filter(projectId=project).update(person=None)

        programme_clear = dict.fromkeys(PROGRAMME_NAME_FIELDS, "")
        ProjectProgrammeBasicInfo.objects.filter(project_programme__project=project).update(**programme_clear)
        ProjectProgrammeBasicInfo.history.model.objects.filter(
            project_programme__project=project
        ).update(**programme_clear)

        # The Talpa Excel is generated on request and never stored by the app,
        # so clearing the field leaves no file behind.
        TalpaProjectOpening.objects.filter(project=project).update(
            **dict.fromkeys(TALPA_CONTACT_FIELDS + TALPA_PERSON_FIELDS, None),
            excelFile=None,
        )

        anonymized = 0
        for person in Person._base_manager.filter(id__in=person_ids):
            if not _is_person_referenced(person):
                Person._base_manager.filter(pk=person.pk).update(**ANONYMIZED_PERSON_VALUES)
                anonymized += 1

        if anonymized:
            transaction.on_commit(lambda: CacheService.invalidate_lookup(Person.__name__))

    return {"removed": removed, "anonymizedPersons": anonymized}
