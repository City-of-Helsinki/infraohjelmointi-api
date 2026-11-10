def get_self_and_descendant_ids(model_class, root_ids, **filters):
    """
    Collect root_ids plus every descendant reachable through the model's
    self-referential `parent` foreign key, walking ids level by level
    instead of matching on the denormalized `path` string.

    `path` is built by migrations and import scripts and can drift from the
    real `parent` links (see IO-822/IO-960, where a migration gave the
    Itaekeskus coordinator classes paths that did not start with their
    parent's path). A `path__startswith` lookup then silently drops such
    rows from hierarchy lookups. Walking `parent_id` instead is correct
    regardless of what `path` happens to contain. Both ProjectClass and
    ProjectLocation expose a self-referential `parent`, so this works for
    either model.

    Any extra keyword filters (e.g. forCoordinatorOnly=True) are applied at
    every level of the walk, matching how the root_ids were selected.
    """
    ids = list(dict.fromkeys(root_ids))
    frontier = ids
    while frontier:
        children = list(
            model_class.objects.filter(parent_id__in=frontier, **filters)
            .exclude(id__in=ids)
            .values_list("id", flat=True)
        )
        ids.extend(children)
        frontier = children
    return ids
