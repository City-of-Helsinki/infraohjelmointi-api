from django.core.management.base import BaseCommand

from django.db import transaction
from ...services import PersonService
from openpyxl import load_workbook

import logging
import re

logger = logging.getLogger("infraohjelmointi_api")

class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        Add the following arguments to the hierarchies command

        --file /folder/folder/file.xlsx
        --sync-locations-from-pw
        """

        ## --file, used to tell the script to populate local db with
        ## person data using the path provided in the --file argument
        parser.add_argument(
            "--file",
            type=str,
            help=(
                "Argument to give full path to the excel file containing Class/Location data. "
                + "Usage: --file /folder/folder/file.xlsx"
            ),
            default="",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        wb = load_workbook(options["file"], data_only=True, read_only=True)
        rows = list(wb.worksheets[0].rows)
        for row in rows:
            lastName = row[0]
            if lastName.value:
                logging.info(lastName.value)
                if len(row) > 1:
                    firstName = row[1]
                    logging.info(firstName.value)
                    PersonService().get_or_create_by_name(firstName.value, lastName.value)
                else:
                    logging.info("no first name")
                    PersonService().get_or_create_by_last_name(lastName.value)
