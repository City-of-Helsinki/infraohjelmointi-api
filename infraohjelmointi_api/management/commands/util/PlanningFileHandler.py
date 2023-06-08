from openpyxl import load_workbook
import re
from .hierarchy import buildHierarchiesAndProjects, getColor, MAIN_CLASS_COLOR
from ....services import PersonService, ProjectService, NoteService
from . import IExcelFileHandler


class PlanningFileHandler(IExcelFileHandler):
    """Excel file handler implementation for planning data"""

    def proceed_with_file(self, excel_path, stdout, style):
        stdout.write(
            style.ERROR(
                "\n\nReading project data from planning file {}\n".format(excel_path)
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

        main_class = [
            cel[0]
            for cel in wb.worksheets[0][3:11]
            if cel[0].value
            and re.match("^\d \d\d.+", cel[0].value.strip())
            and hex(int(getColor(wb, cel[0].fill.start_color), 16)) == MAIN_CLASS_COLOR
        ][0].value

        for sheetname in wb.sheetnames:
            stdout.write(style.NOTICE("\n\nHandling sheet {}\n".format(sheetname)))

            sheet = wb[sheetname]
            rows = list(sheet.rows)

            buildHierarchiesAndProjects(
                wb=wb,
                rows=rows,
                skipables=skipables,
                main_class=main_class,
                project_handler=self.proceed_with_project_row,
            )

        stdout.write(style.SUCCESS("\n\nTotal rows handled  {}\n".format(len(rows))))

        stdout.write(style.SUCCESS("Planning file import done\n\n"))

    def proceed_with_project_row(
        self, row, name, project_class, project_location, project_group
    ):
        sapNumber = row[1].value
        sapNetwork = row[2].value
        projectManager = row[4].value.strip() if row[4].value else None
        responsiblePerson = (
            PersonService.get_or_create_by_last_name(lastName=projectManager)[0]
            if projectManager and projectManager != "?"
            else None
        )
        pwNumber = row[29].value

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

        project.sapProject = sapNumber
        project.sapNetwork = (
            [sapNetwork]
            if sapNetwork != None and not str(sapNetwork).strip() in ['"', "?"]
            else None
        )
        project.hkrId = pwNumber
        project.personPlanning = responsiblePerson
        project.save()

        notes = str(row[28].value).strip()
        if notes != "None" and notes != "?":
            NoteService.create(
                content=notes,
                project=project,
                byPerson=responsiblePerson
                if responsiblePerson
                else PersonService.get_or_create_by_name(
                    firstName="Excel", lastName="Integraatio"
                )[0],
            )
