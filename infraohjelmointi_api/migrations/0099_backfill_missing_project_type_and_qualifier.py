from django.db import migrations
from django.db.models import Q
import re


NEW_CONSTRUCTION_TYPE = "newConstruction"
BASIC_IMPROVEMENT_TYPE = "basicImprovement"

STREET_QUALIFIER = "street"
PARK_QUALIFIER = "park"
PRE_CONSTRUCTION_QUALIFIER = "preConstruction"
SPORTS_QUALIFIER = "sports"
SPECIALTY_STRUCTURES_QUALIFIER = "spesialtyStructures"


# Mirrors ProjectClassSerializer name transformation behavior for migration-safe matching.
SUFFIX_PATTERN = re.compile(
    r",\s*(?:Kylkn|kylkn|Kaupunkiympäristölautakunnan|kaupunkiympäristölautakunnan|"
    r"KHN|Khn|khn|Kaupunginhallituksen|kaupunginhallituksen)\s+käytettäväksi"
)
NUMBERING_PATTERN = re.compile(r"^(\d+\s+\d+(?:\s+\d+){0,2})")
LEADING_CODE_PATTERN = re.compile(r"^(?:\d+\s*){1,4}\s*")


# Number + name groups for explicit matching.
NEW_CONSTRUCTION_CLASS_KEYS = {
    "8010301 muu esirakentaminen",
    "8030101 uudisrakentaminen",
    "8040101 uudet puistot",
    "8040102 uudet liikuntapaikat ja ulkoilualueet",
    "808 projektialueiden infrarakentaminen",
    "8090102 kadut uudisrakentaminen",
    "8090103 puistot uudisrakentaminen",
    "8090202 kadut uudisrakentaminen",
    "8090203 puistot uudisrakentaminen",
    "8090302 kadut uudisrakentaminen",
    "8090303 puistot uudisrakentaminen",
    "8090402 kadut uudisrakentaminen",
    "8090403 puistot uudisrakentaminen",
    "810 suuret liikennehankkeet",
}

STREET_CLASS_KEYS = {
    "803 kadut ja liikennevaylat",
    "8030103 muut investoinnit",
    "80802 kadut",
    "8090102 kadut uudisrakentaminen",
    "8090102 kadut peruskorjaus",
    "8090202 kadut uudisrakentaminen",
    "8090202 kadut peruskorjaus",
    "8090302 kadut uudisrakentaminen",
    "8090302 kadut peruskorjaus",
    "8090402 kadut uudisrakentaminen",
    "8090402 kadut peruskorjaus",
    "8100103 liittyvat kadut ja liikennevaylat",
    "81003 sornaisten tunneli",
    "8100402 liittyvat kadut ja liikennevaylat",
}

PARK_CLASS_KEYS = {
    "8040101 uudet puistot",
    "8040101 puistojen peruskorjaus",
    "80803 puistot ja liikunta-alueet",
    "8090103 puistot uudisrakentaminen",
    "8090103 puistot peruskorjaus",
    "8090203 puistot uudisrakentaminen",
    "8090203 puistot peruskorjaus",
    "8090303 puistot uudisrakentaminen",
    "8090303 puistot peruskorjaus",
    "8090403 puistot uudisrakentaminen",
    "8090403 puistot peruskorjaus",
}

PRE_CONSTRUCTION_CLASS_KEYS = {
    "801 kiintea omaisuus",
    "80801 esirakentaminen",
    "8090101 esirakentaminen",
    "8090201 esirakentaminen",
    "8090301 esirakentaminen",
    "8090401 esirakentaminen",
    "8100102 liittyva esirakentaminen",
    "8100401 liittyva esirakentaminen",
}

SPORTS_CLASS_KEYS = {
    "8040102 uudet liikuntapaikat ja ulkoilualueet",
    "8040102 liikunta- ja ulkoilualueiden peruskorjaus",
    "8090103 liikunta-alueet",
    "8090203 liikunta-alueet",
    "8090303 liikunta-alueet",
    "8090403 liikunta-alueet",
}


