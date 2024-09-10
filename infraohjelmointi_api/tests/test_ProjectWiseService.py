from django.test import TestCase
from unittest.mock import patch, MagicMock
from infraohjelmointi_api.models import Project, Person
from infraohjelmointi_api.services import ProjectWiseService


class SyncResponsiblePersonsFromPWTestCase(TestCase):
    def setUp(self):
        self.project_with_hkr_id = Project.objects.create(
            hkrId='12345',
            name="TestProjectWithHkrId",
            description="test")
        self.project_without_hkr_id = Project.objects.create(
            name="TestProjectWithHkrId",
            description="test"
        )

    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw')
    @patch('infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_person')
    @patch('infraohjelmointi_api.services.ProjectService.ProjectService.list_with_non_null_hkr_id')
    def test_sync_responsible_persons(self, mock_list_with_non_null_hkr_id, mock_get_project_person, mock_get_project_from_pw):
        mock_list_with_non_null_hkr_id.return_value = [self.project_with_hkr_id]
        mock_get_project_person.return_value = MagicMock(spec=Person)

        # Mock the get_project_from_pw method to return a simulated PW project response
        mock_get_project_from_pw.return_value = {
            "relationshipInstances": [{
                "relatedInstance": {
                    "properties": {
                        "PROJECT_Vastuuhenkil": "John Doe",
                        "PROJECT_Vastuuhenkiln_titteli": "Project Manager",
                        "PROJECT_Vastuuhenkiln_puhelinnumero": "1234567890",
                        "PROJECT_Vastuuhenkiln_shkpostiosoite": "john.doe@example.com"
                    }
                }
            }],
            "personPlanning": True
        }

        ProjectWiseService.sync_responsible_persons_from_pw(ProjectWiseService)

        # Assert that get_project_from_pw was called
        mock_get_project_from_pw.assert_called_with(12345)

        # Assert that __get_project_person was called with the correct data
        mock_get_project_person.assert_called_with(person_data="John Doe, Project Manager, 1234567890, john.doe@example.com")
