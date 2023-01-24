from django.core.management.base import BaseCommand, CommandError

import requests
import os
from os import path


import environ

from django.db import transaction
from .util.budjetfilehandler import proceedWithBudjetFile
from .util.pwhandler import proceedWithPWArgument


requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"
if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()


class Command(BaseCommand):
    help = (
        "Populates the DB with project excel data. "
        + "\nUsage: python manage.py projectimporter"
        + " --import-from-budjet /path/to/budjet.xsls"
        + " --import-from-plan /path/to/plan.xsls"
    )

    def add_arguments(self, parser):
        """
        Add the following arguments to the manageclasses command

        --import-from-budjet /path/to/budjet.xsls"
        --import-from-plan /path/to/plan.xsls"
        """

        ## --import-from-budjet argument, used to provide the path to excel file
        ## which contains project budjet data, must give full path
        parser.add_argument(
            "--import-from-budjet",
            type=str,
            help=(
                "Argument to give full path to the budjet excel file. "
                + "Usage: --import-from-budjet /path/to/budjet.xsls"
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

        ## --import-from-pw argument, used to import data from PW
        parser.add_argument(
            "--import-from-pw",
            action="store_true",
            help=(
                "Argument to load data from PW into local DB. "
                + "Usage: --import-from-pw"
            ),
        )

    def handle(self, *args, **options):
        print("in handle")

        if (
            not options["import_from_pw"]
            and not options["import_from_budjet"]
            and not options["import_from_plan"]
        ):
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py projectimporter"
                    + " --import-from-budjet /path/to/budjet.xsls"
                    + " --import-from-plan /path/to/plan.xsls"
                    + " [--import-from-pw]"
                )
            )
            return

        if "import_from_pw" in options:
            proceedWithPWArgument(
                session=requests.Session(),
                env=env,
                stdout=self.stdout,
                style=self.style,
            )
            return

        self.proceedWithFileArgument(
            "--import-from-budjet", "import_from_budjet", options, proceedWithBudjetFile
        )
        # self.proceedWithArgument("--import-from-plan", "import_from_plan", options)

    @transaction.atomic
    def proceedWithFileArgument(self, argument, option, options, handler):
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
                handler(options[option], self.stdout, self.style)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        "Error occurred while reading file {}. Error: {}".format(
                            options[option], e
                        )
                    )
                )
