from django.test import TestCase
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from unittest import mock
import environ
import uuid
from overrides import override
from os import path
import pandas as pd
import numpy as np

from ....models import Project, ProjectClass, ProjectLocation
from ....services.ProjectWiseService import PWProjectResponseError
from ....services import ProjectLocationService


if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()
PW_API_URL = env("PW_API_URL")
PW_API_LOCATION_ENDPOINT = env("PW_API_LOCATION_ENDPOINT")

PW_API_LOCATIONS = f"{PW_API_URL}{PW_API_LOCATION_ENDPOINT}"

HKR_ID = 123
PROJECT_ID = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
MAIN_CLASS_ID = uuid.UUID("f235991e-2148-4b64-a80c-a96410e152af")
CLASS_ID = uuid.UUID("8e04d891-346f-4b08-9d85-b641519ce7be")
SUBCLASS_ID = uuid.UUID("be7377e7-e1c4-4a64-add8-2e96d0b21693")

MAIN_DISTRICT_ID = uuid.UUID("02991525-945b-405e-a20e-6b8cbe1a5f5c")
DISTRICT_ID = uuid.UUID("7e215e9f-d432-4efa-a0ff-b731b77a9ff1")
SUB_DISTRICT_ID = uuid.UUID("38ecafbb-cd5f-4387-b5e2-31b9e3b8f763")


def _mock_response(
    status=200, content="CONTENT", json_data=None, raise_for_status=None
):
    """
    since we typically test a bunch of different
    requests calls for a service, we are going to do
    a lot of mock responses, so its usually a good idea
    to have a helper function that builds these things
    """
    mock_resp = mock.Mock()
    # mock raise_for_status call w/optional error
    mock_resp.raise_for_status = mock.Mock()
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    # set status code and content
    mock_resp.status_code = status
    mock_resp.content = content
    # add json data if provided
    if json_data:
        mock_resp.json = mock.Mock(return_value=json_data)
    return mock_resp


