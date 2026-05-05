"""Tests for the IO-865 ``find_pw_orphans`` management command.

The command iterates programmed projects with an ``hkrId`` and asks
ProjectWise for each one. Projects that PW reports as missing are
listed as orphans on stdout (CSV); PW response errors are listed as
``pw_response_error`` rows. The command exits with code 1 if any
orphan was found.
"""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from infraohjelmointi_api.models import Project
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
)


def _make_project(name: str, *, hkr_id: int | None, programmed: bool = True) -> Project:
    return Project.objects.create(
        name=name,
        description="-",
        hkrId=hkr_id,
        programmed=programmed,
    )


def _run(*args: str):
    """Run the command and return (stdout, stderr, exit_code).

    ``exit_code`` is ``None`` when the command completed normally.
    """
    out = StringIO()
    err = StringIO()
    exit_code: int | None = None
    try:
        call_command("find_pw_orphans", *args, stdout=out, stderr=err)
    except SystemExit as exc:
        exit_code = int(exc.code) if exc.code is not None else 0
    return out.getvalue(), err.getvalue(), exit_code


@patch("infraohjelmointi_api.management.commands.find_pw_orphans.ProjectWiseService")
class FindPwOrphansCommandTestCase(TestCase):
    def test_no_candidates_exits_cleanly(self, mock_pw_cls):
        # Project that should not be checked: not programmed.
        _make_project("Not programmed", hkr_id=111, programmed=False)
        # Project that should not be checked: no hkrId.
        _make_project("No hkrId", hkr_id=None, programmed=True)

        stdout, stderr, exit_code = _run()

        mock_pw_cls.return_value.get_project_from_pw.assert_not_called()
        self.assertIn("id,name,hkrId,reason", stdout)
        self.assertIn("checked=0 ok=0 orphans=0 pw_errors=0", stderr)
        self.assertIsNone(exit_code)

    def test_all_projects_ok_exits_cleanly(self, mock_pw_cls):
        _make_project("A", hkr_id=1)
        _make_project("B", hkr_id=2)
        mock_pw_cls.return_value.get_project_from_pw.return_value = {"ok": True}

        stdout, stderr, exit_code = _run()

        self.assertEqual(
            mock_pw_cls.return_value.get_project_from_pw.call_count, 2
        )
        # Only the header row, no orphan/error rows.
        self.assertEqual(stdout.strip().splitlines(), ["id,name,hkrId,reason"])
        self.assertIn("checked=2 ok=2 orphans=0 pw_errors=0", stderr)
        self.assertIsNone(exit_code)

    def test_orphan_is_reported_and_exits_with_code_1(self, mock_pw_cls):
        ok_project = _make_project("Ok", hkr_id=10)
        orphan = _make_project("Orphan", hkr_id=20)

        def fake_get(hkr_id):
            if hkr_id == orphan.hkrId:
                raise PWProjectNotFoundError(
                    f"No project found from PW with given id '{hkr_id}'"
                )
            return {"ok": True}

        mock_pw_cls.return_value.get_project_from_pw.side_effect = fake_get

        stdout, stderr, exit_code = _run()

        self.assertIn(f"{orphan.id},Orphan,20,not_found", stdout)
        self.assertNotIn(str(ok_project.id), stdout)
        self.assertIn("checked=2 ok=1 orphans=1 pw_errors=0", stderr)
        self.assertEqual(exit_code, 1)

    def test_pw_response_error_is_reported_without_failing(self, mock_pw_cls):
        broken = _make_project("Broken", hkr_id=30)
        mock_pw_cls.return_value.get_project_from_pw.side_effect = (
            PWProjectResponseError("PW returned 500")
        )

        stdout, stderr, exit_code = _run()

        self.assertIn(f"{broken.id},Broken,30,pw_response_error", stdout)
        self.assertIn("checked=1 ok=0 orphans=0 pw_errors=1", stderr)
        # Response errors are reported but should not flip the exit code.
        self.assertIsNone(exit_code)

    def test_limit_option_caps_number_of_checks(self, mock_pw_cls):
        # Names are ordered alphabetically by the command (.order_by("name")),
        # so only the first one ("A") should be checked when --limit 1.
        _make_project("A", hkr_id=1)
        _make_project("B", hkr_id=2)
        _make_project("C", hkr_id=3)
        mock_pw_cls.return_value.get_project_from_pw.return_value = {"ok": True}

        _, stderr, _ = _run("--limit", "1")

        self.assertEqual(
            mock_pw_cls.return_value.get_project_from_pw.call_count, 1
        )
        mock_pw_cls.return_value.get_project_from_pw.assert_called_with(1)
        self.assertIn("checked=1 ok=1 orphans=0 pw_errors=0", stderr)
