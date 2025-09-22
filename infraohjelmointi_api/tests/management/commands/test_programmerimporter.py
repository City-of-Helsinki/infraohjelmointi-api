from io import StringIO
import os
from os import path
from openpyxl import Workbook
import tempfile
from django.core.management import call_command
from django.core.management.base import CommandError

from django.test import TestCase
import environ

from infraohjelmointi_api.models import (
    ProjectClass,
    ProjectProgrammer,
    Person,
    ProjectType,
    ProjectCategory
)

if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()

import logging
logger = logging.getLogger("infraohjelmointi_api")


class ProgrammerImporterCommandTestCase(TestCase):
    """Test cases for programmerimporter management command"""

    def setUp(self):
        """Set up test data"""
        # Track initial state for tests
        self.initial_programmer_count = ProjectProgrammer.objects.count()
        self.initial_assigned_classes = ProjectClass.objects.exclude(defaultProgrammer=None).count()

        # Create test project type and category for ProjectClass
        self.project_type, _ = ProjectType.objects.get_or_create(value="test")
        self.project_category, _ = ProjectCategory.objects.get_or_create(value="test")

        # Create test project classes
        self.class1 = ProjectClass.objects.create(
            name="8 01 03 Esirakentaminen test class",
            forCoordinatorOnly=True,
            path="001"
        )
        self.class2 = ProjectClass.objects.create(
            name="8 04 01 02 Liikuntapaikat test class",
            forCoordinatorOnly=True,
            path="002"
        )
        self.district_class = ProjectClass.objects.create(
            name="Keskinen suurpiiri test district",
            forCoordinatorOnly=True,
            path="003"
        )

        # Create a test person
        self.test_person = Person.objects.create(
            firstName="Satu",
            lastName="Järvinen",
            email="satu.jarvinen@test.com"
        )

    def create_test_excel_file(self, include_fallbacks=True):
        """Create a temporary Excel file with test data"""
        wb = Workbook()
        ws = wb.active

        # Header row
        ws.append(['Code', 'Description', 'Programmer'])

        # Specific assignments
        ws.append(['8 01 03', 'Esirakentaminen', 'Satu Järvinen'])
        ws.append(['8 04 01 02', 'Liikuntapaikat', 'Hanna Mikkola'])
        ws.append(['UNKNOWN', 'Unknown class', 'Test Programmer'])
        ws.append(['8 01 01', 'Empty assignment', 'jätetään tyhjiksi'])

        if include_fallbacks:
            # Empty row and fallback section
            ws.append(['', '', ''])
            ws.append(['Muut kohdat lokaatiotiedon mukaan', '', ''])
            ws.append(['Keskinen suurpiiri', '', 'Petri Arponen'])
            ws.append(['Unknown District', '', 'Unknown Programmer'])

        return wb

    def test_without_arguments(self):
        """Test command without any arguments"""
        with self.assertRaises(CommandError) as context:
            call_command("programmerimporter")

        self.assertIn("Excel file path is incorrect or missing", str(context.exception))

    def test_with_incorrect_file_path(self):
        """Test command with non-existent file"""
        with self.assertRaises(CommandError) as context:
            call_command("programmerimporter", "--file", "nonexistent.xlsx")

        self.assertIn("Excel file path is incorrect or missing", str(context.exception))

    def test_dry_run_mode(self):
        """Test dry-run mode shows preview without making changes"""
        wb = self.create_test_excel_file()

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb.save(tmp.name)

            out = StringIO()
            call_command("programmerimporter", "--file", tmp.name, "--dry-run", stdout=out)

            output = out.getvalue()

            # Should show dry run message
            self.assertIn("DRY RUN MODE", output)
            self.assertIn("SPECIFIC ASSIGNMENTS", output)
            self.assertIn("FALLBACK ASSIGNMENTS", output)

            # Should show found classes
            self.assertIn("Found class: 8 01 03", output)
            self.assertIn("Found class: 8 04 01 02", output)

            # Should show unfound classes
            self.assertIn("No project class found containing code 'UNKNOWN'", output)

            # Verify no new programmers were created in dry-run mode
            self.assertEqual(ProjectProgrammer.objects.count(), self.initial_programmer_count)
            self.assertEqual(ProjectClass.objects.exclude(defaultProgrammer=None).count(), self.initial_assigned_classes)

            os.remove(tmp.name)

    def test_process_assignments_successfully(self):
        """Test successful processing of programmer assignments"""
        wb = self.create_test_excel_file()

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb.save(tmp.name)

            out = StringIO()
            call_command("programmerimporter", "--file", tmp.name, stdout=out)

            output = out.getvalue()

            # Should show import completion
            self.assertIn("IMPORTING PROGRAMMERS", output)
            self.assertIn("import completed successfully", output)

            # Verify programmers were created
            satu = ProjectProgrammer.objects.filter(firstName="Satu", lastName="Järvinen").first()
            self.assertIsNotNone(satu)
            self.assertEqual(satu.person, self.test_person)  # Should link to existing person

            hanna = ProjectProgrammer.objects.filter(firstName="Hanna", lastName="Mikkola").first()
            self.assertIsNotNone(hanna)

            petri = ProjectProgrammer.objects.filter(firstName="Petri", lastName="Arponen").first()
            self.assertIsNotNone(petri)

            # Verify assignments were made
            self.class1.refresh_from_db()
            self.class2.refresh_from_db()
            self.district_class.refresh_from_db()

            self.assertEqual(self.class1.defaultProgrammer, satu)
            self.assertEqual(self.class2.defaultProgrammer, hanna)
            self.assertEqual(self.district_class.defaultProgrammer, petri)  # Fallback assignment

            # Verify total counts increased
            total_programmers = ProjectProgrammer.objects.count()
            assigned_classes = ProjectClass.objects.exclude(defaultProgrammer=None).count()

            self.assertGreaterEqual(total_programmers, self.initial_programmer_count + 3)
            self.assertGreaterEqual(assigned_classes, self.initial_assigned_classes + 3)

            os.remove(tmp.name)

    def test_clear_existing_assignments(self):
        """Test clearing existing assignments before import"""
        # Create an existing assignment
        existing_programmer = ProjectProgrammer.objects.create(
            firstName="Existing",
            lastName="Programmer"
        )
        self.class1.defaultProgrammer = existing_programmer
        self.class1.save()

        wb = self.create_test_excel_file(include_fallbacks=False)

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb.save(tmp.name)

            out = StringIO()
            call_command("programmerimporter", "--file", tmp.name, "--clear-existing", stdout=out)

            output = out.getvalue()

            # Should show clearing message
            self.assertIn("Cleared", output)

            # Verify the existing assignment was cleared and new one assigned
            self.class1.refresh_from_db()
            self.assertNotEqual(self.class1.defaultProgrammer, existing_programmer)

            satu = ProjectProgrammer.objects.filter(firstName="Satu", lastName="Järvinen").first()
            self.assertEqual(self.class1.defaultProgrammer, satu)

            os.remove(tmp.name)

    def test_fallback_assignments_only_for_unassigned_classes(self):
        """Test that fallback assignments only apply to classes without specific programmers"""
        # Create a specific programmer assignment first
        specific_programmer = ProjectProgrammer.objects.create(
            firstName="Specific",
            lastName="Programmer"
        )
        self.district_class.defaultProgrammer = specific_programmer
        self.district_class.save()

        wb = self.create_test_excel_file()

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb.save(tmp.name)

            out = StringIO()
            call_command("programmerimporter", "--file", tmp.name, "--dry-run", stdout=out)

            output = out.getvalue()

            # Should show that no classes need fallback assignment
            self.assertIn("Classes without specific programmer: 0", output)

            os.remove(tmp.name)

    def test_error_handling_for_missing_classes(self):
        """Test proper error handling for missing project classes"""
        wb = Workbook()
        ws = wb.active

        # Header row
        ws.append(['Code', 'Description', 'Programmer'])
        # Row with non-existent class
        ws.append(['NONEXISTENT', 'Missing class', 'Test Programmer'])

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb.save(tmp.name)

            out = StringIO()
            call_command("programmerimporter", "--file", tmp.name, stdout=out)

            output = out.getvalue()

            # Should show error but complete successfully
            self.assertIn("No project class found containing code 'NONEXISTENT'", output)
            self.assertIn("Errors: 1", output)
            self.assertIn("import completed successfully", output)

            os.remove(tmp.name)

    def test_excel_file_parsing(self):
        """Test that Excel file is parsed correctly"""
        wb = self.create_test_excel_file()

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb.save(tmp.name)

            out = StringIO()
            call_command("programmerimporter", "--file", tmp.name, "--dry-run", stdout=out)

            output = out.getvalue()

            # Should show correct parsing
            self.assertIn("Found 3 specific assignments", output)  # Excluding empty and unknown
            self.assertIn("Found 2 fallback assignments", output)  # Excluding unknown district

            # Should identify the fallback section
            self.assertIn("Found fallback section", output)

            os.remove(tmp.name)