class ManageHierarchiesCommandTestCase(TestCase):
    @classmethod
    @override
    def setUpTestData(self):
        """
        Set up test data
        """

        Project.objects.create(
            id=PROJECT_ID,
            name="Test project",
            description="Description",
            hkrId=HKR_ID,
        )

        master_class = ProjectClass.objects.create(
            id=MAIN_CLASS_ID, name="Main Class", path="Main Class", parent=None
        )

        class_object = ProjectClass.objects.create(
            id=CLASS_ID, name="Class", path="Main Class/Class", parent=master_class
        )

        ProjectClass.objects.create(
            id=SUBCLASS_ID,
            name="Subclass",
            path="Main Class/Class/Subclass",
            parent=class_object,
        )

        district = ProjectLocation.objects.create(
            id=MAIN_DISTRICT_ID, name="District", path="District", parent=None
        )

        ProjectLocation.objects.create(
            id=DISTRICT_ID,
            name="Division",
            path="District/Division",
            parent=district,
        )

    def test_Without_Arguments(self):
        out = StringIO()
        call_command("hierarchies", stdout=out)
        self.assertIn("No arguments given.", out.getvalue())

    def test_With_File_Only_Argument(self):
        with self.assertRaises(CommandError):
            call_command(
                "hierarchies",
                "--file",
            )

    @mock.patch("requests.Session")
    def test_With_SyncWithPW_Only_ErrorResponse(self, session_mock):
        session_mock.return_value.get.return_value.status_code = 500
        session_mock.return_value.get.asswer_call_with(PW_API_LOCATIONS)
        with self.assertRaises(PWProjectResponseError):
            call_command(
                "hierarchies",
                "--sync-locations-with-pw",
            )

    @mock.patch("requests.Session")
    def test_With_SyncWithPW_Only_FetchOneLocationHierarchy(self, session_mock):
        session_mock.return_value.get.return_value = _mock_response(
            json_data={
                "instances": [
                    {
                        "properties": {
                            "PAALUOKKA": "District",
                            "LUOKKA": "Division",
                            "ALALUOKKA": "Sub division",
                        }
                    }
                ]
            }
        )
        session_mock.return_value.get.asswer_call_with(PW_API_LOCATIONS)

        call_command(
            "hierarchies",
            "--sync-locations-with-pw",
        )
        path = "District/Division/Sub Division"
        locations = ProjectLocationService.find_by_path(path)
        self.assertTrue(
            len(locations),
            f"Should find only one location with path '{path}'",
        )

        self.assertTrue(
            locations[0].path == path,
            f"Found location should have path '{path}'",
        )

    @mock.patch("requests.Session")
    def test_With_SyncWithPW_Only_ShouldNotStoreEmptySubDivision(self, session_mock):
        session_mock.return_value.get.return_value = _mock_response(
            json_data={
                "instances": [
                    {
                        "properties": {
                            "PAALUOKKA": "District",
                            "LUOKKA": "Division",
                            "ALALUOKKA": "",
                        }
                    }
                ]
            }
        )
        session_mock.return_value.get.asswer_call_with(PW_API_LOCATIONS)

        call_command(
            "hierarchies",
            "--sync-locations-with-pw",
        )

        path = "District/Division/"
        locations = ProjectLocationService.find_by_path(path)
        self.assertTrue(
            len(locations) == 0,
            f"Should not find any sub division location with '{path}'",
        )

    @mock.patch("requests.Session")
    def test_With_SyncWithPW_Only_ShouldNotStoreSubDivisionWithEmptyDivision(
        self, session_mock
    ):
        session_mock.return_value.get.return_value = _mock_response(
            json_data={
                "instances": [
                    {
                        "properties": {
                            "PAALUOKKA": "District",
                            "LUOKKA": "",
                            "ALALUOKKA": "Sub division",
                        }
                    }
                ]
            }
        )
        session_mock.return_value.get.asswer_call_with(PW_API_LOCATIONS)

        call_command(
            "hierarchies",
            "--sync-locations-with-pw",
        )

        path = "District//Sub Division"
        locations = ProjectLocationService.find_by_path(path)
        self.assertTrue(
            len(locations) == 0,
            f"Should not find any sub division location with '{path}'",
        )

    # The folowing tests must be refactored to use openpyxl
    # @mock.patch("pandas.read_excel")
    # def test_With_PopulateWithExcel_EmptyFile(self, pandas_mock):
    #     with mock.patch("os.path.isfile") as isFile:
    #         isFile.return_value = True
    #         pandas_mock.return_value = pd.DataFrame()
    #         out = StringIO()

    #         call_command(
    #             "hierarchies",
    #             "--file",
    #             file="notexisting.xsls",
    #             stdout=out,
    #         )

    #         self.assertIn(
    #             "Excel sheet should have the following columns only PÄÄLUOKKA, LUOKKA, ALALUOKKA",
    #             out.getvalue(),
    #         )

    # @mock.patch("pandas.read_excel")
    # def test_With_PopulateWithExcel_ColumnHeadersOnly(self, pandas_mock):
    #     with mock.patch("os.path.isfile") as isFile:
    #         isFile.return_value = True
    #         pandas_mock.return_value = pd.DataFrame(
    #             {"PÄÄLUOKKA": [], "LUOKKA": [], "ALALUOKKA": []}
    #         )

    #         call_command(
    #             "managehierarchies",
    #             "--populate-with-excel",
    #             file="notexisting.xsls",
    #         )
    #         # only Master Class, Class, and Subclass should remain in DB
    #         projectClasses = ProjectClass.objects.all()
    #         self.assertTrue(
    #             len(projectClasses) == 3, "No classes should be created from Excel file"
    #         )

    # @mock.patch("pandas.read_excel")
    # def test_With_PopulateWithExcel_CreatesOnlyMasterClass(self, pandas_mock):
    #     with mock.patch("os.path.isfile") as isFile:
    #         isFile.return_value = True
    #         pandas_mock.return_value = pd.DataFrame(
    #             {"PÄÄLUOKKA": ["Pääluokka"], "LUOKKA": [np.nan], "ALALUOKKA": [np.nan]}
    #         )
    #         out = StringIO()

    #         call_command(
    #             "managehierarchies",
    #             "--populate-with-excel",
    #             file="notexisting.xsls",
    #             stdout=out,
    #         )
    #         projectClasses = ProjectClass.objects.all()
    #         self.assertTrue(
    #             len(projectClasses) == 4, "One class should be created from Excel file"
    #         )
    #         projectClass = projectClasses[3]
    #         self.assertTrue(
    #             projectClass.name == "Pääluokka" and not projectClass.id == None,
    #             "Class 'Pälluokka' should be created from Excel file",
    #         )

    # @mock.patch("pandas.read_excel")
    # def test_With_PopulateWithExcel_CreatesOnlyMasterClassAndClass(self, pandas_mock):
    #     with mock.patch("os.path.isfile") as isFile:
    #         isFile.return_value = True
    #         pandas_mock.return_value = pd.DataFrame(
    #             {"PÄÄLUOKKA": ["Pääluokka"], "LUOKKA": ["Luokka"], "ALALUOKKA": [None]}
    #         )
    #         out = StringIO()

    #         call_command(
    #             "managehierarchies",
    #             "--populate-with-excel",
    #             file="notexisting.xsls",
    #             stdout=out,
    #         )
    #         projectClasses = ProjectClass.objects.all()
    #         self.assertTrue(
    #             len(projectClasses) == 5,
    #             "Two classes should be created from Excel file",
    #         )
    #         projectClass = projectClasses[3]
    #         self.assertTrue(
    #             projectClass.name == "Pääluokka" and not projectClass.id == None,
    #             "Class 'Pääluokka' should be created from Excel file",
    #         )

    #         projectClass = projectClasses[4]
    #         self.assertTrue(
    #             projectClass.name == "Luokka" and not projectClass.id == None,
    #             "Class 'Luokka' should be created from Excel file",
    #         )

    # @mock.patch("pandas.read_excel")
    # def test_With_PopulateWithExcel_CreatesMasterClassAndClassAndSubclass(
    #     self, pandas_mock
    # ):
    #     with mock.patch("os.path.isfile") as isFile:
    #         isFile.return_value = True
    #         pandas_mock.return_value = pd.DataFrame(
    #             {
    #                 "PÄÄLUOKKA": ["Pääluokka"],
    #                 "LUOKKA": ["Luokka"],
    #                 "ALALUOKKA": ["Alaluokka"],
    #             }
    #         )
    #         out = StringIO()

    #         call_command(
    #             "managehierarchies",
    #             "--populate-with-excel",
    #             file="notexisting.xsls",
    #             stdout=out,
    #         )
    #         projectClasses = ProjectClass.objects.all()
    #         self.assertTrue(
    #             len(projectClasses) == 6,
    #             "Three classes should be created from Excel file",
    #         )
    #         projectClass = projectClasses[3]
    #         self.assertTrue(
    #             projectClass.name == "Pääluokka" and not projectClass.id == None,
    #             "Class 'Pääluokka' should be created from Excel file",
    #         )

    #         projectClass = projectClasses[4]
    #         self.assertTrue(
    #             projectClass.name == "Luokka" and not projectClass.id == None,
    #             "Class 'Luokka' should be created from Excel file",
    #         )

    #         projectClass = projectClasses[5]
    #         self.assertTrue(
    #             projectClass.name == "Alaluokka" and not projectClass.id == None,
    #             "Class 'Alaluokka' should be created from Excel file",
    #         )