def normalize_text(value):
    if not value:
        return ""
    normalized = " ".join(str(value).strip().lower().split())
    normalized = normalized.replace("ä", "a").replace("ö", "o")
    return normalized


def clean_class_name(name):
    if not name:
        return ""
    return SUFFIX_PATTERN.sub("", str(name)).strip()


def normalize_display_name_for_match(name):
    clean_name = clean_class_name(name)
    without_numbering = LEADING_CODE_PATTERN.sub("", clean_name).strip()
    normalized = normalize_text(without_numbering)
    normalized = normalized.replace(" - ", "-")
    return normalized


def build_number_name_key(value):
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    digit_match = re.search(r"[0-9][0-9 ]+", text)
    if not digit_match:
        return None

    digits = re.sub(r"\D", "", digit_match.group(0))
    if not digits:
        return None

    name_part = normalize_display_name_for_match(text)
    if not name_part:
        return None

    return f"{digits} {name_part}"


def extract_numbering(name):
    clean_name = clean_class_name(name)
    match = NUMBERING_PATTERN.match(clean_name)
    return match.group(1) if match else None


def get_coordinator_numbering(project_class):
    try:
        coordinator = project_class.coordinatorClass
    except Exception:
        return None

    for _ in range(10):
        if not coordinator:
            break
        numbering = extract_numbering(getattr(coordinator, "name", ""))
        if numbering:
            return numbering
        coordinator = getattr(coordinator, "parent", None)

    return None


def find_ancestor_numbering(project_class):
    parent = getattr(project_class, "parent", None)
    for _ in range(10):
        if not parent or getattr(parent, "forCoordinatorOnly", False):
            break

        parent_raw_numbering = extract_numbering(getattr(parent, "name", ""))
        parent_coordinator_numbering = get_coordinator_numbering(parent)

        if (
            parent_coordinator_numbering
            and parent_raw_numbering != parent_coordinator_numbering
        ):
            return parent_coordinator_numbering

        parent = getattr(parent, "parent", None)

    return None


def is_more_specific(child_numbering, ancestor_numbering):
    return child_numbering.startswith(ancestor_numbering) and len(child_numbering) > len(
        ancestor_numbering
    )


def get_numbering_to_apply(project_class):
    class_name = normalize_text(getattr(project_class, "name", ""))
    # Keep numbering behavior aligned with ProjectClassSerializer display rules.
    if getattr(project_class, "forCoordinatorOnly", False) or "suurpiiri" in class_name:
        return None

    my_numbering = get_coordinator_numbering(project_class)
    if not my_numbering:
        return None

    ancestor_numbering = find_ancestor_numbering(project_class)
    if not ancestor_numbering:
        return my_numbering

    if is_more_specific(my_numbering, ancestor_numbering):
        return my_numbering

    return None


def get_class_display_name(project_class):
    base_name = clean_class_name(getattr(project_class, "name", ""))
    numbering = get_numbering_to_apply(project_class)
    if not numbering:
        return base_name

    name_without_numbering = NUMBERING_PATTERN.sub("", base_name).strip()
    return f"{numbering} {name_without_numbering}".strip()


def iter_class_hierarchy(project_class, max_depth=10):
    # Traverse selected class and parents with cycle/depth guards for migration safety.
    current = project_class
    seen = set()

    for _ in range(max_depth):
        if not current:
            break

        class_id = getattr(current, "id", None)
        if class_id is not None:
            if class_id in seen:
                break
            seen.add(class_id)

        yield current
        current = getattr(current, "parent", None)


def get_number_name_keys(project_class):
    if not project_class:
        return set()

    # Build a lookup key set from the direct class and all ancestors so inherited
    # classifications can still resolve type/qualifier values.
    keys = set()
    for current_class in iter_class_hierarchy(project_class):
        display_name = get_class_display_name(current_class)
        raw_name = getattr(current_class, "name", "")
        path = getattr(current_class, "path", "")

        for candidate in [display_name, raw_name]:
            key = build_number_name_key(candidate)
            if key:
                keys.add(key)

        if path:
            for segment in str(path).split("/"):
                key = build_number_name_key(segment)
                if key:
                    keys.add(key)

    return keys


