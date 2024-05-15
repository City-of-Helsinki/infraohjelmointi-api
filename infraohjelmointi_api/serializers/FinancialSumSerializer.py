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
from django.db.models import IntegerField
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
from django.db.models.functions import Coalesce


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def get_frameBudget_and_budgetChange(self, instance, year: int) -> dict:
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
        if instance.finances.filter(year=year).exists():
            if _type == "ProjectClass":
                finance_instance = ClassFinancialService.get(
                    class_id=instance.id, year=year
                )
            if _type == "ProjectLocation":
                finance_instance = LocationFinancialService.get(
                    location_id=instance.id, year=year
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
                .prefetch_related("finances")
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
            "isFrameBudgetOverlap": False
            if _type == "ProjectLocation"
            else is_frame_budget_overlap
            ,
        }

    def get_finance_sums(self, instance):
        """
        Calculates financial sums for 10 years given a group | location | class instance.
        """
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        forced_to_frame = self.context.get("forcedToFrame", False)

        related_projects = self.get_related_projects(instance=instance, _type=_type)

        summed_finances = related_projects.aggregate(
            year0_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year),
            ),
            year1_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 1),
            ),
            year2_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 2),
            ),
            year3_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 3),
            ),
            year4_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 4),
            ),
            year5_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 5),
            ),
            year6_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 6),
            ),
            year7_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 7),
            ),
            year8_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 8),
            ),
            year9_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 9),
            ),
            year10_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__forFrameView=forced_to_frame)
                & Q(finances__year=year + 10),
            ),
            budgetOverrunAmount=Sum("budgetOverrunAmount", default=0),
        )

        if _type == "ProjectGroup":
            summed_finances["projectBudgets"] = related_projects.aggregate(
                projectBudgets=Sum("costForecast", default=0)
            )["projectBudgets"]

        summed_finances["year"] = year
        summed_finances["year0"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year,
            ),
            "plannedBudget": int(summed_finances.pop("year0_plannedBudget")),
        }
        summed_finances["year1"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 1,
            ),
            "plannedBudget": int(summed_finances.pop("year1_plannedBudget")),
        }
        summed_finances["year2"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 2,
            ),
            "plannedBudget": int(summed_finances.pop("year2_plannedBudget")),
        }
        summed_finances["year3"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 3,
            ),
            "plannedBudget": int(summed_finances.pop("year3_plannedBudget")),
        }
        summed_finances["year4"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 4,
            ),
            "plannedBudget": int(summed_finances.pop("year4_plannedBudget")),
        }
        summed_finances["year5"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 5,
            ),
            "plannedBudget": int(summed_finances.pop("year5_plannedBudget")),
        }
        summed_finances["year6"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 6,
            ),
            "plannedBudget": int(summed_finances.pop("year6_plannedBudget")),
        }
        summed_finances["year7"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 7,
            ),
            "plannedBudget": int(summed_finances.pop("year7_plannedBudget")),
        }
        summed_finances["year8"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 8,
            ),
            "plannedBudget": int(summed_finances.pop("year8_plannedBudget")),
        }
        summed_finances["year9"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 9,
            ),
            "plannedBudget": int(summed_finances.pop("year9_plannedBudget")),
        }
        summed_finances["year10"] = {
            **self.get_frameBudget_and_budgetChange(
                instance=instance,
                year=year + 10,
            ),
            "plannedBudget": int(summed_finances.pop("year10_plannedBudget")),
        }

        return summed_finances

    def get_related_projects(self, instance, _type) -> list[Project]:
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
                        .prefetch_related("finances")
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
                    .prefetch_related("finances")
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
