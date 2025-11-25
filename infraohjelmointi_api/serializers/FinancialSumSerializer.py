from collections import defaultdict
from datetime import date
from infraohjelmointi_api.models import (
    Project,
    ClassFinancial,
    ProjectClass,
    LocationFinancial,
    ProjectLocation,
)
from infraohjelmointi_api.services import (
    ProjectService,
    ClassFinancialService,
    LocationFinancialService,
)
from infraohjelmointi_api.services.CacheService import CacheService
from rest_framework import serializers
from django.db.models import (
    Sum,
    Q,
)
from django.db.models.manager import BaseManager


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def _get_coordinator_instance(self, instance, _type: str):
        """Get the coordinator instance if needed."""
        for_coordinator = self.context.get("for_coordinator", False)

        if not for_coordinator or not getattr(instance, "forCoordinatorOnly", False):
            if _type == "ProjectClass":
                coordinator_id = getattr(instance, "coordinatorClass_id", None)
                if coordinator_id:
                    # Get fresh instance from database to ensure all relationships are available
                    # This is critical for overlap detection - we need a fresh query
                    coordinator = ProjectClass.objects.get(id=coordinator_id)
                    # Clear prefetch cache to force fresh query for finances after updates
                    if hasattr(coordinator, '_prefetched_objects_cache'):
                        coordinator._prefetched_objects_cache.pop('finances', None)
                    return coordinator
                # Fallback to relationship access if ID not available
                coordinator = getattr(instance, "coordinatorClass", None)
                if coordinator:
                    coordinator.refresh_from_db()
                    if hasattr(coordinator, '_prefetched_objects_cache'):
                        coordinator._prefetched_objects_cache.pop('finances', None)
                return coordinator
            elif _type == "ProjectLocation":
                coordinator_id = getattr(instance, "coordinatorLocation_id", None)
                if coordinator_id:
                    # Get fresh instance from database
                    coordinator = ProjectLocation.objects.get(id=coordinator_id)
                    if hasattr(coordinator, '_prefetched_objects_cache'):
                        coordinator._prefetched_objects_cache.pop('finances', None)
                    return coordinator
                # Fallback to relationship access
                coordinator = getattr(instance, "coordinatorLocation", None)
                if coordinator:
                    coordinator.refresh_from_db()
                    if hasattr(coordinator, '_prefetched_objects_cache'):
                        coordinator._prefetched_objects_cache.pop('finances', None)
                return coordinator
        return instance

    def _create_empty_budget_result(self) -> dict:
        """Create empty budget result structure for 11 years."""
        return {
            f"year{y}": {
                "frameBudget": 0, "budgetChange": 0, "isFrameBudgetOverlap": False
            }
            for y in range(11)
        }

    def _populate_financial_data(self, instance, _type: str, year: int, for_frame_view: bool, ret_val: dict):
        """Populate frameBudget and budgetChange data for all years using prefetched data."""
        # Clear prefetch cache to ensure we get fresh data (important after PATCH operations)
        if hasattr(instance, '_prefetched_objects_cache') and 'finances' in instance._prefetched_objects_cache:
            del instance._prefetched_objects_cache['finances']

        # Force a fresh query to get the latest finances (avoids stale prefetched data)
        # This is critical after PATCH operations that update finances
        if _type == "ProjectClass":
            finances_list = list(
                ClassFinancial.objects.filter(
                    classRelation=instance,
                    year__in=range(year, year + 11),
                    forFrameView=for_frame_view
                )
            )
        elif _type == "ProjectLocation":
            finances_list = list(
                LocationFinancial.objects.filter(
                    locationRelation=instance,
                    year__in=range(year, year + 11),
                    forFrameView=for_frame_view
                )
            )
        else:
            # Fallback to prefetched data for other types
            finances_list = list(instance.finances.all()) if hasattr(instance, 'finances') else []

        # Create a lookup dict for O(1) access
        finances_by_year = {
            f.year: f for f in finances_list
        }

        for y in range(11):
            target_year = year + y
            finance_instance = finances_by_year.get(target_year)

            if finance_instance is not None:
                ret_val[f"year{y}"]["frameBudget"] = finance_instance.frameBudget
                ret_val[f"year{y}"]["budgetChange"] = finance_instance.budgetChange

    def _get_finance_instance(self, _type: str, instance_id, year: int, for_frame_view: bool):
        """Get finance instance based on type."""
        try:
            if _type == "ProjectClass":
                return ClassFinancialService.get(
                    class_id=instance_id, year=year, for_frame_view=for_frame_view
                )
            elif _type == "ProjectLocation":
                return LocationFinancialService.get(
                    location_id=instance_id, year=year, for_frame_view=for_frame_view
                )
        except Exception:
            # If service call fails, return None (no financial data exists)
            return None
        return None

    def _get_child_relations(self, instance):
        """Get all child class and location relations."""
        # Get direct children only (where parent == instance)
        child_classes = (
            ProjectClass.objects.filter(
                parent=instance,
                forCoordinatorOnly=True,
            )
            .values("id")
        )

        # Also get child locations that belong to this class or its child classes
        child_class_ids = list(child_classes.values_list("id", flat=True))
        child_locations = (
            ProjectLocation.objects.filter(
                parentClass__in=[instance.id, *child_class_ids],
                forCoordinatorOnly=True,
            )
            .values("id", "parentClass")
        )

        # Build result list with proper parentRelation annotation
        result = []
        for child_class in child_classes:
            result.append({
                'id': child_class['id'],
                'parentRelation': instance.id
            })
        for child_location in child_locations:
            result.append({
                'id': child_location['id'],
                'parentRelation': child_location['parentClass']
            })

        return result

    def _calculate_budget_overlaps(self, instance, year: int, frame_budgets: defaultdict,
                                   all_child_relations, ret_val: dict):
        """Calculate budget overlaps for all years."""
        # Convert instance.id to string for consistent key matching
        instance_id_str = str(instance.id)

        for y in range(11):
            target_year = year + y
            children_budget_sum = 0

            # Iterate through child relations and sum budgets of direct children
            for relation in all_child_relations:
                parent_relation = relation.get('parentRelation')
                # Compare UUIDs - convert both to strings for consistent comparison
                # Handle both UUID objects and None values
                if parent_relation is not None:
                    parent_relation_str = str(parent_relation)
                    if parent_relation_str == instance_id_str:
                        child_id_str = str(relation['id'])
                        key = f"{target_year}-{child_id_str}"
                        child_budget = frame_budgets[key]
                        children_budget_sum += child_budget

            # Get current budget for this instance
            current_budget_key = f"{target_year}-{instance_id_str}"
            current_budget = frame_budgets[current_budget_key]

            # Set overlap flag if children exceed parent budget
            # Note: We check children_budget_sum > 0 to ensure we have children, and
            # children_budget_sum > current_budget to detect overlap
            if children_budget_sum > current_budget:
                ret_val[f"year{y}"]["isFrameBudgetOverlap"] = True

    def get_frameBudget_and_budgetChange(self, instance, year: int, for_frame_view: bool, frame_budgets: defaultdict) -> dict:
        """
        Returns the frameBudget, budgetChange and isFrameBudgetOverlap for a given year and class/location instance.
        isFrameBudgetOverlap indicates if child classes have a frameBudget sum that exceeds the current class frameBudget.
        """
        _type = instance._meta.model.__name__
        instance = self._get_coordinator_instance(instance, _type)
        ret_val = self._create_empty_budget_result()

        if _type not in ["ProjectClass", "ProjectLocation"] or instance is None:
            return ret_val

        self._populate_financial_data(instance, _type, year, for_frame_view, ret_val)

        # Only ProjectClass instances can have budget overlaps (coordinator locations have no children)
        if _type == "ProjectClass":
            all_child_relations = self._get_child_relations(instance)
            # _get_child_relations now returns a list, so no need to convert
            if all_child_relations:
                self._calculate_budget_overlaps(instance, year, frame_budgets, all_child_relations, ret_val)

        return ret_val

    def get_finance_sums(self, instance):
        """
        Calculates financial sums for 10 years given a group | location | class instance.
        Uses caching for performance optimization.
        """
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        forced_to_frame = self.context.get("forcedToFrame", False)
        for_coordinator = self.context.get("for_coordinator", False)

        frame_budgets = self.context.get("frame_budgets")
        if frame_budgets is None:
            from infraohjelmointi_api.views.BaseClassLocationViewSet import (
                BaseClassLocationViewSet,
            )
            frame_budgets = BaseClassLocationViewSet.build_frame_budgets_context(
                year, for_frame_view=forced_to_frame
            )

        # Coordinator classes/locations should always be cached (best performance benefit)
        # Planning classes should not be cached (depend on coordinator finances for overlap)
        use_cache = True
        if _type == "ProjectClass":
            # Coordinator classes: always cache
            if getattr(instance, "forCoordinatorOnly", False):
                use_cache = True
            # Planning classes: don't cache (have coordinatorClass attribute)
            elif getattr(instance, "coordinatorClass", None):
                use_cache = False
        elif _type == "ProjectLocation":
            # Coordinator locations: always cache
            if getattr(instance, "forCoordinatorOnly", False):
                use_cache = True
            # Planning locations: don't cache (have coordinatorLocation attribute)
            elif getattr(instance, "coordinatorLocation", None):
                use_cache = False

        cached_result = None
        if use_cache:
            cached_result = CacheService.get_financial_sum(
                instance_id=instance.id,
                instance_type=_type,
                year=year,
                for_frame_view=forced_to_frame,
                for_coordinator=for_coordinator
            )

        if cached_result is not None:
            return cached_result

        related_projects = self.get_related_projects(instance=instance, _type=_type)

        args = {
            f"year{i}_plannedBudget": Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year+i),
            )
            for i in range(11)
        }

        summed_finances = related_projects.aggregate(
            **args,
            budgetOverrunAmount=Sum("budgetOverrunAmount", default=0),
        )

        if _type == "ProjectGroup":
            summed_finances["projectBudgets"] = related_projects.aggregate(
                projectBudgets=Sum("costForecast", default=0)
            )["projectBudgets"]

        summed_finances["year"] = year
        summed_finances = {
            **summed_finances,
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year,
                for_frame_view=forced_to_frame,
                frame_budgets=frame_budgets
            ),
        }
        for i in range(11):
            summed_finances[f"year{i}"]["plannedBudget"] = int(summed_finances.pop(f"year{i}_plannedBudget"))

        if use_cache:
            CacheService.set_financial_sum(
                instance_id=instance.id,
                instance_type=_type,
                year=year,
                for_frame_view=forced_to_frame,
                data=summed_finances,
                for_coordinator=for_coordinator
            )

        return summed_finances

    def get_related_projects(self, instance, _type) -> BaseManager[Project]:
        """
        Returns projects under the provided class | location | group instance.
        """
        # use context to check if coordinator class/locations are needed
        for_coordinator = self.context.get("for_coordinator", False)
        if _type == "ProjectLocation":
            if instance.parent is None:
                if for_coordinator == True:
                    # Base filter: projects that belong to this coordinatorLocation or its children
                    coordinator_base_filter = Q(
                        Q(projectLocation__coordinatorLocation=instance)
                        | Q(projectLocation__parent__coordinatorLocation=instance)
                        | Q(projectLocation__parent__parent__coordinatorLocation=instance)
                    )

                    # Group filter for coordinator: either no group OR group belongs to this location hierarchy
                    coordinator_group_filter = Q(projectGroup__isnull=True) | Q(
                        Q(projectGroup__locationRelation__coordinatorLocation=instance)
                        | Q(projectGroup__locationRelation__parent__coordinatorLocation=instance)
                        | Q(projectGroup__locationRelation__parent__parent__coordinatorLocation=instance)
                    )

                    return (
                        Project.objects.select_related(
                            "projectLocation",
                            "projectLocation__coordinatorLocation",
                            "projectLocation__parent__coordinatorLocation",
                            "projectLocation__parent__parent__coordinatorLocation",
                            "projectGroup",
                            "projectGroup__locationRelation__coordinatorLocation",
                            "projectGroup__locationRelation__parent__coordinatorLocation",
                            "projectGroup__locationRelation__parent__parent__coordinatorLocation",
                        )
                        .prefetch_related("finances")
                        .filter(
                            coordinator_base_filter & coordinator_group_filter,
                            programmed=True,
                        )
                    )
                else:
                    # Base filter: projects that belong to this location or its children
                    base_filter = Q(
                        Q(projectLocation=instance)
                        | Q(projectLocation__parent=instance)
                        | Q(projectLocation__parent__parent=instance)
                    )

                    # Group filter: either no group OR group belongs to this location hierarchy
                    group_filter = Q(projectGroup__isnull=True) | Q(
                        Q(projectGroup__locationRelation=instance)
                        | Q(projectGroup__locationRelation__parent=instance)
                        | Q(projectGroup__locationRelation__parent__parent=instance)
                    )

                    return (
                        Project.objects.select_related(
                            "projectLocation",
                            "projectLocation__parent",
                            "projectLocation__parent__parent",
                            "projectGroup",
                            "projectGroup__locationRelation",
                            "projectGroup__locationRelation__parent",
                            "projectGroup__locationRelation__parent__parent",
                        )
                        .prefetch_related("finances")
                        .filter(
                            base_filter & group_filter,
                            programmed=True,
                        )
                    )
            return Project.objects.none()
        if _type == "ProjectClass":
            if for_coordinator == True:
                return (
                    Project.objects.select_related(
                        "projectClass",
                        "projectClass__coordinatorClass",
                        "projectClass__parent",
                        "projectClass__parent__coordinatorClass",
                    )
                    .prefetch_related("finances")  # CRITICAL: Prevents N+1 queries when aggregating ProjectFinancial
                    .filter(
                        (
                            Q(projectClass__name__icontains="suurpiiri")
                            & Q(
                                projectClass__parent__coordinatorClass__path__startswith=instance.path
                            )
                        )
                        | Q(
                            projectClass__coordinatorClass__path__startswith=instance.path
                        ),
                        programmed=True,
                    )
                )
            else:
                return (
                    Project.objects.select_related("projectClass")
                    .prefetch_related("finances")
                    .filter(
                        Q(projectClass=instance)
                        | Q(projectClass__parent=instance)
                        | Q(projectClass__parent__parent=instance),
                        programmed=True,
                    )
                )

        if _type == "ProjectGroup":
            return (
                ProjectService.find_by_group_id(group_id=instance.id)
                .filter(programmed=True)
                .prefetch_related("finances")
            )

        return Project.objects.none()
