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

    def get_frameBudget_and_budgetChange_new(self, instance, year: int, for_frame_view: bool, frame_budgets: defaultdict) -> dict:
        """
        Returns the frameBudget, budgetChange and isFrameBudgetOverlap for a given year and class/location instance.\n
        isFrameBudgetOverlap donates if child classes have a frameBudget sum that exceeds the current class frameBudget.
        """

        for_coordinator = self.context.get("for_coordinator", False)
        _type = instance._meta.model.__name__

        if (
            for_coordinator == False
            or getattr(instance, "forCoordinatorOnly", False) == False
        ):
            # get coordinatorClass when planning classes/locations are being fetched
            if _type == "ProjectClass":
                instance = getattr(instance, "coordinatorClass", None)
            if _type == "ProjectLocation":
                instance = getattr(instance, "coordinatorLocation", None)

        ret_val = {
            f"year{y}": {
                "frameBudget": 0, "budgetChange": 0, "isFrameBudgetOverlap": False
            }
            for y in range(11)
        }

        if _type not in ["ProjectClass", "ProjectLocation"] or instance == None:
            return ret_val
        
        for y in range(11):
            finance_instance = None
            if instance.finances.filter(year=year+y, forFrameView=for_frame_view).exists():
                if _type == "ProjectClass":
                    finance_instance = ClassFinancialService.get(
                        class_id=instance.id, year=year+y, for_frame_view=for_frame_view
                    )
                if _type == "ProjectLocation":
                    finance_instance = LocationFinancialService.get(
                        location_id=instance.id, year=year+y, for_frame_view=for_frame_view
                    )
            if finance_instance != None:
                ret_val[f"year{y}"]["frameBudget"] = finance_instance.frameBudget
                ret_val[f"year{y}"]["budgetChange"] = finance_instance.budgetChange
        
        # Get framebudget sums for children only for ProjectClass instances since coordinator locations have no more levels under it
        if _type != "ProjectClass":
            return ret_val

        # get all childs with frameBudget for each level
        child_classes = (
            ProjectClass.objects.filter(
                path__startswith=instance.path,
                path__gt=instance.path,
                forCoordinatorOnly=True,
            )
            .annotate(parentRelation=F("parent"))
            .values("id", "parentRelation")
        )
        # get all locations with parentClass as childs and get frameBudgets
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

        # Combine all child relations of the current instance into one single queryset
        all_child_relations = child_locations.union(child_classes)
        if all_child_relations.exists():
            for y in range(11):    
                grouped = defaultdict(lambda: {'frameBudget': 0})
                for relation in all_child_relations:
                    grouped[relation['parentRelation']]['frameBudget'] += frame_budgets[f"{year+y}-{relation['id']}"] 
                    if grouped[relation['parentRelation']]['frameBudget'] > frame_budgets[f"{year+y}-{relation['parentRelation']}"]:
                        ret_val[f"year{y}"]["isFrameBudgetOverlap"] = True
                        break
        return ret_val

    def get_frameBudget_and_budgetChange(self, instance, year: int, for_frame_view: bool) -> dict:
        """
        Returns the frameBudget, budgetChange and isFrameBudgetOverlap for a given year and class/location instance.\n
        isFrameBudgetOverlap donates if child classes have a frameBudget sum that exceeds the current class frameBudget.
        """

        for_coordinator = self.context.get("for_coordinator", False)
        _type = instance._meta.model.__name__

        if (
            for_coordinator == False
            or getattr(instance, "forCoordinatorOnly", False) == False
        ):
            # get coordinatorClass when planning classes/locations are being fetched
            if _type == "ProjectClass":
                instance = getattr(instance, "coordinatorClass", None)
            if _type == "ProjectLocation":
                instance = getattr(instance, "coordinatorLocation", None)

        if _type not in ["ProjectClass", "ProjectLocation"] or instance == None:
            return {"frameBudget": 0, "budgetChange": 0, "isFrameBudgetOverlap": False}

        finance_instance = None
        if instance.finances.filter(year=year, forFrameView=for_frame_view).exists():
            if _type == "ProjectClass":
                finance_instance = ClassFinancialService.get(
                    class_id=instance.id, year=year, for_frame_view=for_frame_view
                )
            if _type == "ProjectLocation":
                finance_instance = LocationFinancialService.get(
                    location_id=instance.id, year=year, for_frame_view=for_frame_view
                )

        is_frame_budget_overlap = False
        # Get framebudget sums for children only for ProjectClass instances since coordinator locations have no more levels under it
        if _type == "ProjectClass":
            # get all childs with frameBudget for each level

            child_classes = (
                ProjectClass.objects.filter(
                    path__startswith=instance.path,
                    path__gt=instance.path,
                    forCoordinatorOnly=True,
                )
                .annotate(
                    frameBudget=Coalesce(
                        Subquery(
                            ClassFinancial.objects.filter(
                                classRelation=OuterRef("id"), year=year
                            ).values_list("frameBudget", flat=True)[:1],
                            output_field=IntegerField(),
                        ),
                        Value(0),
                    ),
                    parentRelation=F("parent"),
                    parentFrameBudget=Coalesce(
                        Subquery(
                            ClassFinancial.objects.filter(
                                classRelation=OuterRef("parent"), year=year
                            ).values_list("frameBudget", flat=True)[:1],
                            output_field=IntegerField(),
                        ),
                        Value(0),
                    ),
                )
                .values("id", "parentRelation", "frameBudget", "parentFrameBudget")
            )
            # get all locations with parentClass as childs and get frameBudgets
            child_locations = (
                ProjectLocation.objects.filter(
                    parentClass__in=[
                        *child_classes.values_list("id", flat=True),
                        instance.id,
                    ],
                    forCoordinatorOnly=True,
                )
                .annotate(
                    frameBudget=Coalesce(
                        Subquery(
                            LocationFinancial.objects.filter(
                                locationRelation=OuterRef("id"), year=year
                            ).values_list("frameBudget", flat=True)[:1],
                            output_field=IntegerField(),
                        ),
                        Value(0),
                    ),
                    parentRelation=F("parentClass"),
                    parentFrameBudget=Coalesce(
                        Subquery(
                            ClassFinancial.objects.filter(
                                classRelation=OuterRef("parentClass"), year=year
                            ).values_list("frameBudget", flat=True)[:1],
                            output_field=IntegerField(),
                        ),
                        Value(0),
                    ),
                )
                .values("id", "parentRelation", "frameBudget", "parentFrameBudget")
            )
            # Combine all child relations of the current instance into one single queryset
            all_child_relations = child_locations.union(child_classes)
            if all_child_relations.exists():
                grouped = defaultdict(lambda: {'frameBudget': 0})

                for relation in all_child_relations:
                    grouped[relation['parentRelation']]['frameBudget'] += relation['frameBudget']
                    if grouped[relation['parentRelation']]['frameBudget'] > relation['parentFrameBudget']:
                        is_frame_budget_overlap = True
                        break

        return {
            "frameBudget": finance_instance.frameBudget
            if finance_instance != None
            else 0,
            "budgetChange": finance_instance.budgetChange
            if finance_instance != None
            else 0,
            "isFrameBudgetOverlap": is_frame_budget_overlap,
        }

    def get_finance_sums(self, instance):
        """
        Calculates financial sums for 10 years given a group | location | class instance.
        """
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        forced_to_frame = self.context.get("forcedToFrame", False)

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
      
        frame_budgets = self.context.get("frame_budgets", None)
        if frame_budgets == None:
            for i in range(11):
                summed_finances[f"year{i}"] = {
                    **self.get_frameBudget_and_budgetChange(
                        instance=instance,
                        year=year + i,
                        for_frame_view=forced_to_frame
                    ),
                    "plannedBudget": int(summed_finances.pop(f"year{i}_plannedBudget")),
                }
        else:
            summed_finances = {
                **summed_finances,
                **self.get_frameBudget_and_budgetChange_new(
                    instance=instance,
                    year=year,
                    for_frame_view=forced_to_frame,
                    frame_budgets=frame_budgets
                ),
            }
            for i in range(11):
                summed_finances[f"year{i}"]["plannedBudget"] = int(summed_finances.pop(f"year{i}_plannedBudget"))

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
                    return (
                        Project.objects.select_related(
                            "projectLocation",
                            "projectLocation__coordinatorLocation",
                            "projectLocation__parent__coordinatorLocation",
                            "projectLocation__parent__parent__coordinatorLocation",
                        )
                        .prefetch_related("finances")
                        .filter(
                            Q(projectLocation__coordinatorLocation=instance)
                            | Q(projectLocation__parent__coordinatorLocation=instance)
                            | Q(
                                projectLocation__parent__parent__coordinatorLocation=instance
                            ),
                            programmed=True,
                        )
                    )
                else:
                    return (
                        Project.objects.select_related(
                            "projectLocation",
                            "projectLocation__parent",
                            "projectLocation__parent__parent",
                        )
                        .filter(
                            Q(projectLocation=instance)
                            | Q(projectLocation__parent=instance)
                            | Q(projectLocation__parent__parent=instance),
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
