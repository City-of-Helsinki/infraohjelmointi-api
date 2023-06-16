from openpyxl import load_workbook
import datetime

from .hierarchy import buildHierarchiesAndProjects, getColor, MAIN_CLASS_COLOR
from ....services import (
    PersonService,
    ProjectService,
    NoteService,
    ProjectCategoryService,
    ProjectFinancialService,
)

from . import IExcelFileHandler
from django.contrib import messages
from io import BytesIO


class BudgetFileHandler(IExcelFileHandler):
    """Excel file handler implementation for budget data"""

    def __init__(self) -> None:
        super().__init__()
        self.project_categories_map = {
            str(pc.value).lower(): pc for pc in ProjectCategoryService.list_all()
        }
        self.current_budget_year = datetime.date.today().year

    def proceed_with_file(self, excel_path, stdout, style):
        stdout.write(
            style.ERROR(
                "\n\nReading project data from budget file {}\n".format(excel_path)
            )
        )

        wb = load_workbook(excel_path, data_only=True, read_only=True)

        skipables = [
            "none",
            "ylitysoikeus",
            "tae&tse raamit",
            "ylityspaine",
            "ylitysoikeus yhteensä",
        ]

        for sheetname in wb.sheetnames:
            stdout.write(style.NOTICE("\n\nHandling sheet {}\n".format(sheetname)))

            sheet = wb[sheetname]
            rows = list(sheet.rows)
            year_heading = None
            # there is a need to find the year for the budget file
            for year in rows[8:11]:
                if str(year[19].value).lower() == "tae":
                    year_heading = "tae"
                elif year_heading == "tae" and str(year[19].value).isnumeric():
                    self.current_budget_year = year[19].value
                    break

            buildHierarchiesAndProjects(
                wb=wb,
                rows=rows,
                skipables=skipables,
                project_handler=self.proceed_with_project_row,
            )

        stdout.write(style.SUCCESS("\n\nTotal rows handled  {}\n".format(len(rows))))

        stdout.write(style.SUCCESS("Planning file import done\n\n"))

    def proceed_with_uploaded_file(self, request, uploadedFile):
        messages.info(
            request,
            "Reading project data from budget file {}".format(uploadedFile.name),
        )

        wb = load_workbook(
            filename=BytesIO(uploadedFile.read()), data_only=True, read_only=True
        )

        skipables = [
            "none",
            "ylitysoikeus",
            "tae&tse raamit",
            "ylityspaine",
            "ylitysoikeus yhteensä",
        ]

        for sheetname in wb.sheetnames:
            messages.info(request, "\n\nHandling sheet {}\n".format(sheetname))

            sheet = wb[sheetname]
            rows = list(sheet.rows)

            buildHierarchiesAndProjects(
                wb=wb,
                rows=rows,
                skipables=skipables,
                project_handler=self.proceed_with_project_row,
            )

        messages.success(request, "\n\nTotal rows handled  {}\n".format(len(rows)))
        messages.success(request, "Planning file import done\n\n")

    def proceed_with_project_row(
        self, row, name, project_class, project_location, project_group
    ):
        category = None
        try:
            category = self.project_categories_map[str(row[1].value).strip().lower()]
        except:
            # nothing to do here
            pass

        effectHousing = str(row[2].value).strip()
        effectHousing = True if effectHousing == "K" else False
        costForecast = row[6].value

        budgetProposalCurrentYearPlus0 = row[19].value
        budgetProposalCurrentYearPlus1 = row[20].value
        budgetProposalCurrentYearPlus2 = row[21].value
        preliminaryCurrentYearPlus3 = row[22].value
        preliminaryCurrentYearPlus4 = row[23].value
        preliminaryCurrentYearPlus5 = row[24].value
        preliminaryCurrentYearPlus6 = row[25].value
        preliminaryCurrentYearPlus7 = row[26].value
        preliminaryCurrentYearPlus8 = row[27].value
        preliminaryCurrentYearPlus9 = row[28].value

        budget_sum = sum(
            [
                budgetProposalCurrentYearPlus0 or 0,
                budgetProposalCurrentYearPlus1 or 0,
                budgetProposalCurrentYearPlus2 or 0,
                preliminaryCurrentYearPlus3 or 0,
                preliminaryCurrentYearPlus4 or 0,
                preliminaryCurrentYearPlus5 or 0,
                preliminaryCurrentYearPlus6 or 0,
                preliminaryCurrentYearPlus7 or 0,
                preliminaryCurrentYearPlus8 or 0,
                preliminaryCurrentYearPlus9 or 0,
            ]
        )

        notes = str(row[29].value).strip()
        pwNumber = str(row[30].value).strip()

        try:
            project = ProjectService.get(
                name=name,
                projectClass=project_class,
                projectLocation=project_location,
                projectGroup=project_group,
            )
        except:
            project = ProjectService.create(
                name=name,
                projectClass=project_class,
                description="Kuvaus puuttuu",
                projectLocation=project_location,
                projectGroup=project_group,
            )

        try:
            project.programmed = budget_sum > 0
            project.category = category
            project.effectHousing = effectHousing
            # if value already converted into float, convert it back to string to void validation error
            project.costForecast = str(costForecast) if costForecast != None else None

            project_financial, created = ProjectFinancialService.get_or_create(
                year=self.current_budget_year, project_id=project.id
            )

            print(f"Project financial {project_financial.id} created {created}")

            project_financial.budgetProposalCurrentYearPlus0 = (
                str(budgetProposalCurrentYearPlus0)
                if budgetProposalCurrentYearPlus0 != None
                else None
            )

            project_financial.budgetProposalCurrentYearPlus1 = (
                str(budgetProposalCurrentYearPlus1)
                if budgetProposalCurrentYearPlus1 != None
                else None
            )
            project_financial.budgetProposalCurrentYearPlus2 = (
                str(budgetProposalCurrentYearPlus2)
                if budgetProposalCurrentYearPlus2 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus3 = (
                str(preliminaryCurrentYearPlus3)
                if preliminaryCurrentYearPlus3 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus4 = (
                str(preliminaryCurrentYearPlus4)
                if preliminaryCurrentYearPlus4 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus5 = (
                str(preliminaryCurrentYearPlus5)
                if preliminaryCurrentYearPlus5 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus6 = (
                str(preliminaryCurrentYearPlus6)
                if preliminaryCurrentYearPlus6 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus7 = (
                str(preliminaryCurrentYearPlus7)
                if preliminaryCurrentYearPlus7 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus8 = (
                str(preliminaryCurrentYearPlus8)
                if preliminaryCurrentYearPlus8 != None
                else None
            )
            project_financial.preliminaryCurrentYearPlus9 = (
                str(preliminaryCurrentYearPlus9)
                if preliminaryCurrentYearPlus9 != None
                else None
            )

            project_financial.save()

            project.hkrId = pwNumber if pwNumber != "None" and pwNumber != "?" else None
            project.save()
        except Exception as e:
            print(f"Project {name} handling ended in exception")
            print(e)

        if notes != "None" and notes != "?":
            NoteService.create(
                content=notes,
                project=project,
                byPerson=PersonService.get_or_create_by_name(
                    firstName="Excel", lastName="Integraatio"
                )[0],
            )
