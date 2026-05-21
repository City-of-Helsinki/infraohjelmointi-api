import logging

logger = logging.getLogger(__name__)


def get_programmer_from_hierarchy(project_class, max_depth=10):
    if not project_class:
        return None
    visited = set()
    current = project_class
    depth = 0
    while current:
        if current.id in visited:
            raise ValueError(f"Cycle detected in ProjectClass hierarchy at class '{current.name}' (ID: {current.id})")
        visited.add(current.id)
        depth += 1
        if depth > max_depth:
            raise ValueError(f"Maximum hierarchy depth ({max_depth}) exceeded")
        if current.defaultProgrammer:
            return current.defaultProgrammer
        current = current.parent
    return None


def build_location_programmer_lookup():
    """
    Build a {class_name: ProjectProgrammer} lookup from programmer-view
    ProjectClass rows with a defaultProgrammer (IO-411).

    Suurpiiri names appear in multiple rows (one per project type) and are
    expected to all point at the same programmer; on drift we pick the oldest
    deterministically and warn so the data can be reconciled.
    """
    from infraohjelmointi_api.models import ProjectClass

    rows = (
        ProjectClass.objects
        .filter(forCoordinatorOnly=False, defaultProgrammer__isnull=False)
        .order_by("createdDate")
        .values_list("id", "name", "defaultProgrammer_id")
    )

    by_name: dict[str, tuple] = {}
    conflicts: dict[str, set] = {}
    for cls_id, name, programmer_id in rows:
        existing = by_name.get(name)
        if existing is None:
            by_name[name] = (programmer_id, cls_id)
        elif existing[0] != programmer_id:
            conflicts.setdefault(name, {existing[0]}).add(programmer_id)

    for name, programmer_ids in conflicts.items():
        logger.warning(
            "Multiple programmer-view ProjectClass rows named %r resolve to "
            "different defaultProgrammers (%s). Picking the oldest "
            "deterministically; please reconcile the data.",
            name, sorted(str(pid) for pid in programmer_ids),
        )

    if not by_name:
        return {}

    from infraohjelmointi_api.models import ProjectProgrammer

    programmer_ids = {pid for pid, _ in by_name.values()}
    programmers = {
        p.id: p
        for p in ProjectProgrammer.objects.filter(id__in=programmer_ids)
    }

    return {
        name: programmers[pid]
        for name, (pid, _cls_id) in by_name.items()
        if pid in programmers
    }


def get_programmer_from_name_hierarchy(
    node,
    max_depth=10,
    name_lookup=None,
):
    """
    Walk a generic ``parent``-linked hierarchy and look up each node's
    ``name`` in a programmer-view ProjectClass lookup (IO-411).

    Used by both ProjectLocation and ProjectDistrict chains; both models
    expose ``id``, ``name`` and ``parent``, which is all this walker needs.
    Pass ``name_lookup`` (from ``build_location_programmer_lookup``) to share
    the lookup across many calls; it is built lazily otherwise.
    """
    if not node:
        return None

    if name_lookup is None:
        name_lookup = build_location_programmer_lookup()

    if not name_lookup:
        return None

    visited = set()
    current = node
    depth = 0
    while current:
        if current.id in visited:
            raise ValueError(
                "Cycle detected in name hierarchy at "
                f"'{current.name}' (ID: {current.id})"
            )
        visited.add(current.id)
        depth += 1
        if depth > max_depth:
            raise ValueError(
                f"Maximum name hierarchy depth ({max_depth}) exceeded"
            )

        programmer = name_lookup.get(current.name)
        if programmer is not None:
            return programmer

        current = current.parent

    logger.debug(
        "No default programmer found while walking the name hierarchy "
        "starting at '%s' (ID: %s).",
        getattr(node, "name", None),
        getattr(node, "id", None),
    )
    return None


def get_programmer_from_location_hierarchy(
    project_location,
    max_depth=10,
    name_lookup=None,
):
    """Backwards-compatible alias for :func:`get_programmer_from_name_hierarchy`."""
    return get_programmer_from_name_hierarchy(
        project_location, max_depth=max_depth, name_lookup=name_lookup
    )


def get_default_programmer_for_project(project_class, project_location=None, name_lookup=None):
    """
    Resolve the default programmer for a project: walk the class parent chain
    first, then fall back to the location chain (IO-411). A corrupted class
    hierarchy must not prevent the location chain from being consulted.
    """
    try:
        programmer = get_programmer_from_hierarchy(project_class)
    except ValueError as exc:
        logger.error(
            "ProjectClass hierarchy error while resolving default programmer "
            "for class '%s' (ID: %s): %s. Falling back to location chain.",
            getattr(project_class, "name", None),
            getattr(project_class, "id", None),
            exc,
        )
        programmer = None

    if programmer:
        return programmer
    return get_programmer_from_name_hierarchy(project_location, name_lookup=name_lookup)
