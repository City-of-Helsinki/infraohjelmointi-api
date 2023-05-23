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
                "finances__budgetProposalCurrentYearPlus0",
                default=0,
                filter=Q(finances__year=year),
            ),
            year1_plannedBudget=Sum(
                "finances__budgetProposalCurrentYearPlus1",
                default=0,
                filter=Q(finances__year=year),
            ),
            year2_plannedBudget=Sum(
                "finances__budgetProposalCurrentYearPlus2",
                default=0,
                filter=Q(finances__year=year),
            ),
            year3_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus3",
                default=0,
                filter=Q(finances__year=year),
            ),
            year4_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus4",
                default=0,
                filter=Q(finances__year=year),
            ),
            year5_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus5",
                default=0,
                filter=Q(finances__year=year),
            ),
            year6_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus6",
                default=0,
                filter=Q(finances__year=year),
            ),
            year7_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus7",
                default=0,
                filter=Q(finances__year=year),
            ),
            year8_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus8",
                default=0,
                filter=Q(finances__year=year),
            ),
            year9_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus9",
                default=0,
                filter=Q(finances__year=year),
            ),
            year10_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus10",
                default=0,
                filter=Q(finances__year=year),
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
        if _type == "ProjectLocation":
            if instance.parent is None:
                return Project.objects.filter(
                    Q(projectLocation=instance)
                    | Q(projectLocation__parent=instance)
                    | Q(projectLocation__parent__parent=instance)
                ).prefetch_related("finances")
            return Project.objects.none()
        if _type == "ProjectClass":
            return Project.objects.filter(
                projectClass__path__startswith=instance.path
            ).prefetch_related("finances")

        if _type == "ProjectGroup":
            return ProjectService.find_by_group_id(
                group_id=instance.id
            ).prefetch_related("finances")

        return Project.objects.none()
