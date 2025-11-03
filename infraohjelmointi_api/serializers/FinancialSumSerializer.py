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
    IntegerField,
    Sum,
    F,
    Value,
    Q,
    OuterRef,
    Subquery,
)
from django.db.models.manager import BaseManager
from django.db.models.functions import Coalesce


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def _get_coordinator_instance(self, instance, _type: str):
        """Get the coordinator instance if needed."""
        for_coordinator = self.context.get("for_coordinator", False)
        
        if not for_coordinator or not getattr(instance, "forCoordinatorOnly", False):
            if _type == "ProjectClass":
                return getattr(instance, "coordinatorClass", None)
            elif _type == "ProjectLocation":
                return getattr(instance, "coordinatorLocation", None)
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
        # Use prefetched finances data to avoid N+1 queries
        # The finances are already prefetched in the ViewSet queryset
        finances_list = list(instance.finances.all()) if hasattr(instance, 'finances') else []
        
        # Create a lookup dict for O(1) access
        finances_by_year = {
            f.year: f for f in finances_list 
            if f.forFrameView == for_frame_view
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
        child_classes = (
            ProjectClass.objects.filter(
                path__startswith=instance.path,
                path__gt=instance.path,
                forCoordinatorOnly=True,
            )
            .annotate(parentRelation=F("parent"))
            .values("id", "parentRelation")
        )
        
        child_locations = (
            ProjectLocation.objects.filter(
                parentClass__in=[
                    *child_classes.values_list("id", flat=True),
                    instance.id,
                ],
                forCoordinatorOnly=True,
            )
            .annotate(parentRelation=F("parentClass"))
            .values("id", "parentRelation")
        )

        return child_locations.union(child_classes)

    def _calculate_budget_overlaps(self, instance, year: int, frame_budgets: defaultdict, 
                                   all_child_relations, ret_val: dict):
        """Calculate budget overlaps for all years."""
        for y in range(11):    
            children_budget_sum = sum(
                frame_budgets[f"{year+y}-{relation['id']}"]
                for relation in all_child_relations
                if relation['parentRelation'] == instance.id
            )
            
            current_budget = frame_budgets[f"{year+y}-{instance.id}"]
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
            if all_child_relations.exists():
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
        
        # Try to get from cache first
        cached_result = CacheService.get_financial_sum(
            instance_id=instance.id,
            instance_type=_type,
            year=year,
            for_frame_view=forced_to_frame,
            for_coordinator=for_coordinator
        )
        
        if cached_result is not None:
            return cached_result

        # Try to use prefetched project_set if available (from ViewSet)
        # This avoids N+1 queries for ProjectClass, ProjectLocation, and ProjectGroup
        if hasattr(instance, '_prefetched_objects_cache') and 'project_set' in instance._prefetched_objects_cache:
            # Use prefetched data - much faster!
            related_projects = instance.project_set.all()
        else:
            # Fall back to querying (when not prefetched)
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
      
        # Use unified method with frame_budgets context
        frame_budgets = self.context.get("frame_budgets")
        if frame_budgets is None:
            # Build frame_budgets if not provided (e.g., in signal handlers or tests)
            # Use lazy import to avoid circular dependency
            from infraohjelmointi_api.views.BaseClassLocationViewSet import BaseClassLocationViewSet
            frame_budgets = BaseClassLocationViewSet.build_frame_budgets_context(year, for_frame_view=forced_to_frame)
        
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

        # Cache the result
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
                        "projectClass__parent__coordinatorClass",
                    )
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
