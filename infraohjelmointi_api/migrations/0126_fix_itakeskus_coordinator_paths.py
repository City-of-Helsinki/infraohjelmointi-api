import logging

from django.db import migrations, transaction

logger = logging.getLogger(__name__)

# Fix for migration 0092_add_itakeskus_project_classes (IO-822): it hard-coded
# the coordinator rows' paths under "8 08 Projektialueiden infrarakentaminen/",
# but the coordinator-view master class is "8 08 Projektialueiden
# infrarakentaminen, Khn käytettäväksi". The parent FKs are right, but the
# coordinator sums find descendants with path__startswith=parent.path + "/",
# so 8 08 01, 8 08 02, 8 08 03 and the 8 08 total all left out their Itäkeskus
# subtree (e.g. 8 08 03 Puistot ja liikunta-alueet showed 8050 instead of 8350).
COORDINATOR_NAMES = [
    "8 08 01 12 Itäkeskus",
    "8 08 02 12 Itäkeskus",
    "8 08 03 12 Itäkeskus",
]


def fix_itakeskus_coordinator_paths(apps, schema_editor):
    project_class_model = apps.get_model("infraohjelmointi_api", "ProjectClass")

    changed = False
    for project_class in project_class_model.objects.filter(
        name__in=COORDINATOR_NAMES, forCoordinatorOnly=True
    ).select_related("parent"):
        parent = project_class.parent
        if parent is None or not parent.forCoordinatorOnly or not parent.path:
            print(f"\n  0126: skipped {project_class.name}: no coordinator parent with a path")
            continue
        expected = f"{parent.path}/{project_class.name}"
        if project_class.path == expected:
            print(f"\n  0126: {project_class.name} already correct")
            continue

        # Keep any subtree consistent too (none exists today).
        if project_class.path:
            old_prefix = f"{project_class.path}/"
            for child in project_class_model.objects.filter(path__startswith=old_prefix):
                child.path = f"{expected}/{child.path[len(old_prefix):]}"
                child.save(update_fields=["path"])

        print(f"\n  0126: {project_class.path} -> {expected}")
        project_class.path = expected
        project_class.save(update_fields=["path"])
        changed = True

    if changed:
        # After commit, so no pod can re-cache a sum from the old paths
        # between the clear and the commit.
        transaction.on_commit(_clear_cached_sums)


def _clear_cached_sums():
    """Financial sums for these classes may be cached for up to CACHE_TIMEOUT.

    A cache failure must not fail the deploy; the entries then expire on
    their own.
    """
    from django.core.cache import cache

    try:
        cache.clear()
    except Exception:
        logger.warning("Could not clear the cache after fixing Itäkeskus paths", exc_info=True)


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0125_alter_constructionhandover_linkcontractboundaries_and_more"),
    ]

    operations = [
        migrations.RunPython(
            fix_itakeskus_coordinator_paths,
            # The old paths were wrong; there is nothing worth restoring.
            migrations.RunPython.noop,
        ),
    ]
