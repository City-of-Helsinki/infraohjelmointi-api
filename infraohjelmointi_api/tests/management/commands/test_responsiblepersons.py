from io import StringIO
from os import path
import tempfile
from unittest.mock import patch
from django.core.management import call_command
from django.core.management.base import CommandError

from django.test import TestCase
import environ
import pandas as pd

from infraohjelmointi_api.services import PersonService

if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()

import logging
logger = logging.getLogger("infraohjelmointi_api")

class ResponsiblePersonsCommandTestCase(TestCase):
    # Columns does not have a header row.
    # Because of that, the first row includes person information
    mock_data = {
        'Matt': ["Sarah", "Max", "Peter", "John"],
        'Smith': ["Example", "Test", "Incorrect-Email", "Empty-Email"],
        'email1@example.com': ["email2@example.com", "email3@example.com", "email(at)example.com", ""]
    }

    def test_without_arguments(self):
        # Script without arguments
        out = StringIO()
        call_command("responsiblepersons", stdout=out)
        self.assertIn("No arguments given.", out.getvalue())

    def test_with_file_argument_without_file(self):
        # Script with argument without the file name
        with self.assertRaises(CommandError):
            call_command("responsiblepersons", "--file")

    def test_with_file_argument_with_incorrect_file(self):
        # Script with unknown file name
        out = StringIO()

        call_command("responsiblepersons", "--file", "unknown-file.xlsx", stdout=out)
        command_output = out.getvalue()

        expected_error_message = "\x1b[31;1mExcel file path is incorrect or missing. Usage: --file path/to/file.xlsx\x1b[0m\n"

        self.assertIn(expected_error_message, command_output)

    def test_populate_db_with_excel(self):
        # Script with mock data file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            mock_df = pd.DataFrame(self.mock_data)
            mock_df.to_excel(tmp.name, index=False)

        call_command("responsiblepersons", "--file", tmp.name)

        persons = PersonService.get_all_persons()

        self.assertEqual(len(persons), 3, "The count of successfully added person should be three")
