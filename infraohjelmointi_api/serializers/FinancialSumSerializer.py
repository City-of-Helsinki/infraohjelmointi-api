from datetime import date
from infraohjelmointi_api.models import Project, ClassFinancial, ProjectClass
from infraohjelmointi_api.services import ProjectService, ClassFinancialService
from rest_framework import serializers
from django.db.models import Sum, F, Case, When, Value, BooleanField, Q
from django.db.models.functions import Coalesce


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def get_frameBudget_and_budgetChange(self, instance, year: str) -> int:
        for_coordinator = self.context.get("for_coordinator", False)
        _type = instance._meta.model.__name__

        if for_coordinator == False:
            # get coordinatorClass when planning classes are being fetched
            instance = getattr(instance, "coordinatorClass", None)

        if instance == None or _type != "ProjectClass":
            return {"frameBudget": 0, "budgetChange": 0, "isFrameBudgetOverlap": False}

        classFinanceObject: ClassFinancial = (
            ClassFinancialService.get(class_id=instance.id, year=year)
            if _type == "ProjectClass"
            and instance != None
            and instance.finances.filter(year=year).exists()
            else None
        )

        childClassFrameBudgetSum = ClassFinancial.objects.aggregate(
            childFrameBudgetSum=Sum(
                "frameBudget",
                default=0,
                filter=Q(classRelation__path__startswith=instance.path)
                & Q(classRelation__path__gt=instance.path)
                & Q(year=year)
                & Q(classRelation__forCoordinatorOnly=True),
            ),
        )["childFrameBudgetSum"]

        return {
            "frameBudget": classFinanceObject.frameBudget
            if classFinanceObject != None
            else 0,
            "budgetChange": classFinanceObject.budgetChange
            if classFinanceObject != None
            else 0,
            "isFrameBudgetOverlap": childClassFrameBudgetSum
            > classFinanceObject.frameBudget
            if classFinanceObject != None
            else False,
        }

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

        return summedFinances

    def get_related_projects(self, instance, _type) -> list[Project]:
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
            return ProjectService.find_by_group_id(
                group_id=instance.id
            ).prefetch_related("finances")

        return Project.objects.none()
