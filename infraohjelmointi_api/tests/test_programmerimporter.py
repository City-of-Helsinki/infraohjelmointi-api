from django.test import TestCase
from django.core.management import call_command
from io import StringIO
import tempfile
import os

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from infraohjelmointi_api.models import ProjectClass, ProjectProgrammer, Project
from infraohjelmointi_api.models.ProjectPhase import ProjectPhase


class ProgrammerImporterTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.phase_proposal, _ = ProjectPhase.objects.get_or_create(value="proposal")

        cls.master_class = ProjectClass.objects.create(
            name="8 Katujen perusparantaminen"
        )

        cls.class_traffic = ProjectClass.objects.create(
            name="8 01 Liikennejärjestelyt",
            parent=cls.master_class
        )

        cls.subclass_east = ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            parent=cls.class_traffic
        )

        cls.programmer_saija = ProjectProgrammer.objects.create(
            firstName="TestProgrammer",
            lastName="Test"
        )

    def _create_test_excel(self, assignments):
        if not OPENPYXL_AVAILABLE:
            self.skipTest("openpyxl not available")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Class Code", "Description", "Programmer"])

        for assignment in assignments:
            ws.append(assignment)

        fd, path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        wb.save(path)
        return path

    def test_dry_run_mode(self):
        excel_path = self._create_test_excel([
            ["8 01", "Liikennejärjestelyt", "TestProgrammer Test"]
        ])

        try:
            out = StringIO()
            call_command('programmerimporter', '--file', excel_path, '--dry-run', stdout=out)

            output = out.getvalue()
            self.assertIn("DRY RUN MODE", output)

            self.class_traffic.refresh_from_db()
            self.assertIsNone(self.class_traffic.defaultProgrammer)
        finally:
            os.unlink(excel_path)

    def test_specific_assignment(self):
        excel_path = self._create_test_excel([
            ["8 01", "Liikennejärjestelyt", "TestProgrammer Test"]
        ])

        try:
            call_command('programmerimporter', '--file', excel_path, '--skip-projects')

            self.class_traffic.refresh_from_db()
            self.assertIsNotNone(self.class_traffic.defaultProgrammer)
            self.assertEqual(self.class_traffic.defaultProgrammer.firstName, "TestProgrammer")
        finally:
            os.unlink(excel_path)

    def test_hierarchical_fallback(self):
        self.class_traffic.defaultProgrammer = self.programmer_saija
        self.class_traffic.save()

        project = Project.objects.create(
            name="Test Project",
            description="Test",
            projectClass=self.subclass_east,
            phase=self.phase_proposal
        )

        excel_path = self._create_test_excel([
            ["8 01", "Liikennejärjestelyt", "TestProgrammer Test"]
        ])

        try:
            call_command('programmerimporter', '--file', excel_path)

            project.refresh_from_db()
            self.assertIsNotNone(project.personProgramming)
            self.assertEqual(project.personProgramming.firstName, "TestProgrammer")
        finally:
            os.unlink(excel_path)
