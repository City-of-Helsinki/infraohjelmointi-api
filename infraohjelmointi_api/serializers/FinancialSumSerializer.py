from datetime import date
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.services import ProjectService
from rest_framework import serializers
from django.db.models import Sum, Q


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def get_finance_sums(self, instance):
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        relatedProjects = self.get_related_projects(instance=instance, _type=_type)
        summedFinances = relatedProjects.aggregate(
            year0_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year),
            ),
            year1_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 1),
            ),
            year2_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 2),
            ),
            year3_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 3),
            ),
            year4_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 4),
            ),
            year5_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 5),
            ),
            year6_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 6),
            ),
            year7_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 7),
            ),
            year8_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 8),
            ),
            year9_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 9),
            ),
            year10_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 10),
            ),
            budgetOverrunAmount=Sum("budgetOverrunAmount", default=0),
        )
        if _type == "ProjectGroup":
            summedFinances["projectBudgets"] = relatedProjects.aggregate(
                projectBudgets=Sum("costForecast", default=0)
            )["projectBudgets"]
        summedFinances["year"] = year
        summedFinances["year0"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year0_plannedBudget")),
        }
        summedFinances["year1"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year1_plannedBudget")),
        }
        summedFinances["year2"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year2_plannedBudget")),
        }
        summedFinances["year3"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year3_plannedBudget")),
        }
        summedFinances["year4"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year4_plannedBudget")),
        }
        summedFinances["year5"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year5_plannedBudget")),
        }
        summedFinances["year6"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year6_plannedBudget")),
        }
        summedFinances["year7"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year7_plannedBudget")),
        }
        summedFinances["year8"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year8_plannedBudget")),
        }
        summedFinances["year9"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year9_plannedBudget")),
        }
        summedFinances["year10"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year10_plannedBudget")),
        }

        return summedFinances

    def get_related_projects(self, instance, _type) -> list[Project]:
        # use context to check if coordinator class/locations are needed
        for_coordinator = self.context.get("for_coordinator", False)
        if _type == "ProjectLocation":
            if instance.parent is None:
                if for_coordinator == True:
                    return (
                        Project.objects.select_related("projectLocation")
                        .prefetch_related(
                            "finances",
                            "projectLocation__coordinatorLocation",
                        )
                        .filter(projectLocation__coordinatorLocation=instance)
                    )
                else:
                    return (
                        Project.objects.select_related("projectLocation")
                        .prefetch_related(
                            "finances",
                            "projectLocation__parent",
                            "projectLocation__parent__parent",
                        )
                        .filter(
                            Q(projectLocation=instance)
                            | Q(projectLocation__parent=instance)
                            | Q(projectLocation__parent__parent=instance)
                        )
                    )
            return Project.objects.none()
        if _type == "ProjectClass":
            if for_coordinator == True:
                return (
                    Project.objects.select_related("projectClass")
                    .prefetch_related("finances", "projectClass__coordinatorClass")
                    .filter(
                        projectClass__coordinatorClass__path__startswith=instance.path
                    )
                )
            else:
                return (
                    Project.objects.select_related("projectClass")
                    .prefetch_related("finances")
                    .filter(projectClass__path__startswith=instance.path)
                )

        if _type == "ProjectGroup":
            return ProjectService.find_by_group_id(
                group_id=instance.id
            ).prefetch_related("finances")

        return Project.objects.none()
