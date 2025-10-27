from django.core.management.base import BaseCommand

import os

from django.db import transaction
from .util import IExcelFileHandler, PlanningFileHandler, BudgetFileHandler
from ...services import ProjectWiseService


class Command(BaseCommand):
    help = (
        "Populates the DB with project excel and synchronize with PW data. "
        + "\nUsage: python manage.py projectimporter"
        + " --import-from-budget /path/to/budget.xsls"
        + " --import-from-plan /path/to/plan.xsls"
        + " --sync-projects-from-pw"
        + " --sync-project-from-pw pwid"
        + " --sync-projects-to-pw"
        + " --sync-project-to-pw pwid"
    )

    def add_arguments(self, parser):
        """
        Add the following arguments to the manageclasses command

        --import-from-budget /path/to/budget.xsls"
        --import-from-plan /path/to/plan.xsls"
        """

        ## --import-from-budget argument, used to provide the path to excel file
        ## which contains project budget data, must give full path
        parser.add_argument(
            "--import-from-budget",
            type=str,
            help=(
                "Argument to give full path to the budget excel file. "
                + "Usage: --import-from-budget /path/to/budget.xsls"
            ),
            default="",
        )

        ## --import-from-plan argument, used to provide the path to excel file
        ## which contains project plan data, must give full path
        parser.add_argument(
            "--import-from-plan",
            type=str,
            help=(
                "Argument to give full path to the plan excel file. "
                + "Usage: --import-from-plan /path/to/plan.xsls"
            ),
            default="",
        )

        parser.add_argument(
            "--sync-projects-from-pw",
            action="store_true",
            help=(
                "Argument to give to synchronize all projects in DB which have PW id. "
                + "Usage: --sync-projects-from-pw"
            ),
        )

        parser.add_argument(
            "--sync-project-from-pw",
            type=str,
            help=(
                "Argument to give to synchronize given project PW id. "
                + "Usage: --sync-project-from-pw pw_id"
            ),
            default="",
        )

        parser.add_argument(
            "--sync-projects-to-pw",
            action="store_true",
            help=(
                    "Argument to give to synchronize all projects to PW if they have a PW id. "
                    + "Usage: --sync-projects-to-pw"
            ),
        )

        parser.add_argument(
            "--sync-project-to-pw",
            type=str,
            help=(
                    "Argument to give to synchronize given project to PW with PW id. "
                    + "Usage: --sync-project-to-pw pw_id"
            ),
            default="",
        )


    def handle(self, *args, **options):
        if (
            not options["sync_projects_from_pw"]
            and not options["sync_project_from_pw"]
            and not options["sync_projects_to_pw"]
            and not options["sync_project_to_pw"]
            and not options["import_from_budget"]
            and not options["import_from_plan"]
        ):
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. \n"
                    + "\nUsage: python manage.py projectimporter\n"
                    + " --import-from-budget /path/to/budget.xsls\n"
                    + " --import-from-plan /path/to/plan.xsls\n"
                    + " [--sync-projects-from-pw]\n"
                    + " [--sync-project-from-pw pwid]\n"
                    + " [--sync-projects-to-pw]\n"
                    + " [--sync-project-to-pw pwid]\n"
                )
            )
            return

        if options["sync_projects_from_pw"] == True:
            ProjectWiseService().sync_all_projects_from_pw()
            return

        if options["sync_project_from_pw"] != "":
            ProjectWiseService().sync_project_from_pw(options["sync_project_from_pw"])
            return

        if options["sync_projects_to_pw"] == True:
            service = ProjectWiseService()
            update_log = service.sync_all_projects_to_pw()

            # Print comprehensive summary
            successful = len([log for log in update_log if log['status'] == 'success'])
            skipped = len([log for log in update_log if log['status'] == 'skipped'])
            errors = len([log for log in update_log if log['status'] == 'error'])

            self.stdout.write(
                self.style.SUCCESS(
                    f"PRODUCTION mass update completed: {successful} successful, {skipped} skipped, {errors} errors"
                )
            )

            # Print detailed log for errors
            if errors > 0:
                self.stdout.write(self.style.WARNING(f"\n{errors} projects failed to update:"))
                for log in update_log:
                    if log['status'] == 'error':
                        self.stdout.write(
                            self.style.ERROR(
                                f"  - {log['project_name']} (HKR ID: {log['hkr_id']}): {log.get('error', 'Unknown error')}"
                            )
                        )

            # Print summary of successful updates
            if successful > 0:
                self.stdout.write(self.style.SUCCESS(f"\n{successful} projects updated successfully"))

            if skipped > 0:
                self.stdout.write(self.style.WARNING(f"{skipped} projects skipped (no data to update)"))

            return

        if options["sync_project_to_pw"] != "":
            ProjectWiseService().sync_project_to_pw(options["sync_project_to_pw"])
            return


        if options["import_from_budget"] != "":
            self.proceedWithFileArgument(
                argument="--import-from-budget",
                option="import_from_budget",
                options=options,
                handler=BudgetFileHandler(),
            )

        if options["import_from_plan"] != "":
            self.proceedWithFileArgument(
                argument="--import-from-plan",
                option="import_from_plan",
                options=options,
                handler=PlanningFileHandler(),
            )

    @transaction.atomic
    def proceedWithFileArgument(
        self, argument, option, options, handler: IExcelFileHandler
    ):
        if options[option]:
            if not os.path.isfile(options[option]):
                self.stdout.write(
                    self.style.ERROR(
                        "Excel file path is incorrect or missing. Usage: {} path/to/file.xlsx".format(
                            argument
                        )
                    )
                )
                return

            try:
                handler.proceed_with_file(options[option])

            except Exception as e:
                e.with_traceback()
                self.stdout.write(
                    self.style.ERROR(
                        "Error occurred while reading file {}. Error: {}".format(
                            options[option], e
                        )
                    )
                )
