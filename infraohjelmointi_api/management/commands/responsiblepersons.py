import os
import traceback

from openpyxl import load_workbook
from infraohjelmointi_api.services import PersonService
from django.core.management.base import BaseCommand

import logging
logger = logging.getLogger("infraohjelmointi_api")

class Command(BaseCommand):
    help = (
        "Populates the DB with person information. "
        + "\nOne person per a line, first name and second name in different cells: "
        + "\n[firstName | lastName]"
        + "\nUsage: python manage.py addusers --file <path/to/excel.xlsx>"
    )

    def add_arguments(self, parser):
        """
        Add the following arguments to the hierarchies command

        --file /folder/file.xlsx
        """
        parser.add_argument(
            "--file",
            type=str,
            help=(
                "Argument to give full path to the excel file. "
                + "Usage: --file /folder/folder/file.xlsx"
            ),
            default="",
        )

    def handle(self, *args, **options):
        if not options["file"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py responsiblepersons --file <path/to/excel.xlsx>"
                )
            )
            return

        if not os.path.isfile(options["file"]):
            self.stdout.write(
                self.style.ERROR(
                    "Excel file path is incorrect or missing. Usage: --file path/to/file.xlsx"
                )
            )
            return

        try:
            self.populateDBWithExcel(excelPath=options["file"])
            self.stdout.write(
                self.style.SUCCESS(
                    "Done."
                )
            )
        except Exception as e:
            traceback.print_stack(e)
            self.stdout.write(self.style.ERROR(e))

    def populateDBWithExcel(self, excelPath):
        """
        Add every person from the excel file.
        [firstName | lastName | email]
        """
        wb = load_workbook(excelPath, data_only=True, read_only=True)
        rows = list(wb.worksheets[0].rows)
        incorrect_emails = []

        for row in rows:
            if len(row) < 2:
                continue

            firstname = str(row[0].value).strip()
            lastname = str(row[1].value).strip()
            email = str(row[2].value).strip()

            # Filter empty rows in case something is saved in the cell
            if firstname == "None" and lastname == "None" and email == "None":
                continue

            # Check the email is correct.
            if '@' not in email or not email:
                incorrect_emails.append((firstname, lastname, email))
                continue

            person, _ = PersonService.get_or_create_by_name_and_email(
                firstName=firstname, lastName=lastname, email=email
            )

            if person:
                logger.info(
                    "Person added: {} {}, email '{}' ({})".format(
                        person.firstName, person.lastName, person.email, person.id
                    )
                )

        # Print list of incorrect email data
        if len(incorrect_emails) > 0:
            printable_list = "Error with following data:"

            for incorrect_person in incorrect_emails:
                printable_list += "\n{} {}, email: '{}'".format(
                    incorrect_person[0], incorrect_person[1], incorrect_person[2]
                )

            logger.error(printable_list)
