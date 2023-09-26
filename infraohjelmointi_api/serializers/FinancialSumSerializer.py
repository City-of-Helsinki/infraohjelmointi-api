from datetime import date
from infraohjelmointi_api.models import (
    Project,
    ClassFinancial,
    ProjectClass,
    LocationFinancial,
    ProjectLocation,
)
import pandas as pd
from django.core.cache import cache
from infraohjelmointi_api.services import (
    ProjectService,
    ClassFinancialService,
    LocationFinancialService,
)
from django.db.models import IntegerField
from rest_framework import serializers
from django.db.models import (
    Sum,
    F,
    Case,
    When,
    Value,
    BooleanField,
    Q,
    Count,
    PositiveIntegerField,
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

        financeInstance = None
        if instance.finances.filter(year=year).exists():
            if _type == "ProjectClass":
                financeInstance = ClassFinancialService.get(
                    class_id=instance.id, year=year
                )
            if _type == "ProjectLocation":
                financeInstance = LocationFinancialService.get(
                    location_id=instance.id, year=year
                )

        childClassQueryResult = {"subChildrenOverlapCount": 0, "childSums": 0}
        # Get framebudget sums for children only for ProjectClass instances since coordinator locations have no more levels under it
        if _type == "ProjectClass":
            # get all childs with frameBudget for each level

            childClasses = (
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
            childLocations = (
                ProjectLocation.objects.filter(
                    parentClass__in=[
                        *childClasses.values_list("id", flat=True),
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
            allChildRelations = childLocations.union(childClasses)
            if allChildRelations.count() > 0:
                dataFrame = pd.DataFrame.from_records(allChildRelations)

                # Group by 'parentRelation' and calculate the sum of 'frameBudget' for each group
                # This gives us frameBudget sums of each level under the current instance
                grouped = (
                    dataFrame.groupby("parentRelation")
                    .agg({"parentFrameBudget": "first", "frameBudget": "sum"})
                    .reset_index()
                )
                # Calculate for each level if child sums exceed frameBudget of that level
                grouped["isOverlap"] = (
                    grouped["frameBudget"] > grouped["parentFrameBudget"]
                )

                # Rename the 'frameBudget' column to 'frameBudgetSums'
                grouped.rename(columns={"frameBudget": "frameBudgetSums"}, inplace=True)
                # Total frameBudget sum of all levels under current instance
                child_sums = grouped["frameBudgetSums"].sum()
                # Check how many levels under current instance have frameBudget warnings
                sub_children_overlap_count = grouped["isOverlap"].sum()

                # Create a new DataFrame with the results
                result_df = pd.DataFrame(
                    {
                        "childSums": [child_sums],
                        "subChildrenOverlapCount": [sub_children_overlap_count],
                    }
                )
                childClassQueryResult = result_df.to_dict(orient="records")[0]

        return {
            "frameBudget": financeInstance.frameBudget
            if financeInstance != None
            else 0,
            "budgetChange": financeInstance.budgetChange
            if financeInstance != None
            else 0,
            # check if overlapCount > 0, means there is some level under this class which has frameBudget exceeding its parent
            # or the frameBudget sums for all child levels exceeds the frameBudget of this level
            "isFrameBudgetOverlap": False
            if _type == "ProjectLocation"
            else childClassQueryResult["subChildrenOverlapCount"] > 0
            or (
                financeInstance != None
                and (childClassQueryResult["childSums"] > financeInstance.frameBudget)
            ),
        }

    # try caching this whole result for a class
    # can change based on frameview, and year
    def get_finance_sums(self, instance):
        """
        Calculates financial sums for 10 years given a group | location | class instance.
        """
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        forcedToFrame = self.context.get("forcedToFrame", False)

        # Check if current instance has changed since the last time by searching for its id in the cache
        relationEffectedCached: list = cache.get("relationEffected", None)
        if (
            isinstance(relationEffectedCached, list)
            and (instance in relationEffectedCached)
            or (
                cache.get(str(instance.id) + "/{}/{}".format(forcedToFrame, year))
                == None
            )
        ):
            # this instance needs new financial sums to be calculated
            relatedProjects = self.get_related_projects(instance=instance, _type=_type)

            summedFinances = relatedProjects.aggregate(
                year0_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year),
                ),
                year1_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 1),
                ),
                year2_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 2),
                ),
                year3_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 3),
                ),
                year4_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 4),
                ),
                year5_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 5),
                ),
                year6_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 6),
                ),
                year7_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 7),
                ),
                year8_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 8),
                ),
                year9_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 9),
                ),
                year10_plannedBudget=Sum(
                    "finances__value",
                    default=0,
                    filter=Q(finances__forFrameView=forcedToFrame)
                    & Q(finances__year=year + 10),
                ),
                budgetOverrunAmount=Sum("budgetOverrunAmount", default=0),
            )
            if _type == "ProjectGroup":
                summedFinances["projectBudgets"] = relatedProjects.aggregate(
                    projectBudgets=Sum("costForecast", default=0)
                )["projectBudgets"]

            summedFinances["year"] = year
            summedFinances["year0"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year,
                ),
                "plannedBudget": int(summedFinances.pop("year0_plannedBudget")),
            }
            summedFinances["year1"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 1,
                ),
                "plannedBudget": int(summedFinances.pop("year1_plannedBudget")),
            }
            summedFinances["year2"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 2,
                ),
                "plannedBudget": int(summedFinances.pop("year2_plannedBudget")),
            }
            summedFinances["year3"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 3,
                ),
                "plannedBudget": int(summedFinances.pop("year3_plannedBudget")),
            }
            summedFinances["year4"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 4,
                ),
                "plannedBudget": int(summedFinances.pop("year4_plannedBudget")),
            }
            summedFinances["year5"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 5,
                ),
                "plannedBudget": int(summedFinances.pop("year5_plannedBudget")),
            }
            summedFinances["year6"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 6,
                ),
                "plannedBudget": int(summedFinances.pop("year6_plannedBudget")),
            }
            summedFinances["year7"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 7,
                ),
                "plannedBudget": int(summedFinances.pop("year7_plannedBudget")),
            }
            summedFinances["year8"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 8,
                ),
                "plannedBudget": int(summedFinances.pop("year8_plannedBudget")),
            }
            summedFinances["year9"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 9,
                ),
                "plannedBudget": int(summedFinances.pop("year9_plannedBudget")),
            }
            summedFinances["year10"] = {
                **self.get_frameBudget_and_budgetChange(
                    instance=instance,
                    year=year + 10,
                ),
                "plannedBudget": int(summedFinances.pop("year10_plannedBudget")),
            }
            # caching calculations for 24 hours
            # will get updated according to relations which change
            cache.set(
                str(instance.id) + "/{}/{}".format(forcedToFrame, year),
                summedFinances,
                60 * 60 * 24,
            )

            # delete this instance from relationEffected if it exists there since it has been updated now
            if (
                isinstance(relationEffectedCached, list)
                and instance in relationEffectedCached
            ):
                relationEffectedCached.remove(instance)
            cache.set("relationEffected", relationEffectedCached)

        else:
            # instance doesn't exist in changed relations cache
            # get calculations from cache
            summedFinances = cache.get(
                str(instance.id) + "/{}/{}".format(forcedToFrame, year)
            )

        return summedFinances

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
                        projectClass__path__startswith=instance.path, programmed=True
                    )
                )

        if _type == "ProjectGroup":
            return (
                ProjectService.find_by_group_id(group_id=instance.id)
                .filter(programmed=True)
                .prefetch_related("finances")
            )

        return Project.objects.none()
