from io import StringIO
from unittest.mock import patch

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from infraohjelmointi_api.models import Project, ProjectWiseFolder
from infraohjelmointi_api.services.ProjectWiseService import PWProjectNotFoundError


class RefreshPwFolderLinksTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project", description="-", hkrId=123)

    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    def test_refresh_looks_up_each_hkr_once(self, mock_get):
        Project.objects.create(name="Other project", description="-", hkrId=123)
        Project.objects.create(name="Unlinked project", description="-")
        mock_get.return_value = {"instanceId": "folder-123"}
        output = StringIO()
        call_command("refresh_pw_folder_links", stdout=output)
        self.assertEqual(ProjectWiseFolder.objects.get(hkrId=123).instanceId, "folder-123")
        mock_get.assert_called_once_with(123, timeout=15)
        self.assertIn("updated=1 missing=0 failed=0", output.getvalue())

    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    def test_failure_retains_cache_and_not_found_clears_it(self, mock_get):
        ProjectWiseFolder.objects.create(hkrId=123, instanceId="folder-123")
        for error in (requests.Timeout("unavailable"), {"instanceId": None}):
            with self.subTest(error=error):
                if isinstance(error, Exception):
                    mock_get.side_effect = error
                else:
                    mock_get.side_effect = None
                    mock_get.return_value = error
                with self.assertRaises(CommandError):
                    call_command("refresh_pw_folder_links", stdout=StringIO())
                self.assertEqual(ProjectWiseFolder.objects.get(hkrId=123).instanceId, "folder-123")

        mock_get.side_effect = PWProjectNotFoundError("missing")
        call_command("refresh_pw_folder_links", stdout=StringIO())
        self.assertFalse(ProjectWiseFolder.objects.filter(hkrId=123).exists())

    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    def test_refresh_updates_existing_folder(self, mock_get):
        ProjectWiseFolder.objects.create(hkrId=123, instanceId="old-folder")
        mock_get.return_value = {"instanceId": "new-folder"}
        call_command("refresh_pw_folder_links", stdout=StringIO())
        self.assertEqual(ProjectWiseFolder.objects.get(hkrId=123).instanceId, "new-folder")