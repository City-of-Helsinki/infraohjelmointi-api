"""
Batch computation of the ``finances`` field for class / location / group lists.

``FinancialSumSerializer.get_finance_sums`` answers one instance at a time with
4-6 queries each, so listing ~500 groups or ~300 classes costs ~1000 queries.
This service computes the same payload for a whole list with a handful of
queries: project sums are fetched once, grouped by (class, location, group),
and every instance then adds up the buckets its relation filter would match.

The matching rules mirror ``FinancialSumSerializer.get_related_projects`` and
``get_frameBudget_and_budgetChange`` exactly (including their quirks), so the
list payload is identical to the per-instance one. Keep the two in sync.
"""

from collections import defaultdict

from django.db.models import Q, Sum

from infraohjelmointi_api.models import (
    ClassFinancial,
    LocationFinancial,
    Project,
    ProjectClass,
    ProjectGroup,
    ProjectLocation,
)

YEARS = range(11)


class FinancialSumBatchService:
    def __init__(self, year: int, forced_to_frame: bool, for_coordinator: bool,
                 frame_budgets=None, class_rows=None):
        self.year = year
        self.forced_to_frame = forced_to_frame
        self.for_coordinator = for_coordinator
        self._frame_budgets = frame_budgets
        self._classes = class_rows
        self._locations = None

    def compute(self, instances: list, _type: str) -> dict:
        """Return ``{instance.id: finances}`` for every instance that can be batched.

        Instances missing from the result fall back to the per-instance path.
        """
        if _type == "ProjectGroup":
            return self._compute_groups(instances)
        if _type == "ProjectClass":
            return self._compute_classes(instances)
        if _type == "ProjectLocation":
            return self._compute_locations(instances)
        return {}

    # ------------------------------------------------------------------ data

    def _project_buckets(self, **filters) -> list:
        """Programmed-project sums grouped by (class, location, group).

        Same expressions as the per-instance aggregate, including the join on
        finances: ``budgetOverrunAmount`` is summed once per joined finance row
        there, and the per-bucket sums add up to the same total.
        """
        args = {
            f"year{i}_plannedBudget": Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=self.forced_to_frame)
                & Q(finances__year=self.year + i),
            )
            for i in YEARS
        }
        return list(
            Project.objects.filter(programmed=True, **filters)
            .values("projectClass_id", "projectLocation_id", "projectGroup_id")
            .annotate(**args, budgetOverrunAmount=Sum("budgetOverrunAmount", default=0))
            .order_by()
        )

    def _all_classes(self) -> dict:
        if self._classes is None:
            self._classes = {
                c["id"]: c
                for c in ProjectClass.objects.values(
                    "id", "name", "path", "parent_id", "relatedTo_id", "forCoordinatorOnly"
                )
            }
        return self._classes

    def _all_locations(self) -> dict:
        if self._locations is None:
            self._locations = {
                loc["id"]: loc
                for loc in ProjectLocation.objects.values(
                    "id", "parent_id", "parentClass_id", "relatedTo_id", "forCoordinatorOnly"
                )
            }
        return self._locations

    @staticmethod
    def _coordinator_of(rows: dict) -> dict:
        """planning id -> coordinator id (the reverse of ``relatedTo``)."""
        return {r["relatedTo_id"]: r["id"] for r in rows.values() if r["relatedTo_id"]}

    def _frame_budget_map(self):
        if self._frame_budgets is None:
            from infraohjelmointi_api.views.BaseClassLocationViewSet import (
                BaseClassLocationViewSet,
            )
            self._frame_budgets = BaseClassLocationViewSet.build_frame_budgets_context(
                self.year, for_frame_view=self.forced_to_frame
            )
        return self._frame_budgets

    # -------------------------------------------------------------- assembly

    def _sum_buckets(self, buckets) -> dict:
        totals = {f"year{i}_plannedBudget": 0 for i in YEARS}
        totals["budgetOverrunAmount"] = 0
        for bucket in buckets:
            for key in totals:
                totals[key] += bucket[key]
        return totals

    @staticmethod
    def _empty_frame_result() -> dict:
        return {
            f"year{y}": {"frameBudget": 0, "budgetChange": 0, "isFrameBudgetOverlap": False}
            for y in YEARS
        }

    def _assemble(self, sums: dict, frame_result: dict, extra: dict = None) -> dict:
        result = {
            **{f"year{i}_plannedBudget": sums[f"year{i}_plannedBudget"] for i in YEARS},
            "budgetOverrunAmount": sums["budgetOverrunAmount"],
            **(extra or {}),
            "year": self.year,
            **frame_result,
        }
        for i in YEARS:
            result[f"year{i}"]["plannedBudget"] = int(result.pop(f"year{i}_plannedBudget"))
        return result

    # ---------------------------------------------------------------- groups

    def _compute_groups(self, groups: list) -> dict:
        group_ids = [g.id for g in groups]
        buckets_by_group = defaultdict(list)
        for bucket in self._project_buckets(projectGroup__in=group_ids):
            buckets_by_group[bucket["projectGroup_id"]].append(bucket)

        project_budgets = dict(
            Project.objects.filter(programmed=True, projectGroup__in=group_ids)
            .values("projectGroup_id")
            .annotate(total=Sum("costForecast", default=0))
            .order_by()
            .values_list("projectGroup_id", "total")
        )

        return {
            g.id: self._assemble(
                self._sum_buckets(buckets_by_group[g.id]),
                self._empty_frame_result(),
                {"projectBudgets": project_budgets.get(g.id, 0)},
            )
            for g in groups
        }

    # --------------------------------------------------------------- classes

    def _class_targets(self, instances: list, coordinator_of: dict):
        """Function mapping a project class id to the listed instances it falls under.

        An instance matches a class that is the instance itself or whose path
        starts with ``instance.path + "/"`` (IO-928 boundary). Instead of testing
        every instance, a class looks up the instances sitting at each "/"
        boundary of its own path. Unknown ids (a class created after the class
        table was read) never match.
        """
        classes = self._all_classes()
        listed_ids = {i.id for i in instances}
        by_path = defaultdict(set)
        for instance in instances:
            by_path[instance.path].add(instance.id)

        def self_or_ancestors(class_id):
            targets = {class_id} & listed_ids
            row = classes.get(class_id)
            path = (row["path"] or "") if row else ""
            for i, char in enumerate(path):
                if char == "/":
                    targets |= by_path.get(path[:i], set())
            return targets

        if not self.for_coordinator:
            return self_or_ancestors

        def coordinator_targets(project_class_id):
            project_class = classes.get(project_class_id)
            if project_class is None:
                return set()
            coordinator = coordinator_of.get(project_class_id)
            targets = self_or_ancestors(coordinator) if coordinator else set()
            if "suurpiiri" in project_class["name"].lower():
                parent_coordinator = coordinator_of.get(project_class["parent_id"])
                if parent_coordinator:
                    targets |= self_or_ancestors(parent_coordinator)
            return targets
        return coordinator_targets

    def _compute_classes(self, instances: list) -> dict:
        classes = self._all_classes()
        locations = self._all_locations()
        coordinator_of = self._coordinator_of(classes)

        buckets_by_class = defaultdict(list)
        for bucket in self._project_buckets(projectClass__isnull=False):
            buckets_by_class[bucket["projectClass_id"]].append(bucket)

        # Whose frame data is shown: the coordinator twin in the planning view,
        # the class itself in the coordinator view.
        frame_source = {}
        for instance in instances:
            if self.for_coordinator and instance.forCoordinatorOnly:
                frame_source[instance.id] = instance.id
            else:
                frame_source[instance.id] = coordinator_of.get(instance.id)
        frame_rows = self._financial_rows(
            ClassFinancial, "classRelation_id", {s for s in frame_source.values() if s}
        )

        child_classes = defaultdict(list)
        for c in classes.values():
            if c["forCoordinatorOnly"] and c["parent_id"]:
                child_classes[c["parent_id"]].append(c["id"])
        child_locations = defaultdict(list)
        for loc in locations.values():
            if loc["forCoordinatorOnly"] and loc["parentClass_id"]:
                child_locations[loc["parentClass_id"]].append(loc["id"])

        # The per-instance path raises on a missing path; leave those to it.
        batchable = [i for i in instances if i.path is not None]
        targets_of = self._class_targets(batchable, coordinator_of)
        buckets_by_instance = defaultdict(list)
        for class_id, class_buckets in buckets_by_class.items():
            for instance_id in targets_of(class_id):
                buckets_by_instance[instance_id].extend(class_buckets)

        result = {}
        for instance in batchable:
            buckets = buckets_by_instance[instance.id]

            frame_result = self._empty_frame_result()
            source = frame_source[instance.id]
            if source is not None:
                self._apply_financial_rows(frame_rows.get(source, {}), frame_result)
                self._apply_overlaps(source, child_classes, child_locations, frame_result)
            result[instance.id] = self._assemble(self._sum_buckets(buckets), frame_result)
        return result

    def _apply_overlaps(self, class_id, child_classes, child_locations, frame_result):
        """Mirror of ``_get_child_relations`` + ``_calculate_budget_overlaps``."""
        direct_classes = child_classes.get(class_id, [])
        # Locations under the child classes only decide whether the check runs at all.
        has_any_child = bool(direct_classes) or any(
            child_locations.get(parent) for parent in [class_id, *direct_classes]
        )
        if not has_any_child:
            return

        frame_budgets = self._frame_budget_map()
        direct_children = [*direct_classes, *child_locations.get(class_id, [])]
        for y in YEARS:
            target_year = self.year + y
            children_budget_sum = sum(
                frame_budgets[f"{target_year}-{child_id}"] for child_id in direct_children
            )
            if children_budget_sum > frame_budgets[f"{target_year}-{class_id}"]:
                frame_result[f"year{y}"]["isFrameBudgetOverlap"] = True

    # ------------------------------------------------------------- locations

    def _compute_locations(self, instances: list) -> dict:
        locations = self._all_locations()
        coordinator_of = self._coordinator_of(locations)

        def chain(location_id):
            """The location and its two ancestors, as the ORM filter walks them."""
            ids = []
            for _ in range(3):
                if location_id is None:
                    break
                ids.append(location_id)
                location = locations.get(location_id)
                location_id = location["parent_id"] if location else None
            return ids

        if self.for_coordinator:
            def related(location_id):
                return {coordinator_of.get(i) for i in chain(location_id)} - {None}
        else:
            def related(location_id):
                return set(chain(location_id))

        group_location = dict(ProjectGroup.objects.values_list("id", "locationRelation_id"))

        # Only top-level locations carry project sums.
        top_level_ids = {i.id for i in instances if i.parent_id is None}
        buckets_by_instance = defaultdict(list)
        for bucket in self._project_buckets(projectLocation__isnull=False):
            targets = related(bucket["projectLocation_id"]) & top_level_ids
            group_id = bucket["projectGroup_id"]
            if group_id is not None:  # no group: the group filter always passes
                group_loc = group_location.get(group_id)
                targets &= related(group_loc) if group_loc else set()
            for instance_id in targets:
                buckets_by_instance[instance_id].append(bucket)

        frame_source = {}
        for instance in instances:
            if self.for_coordinator and instance.forCoordinatorOnly:
                frame_source[instance.id] = instance.id
            else:
                frame_source[instance.id] = coordinator_of.get(instance.id)
        frame_rows = self._financial_rows(
            LocationFinancial, "locationRelation_id", {s for s in frame_source.values() if s}
        )

        result = {}
        for instance in instances:
            frame_result = self._empty_frame_result()
            source = frame_source[instance.id]
            if source is not None:
                self._apply_financial_rows(frame_rows.get(source, {}), frame_result)
            result[instance.id] = self._assemble(
                self._sum_buckets(buckets_by_instance[instance.id]), frame_result
            )
        return result

    # --------------------------------------------------------------- shared

    def _financial_rows(self, model, relation_field: str, relation_ids: set) -> dict:
        """{relation id: {year: (frameBudget, budgetChange)}} for the 11-year window."""
        rows = defaultdict(dict)
        for row in model.objects.filter(
            **{f"{relation_field}__in": relation_ids},
            year__in=range(self.year, self.year + 11),
            forFrameView=self.forced_to_frame,
        ).values(relation_field, "year", "frameBudget", "budgetChange"):
            rows[row[relation_field]][row["year"]] = (row["frameBudget"], row["budgetChange"])
        return rows

    def _apply_financial_rows(self, rows_by_year: dict, frame_result: dict):
        for y in YEARS:
            row = rows_by_year.get(self.year + y)
            if row is not None:
                frame_result[f"year{y}"]["frameBudget"], frame_result[f"year{y}"]["budgetChange"] = row
