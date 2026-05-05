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

from infraohjelmointi_api.models import (
    ProjectClass,
    ProjectLocation,
    ProjectProgrammer,
    Project,
)
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

        cls.programmer_anna = ProjectProgrammer.objects.create(
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
        self.class_traffic.defaultProgrammer = self.programmer_anna
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

    def test_location_based_backfill(self):
        """
        IO-411: a project picks a generic class (e.g. Liikennejärjestelyt)
        plus a suurpiiri location. The class chain has no programmer, but a
        programmer-view ProjectClass with the same name as the location does.
        The importer must backfill via the location chain.
        """
        programmer = ProjectProgrammer.objects.create(
            firstName="Anna", lastName="Esimerkki"
        )
        # Programmer-view suurpiiri ProjectClass with default programmer
        ProjectClass.objects.create(
            name="Itäinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=programmer,
        )
        # Generic class with no default programmer anywhere up the chain
        generic_class = ProjectClass.objects.create(name="Liikennejärjestelyt")
        location = ProjectLocation.objects.create(name="Itäinen suurpiiri")

        project = Project.objects.create(
            name="Test traffic calming project",
            description="Test",
            projectClass=generic_class,
            projectLocation=location,
            phase=self.phase_proposal,
        )

        excel_path = self._create_test_excel([
            ["8 01", "Liikennejärjestelyt", "TestProgrammer Test"]
        ])

        try:
            call_command('programmerimporter', '--file', excel_path)
            project.refresh_from_db()
            self.assertIsNotNone(project.personProgramming)
            self.assertEqual(project.personProgramming.firstName, "Anna")
            self.assertEqual(project.personProgramming.lastName, "Esimerkki")
        finally:
            os.unlink(excel_path)

    def test_location_only_backfill_with_no_class(self):
        """
        Even when projectClass is null, a project with a suurpiiri location
        should still get a programmer assigned.
        """
        programmer = ProjectProgrammer.objects.create(
            firstName="Eero", lastName="Esimerkki"
        )
        ProjectClass.objects.create(
            name="Läntinen suurpiiri",
            forCoordinatorOnly=False,
            defaultProgrammer=programmer,
        )
        location = ProjectLocation.objects.create(name="Läntinen suurpiiri")

        project = Project.objects.create(
            name="Some western project",
            description="Test",
            projectClass=None,
            projectLocation=location,
            phase=self.phase_proposal,
        )

        excel_path = self._create_test_excel([
            ["8 01", "Liikennejärjestelyt", "TestProgrammer Test"]
        ])

        try:
            call_command('programmerimporter', '--file', excel_path)
            project.refresh_from_db()
            self.assertIsNotNone(project.personProgramming)
            self.assertEqual(project.personProgramming.firstName, "Eero")
        finally:
            os.unlink(excel_path)