def resolve_project_type_value(project_class):
    if not project_class:
        return BASIC_IMPROVEMENT_TYPE

    number_name_keys = get_number_name_keys(project_class)
    if number_name_keys.intersection(NEW_CONSTRUCTION_CLASS_KEYS):
        return NEW_CONSTRUCTION_TYPE

    return BASIC_IMPROVEMENT_TYPE


def resolve_project_type_qualifier_value(project_class):
    if not project_class:
        return None

    number_name_keys = get_number_name_keys(project_class)
    raw_name = normalize_text(getattr(project_class, "name", ""))

    # Name-based exceptional mapping for special structures.
    if "siltojen peruskorjaus ja uusiminen" in raw_name:
        return SPECIALTY_STRUCTURES_QUALIFIER
    if "tulvasuojelu ja rantarakenteet" in raw_name:
        return SPECIALTY_STRUCTURES_QUALIFIER

    if number_name_keys.intersection(STREET_CLASS_KEYS):
        return STREET_QUALIFIER

    if number_name_keys.intersection(PRE_CONSTRUCTION_CLASS_KEYS):
        return PRE_CONSTRUCTION_QUALIFIER

    if number_name_keys.intersection(SPORTS_CLASS_KEYS):
        return SPORTS_QUALIFIER

    if number_name_keys.intersection(PARK_CLASS_KEYS):
        return PARK_QUALIFIER

    return None


def backfill_missing_project_type_and_qualifier(apps, schema_editor):
    Project = apps.get_model("infraohjelmointi_api", "Project")
    ProjectType = apps.get_model("infraohjelmointi_api", "ProjectType")
    ProjectTypeQualifier = apps.get_model("infraohjelmointi_api", "ProjectTypeQualifier")

    project_type_ids = dict(
        ProjectType.objects.filter(
            value__in=[NEW_CONSTRUCTION_TYPE, BASIC_IMPROVEMENT_TYPE]
        ).values_list("value", "id")
    )

    required_types = [NEW_CONSTRUCTION_TYPE, BASIC_IMPROVEMENT_TYPE]
    missing_types = [value for value in required_types if value not in project_type_ids]
    if missing_types:
        raise RuntimeError(
            f"Required ProjectType values missing for migration: {', '.join(missing_types)}"
        )

    qualifier_values = [
        STREET_QUALIFIER,
        PARK_QUALIFIER,
        PRE_CONSTRUCTION_QUALIFIER,
        SPORTS_QUALIFIER,
        SPECIALTY_STRUCTURES_QUALIFIER,
    ]
    qualifier_ids = dict(
        ProjectTypeQualifier.objects.filter(value__in=qualifier_values).values_list(
            "value", "id"
        )
    )

    pending_updates = []
    # Only touch rows that still have missing target fields.
    queryset = Project.objects.filter(
        Q(type__isnull=True) | Q(typeQualifier__isnull=True)
    ).select_related("projectClass")

    for project in queryset.iterator(chunk_size=1000):
        changed = False

        if project.type_id is None:
            type_value = resolve_project_type_value(project.projectClass)
            project.type_id = project_type_ids[type_value]
            changed = True

        if project.typeQualifier_id is None:
            qualifier_value = resolve_project_type_qualifier_value(project.projectClass)
            qualifier_id = qualifier_ids.get(qualifier_value)
            if qualifier_id:
                project.typeQualifier_id = qualifier_id
                changed = True

        if changed:
            pending_updates.append(project)

        if len(pending_updates) >= 1000:
            # Batch updates to keep memory use and transaction overhead bounded.
            Project.objects.bulk_update(pending_updates, ["type", "typeQualifier"])
            pending_updates = []

    if pending_updates:
        Project.objects.bulk_update(pending_updates, ["type", "typeQualifier"])


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0098_merge_20260415_1417"),
    ]

    operations = [
        migrations.RunPython(
            backfill_missing_project_type_and_qualifier,
            migrations.RunPython.noop,
        ),
    ]
