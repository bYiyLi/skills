from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from novelctl.cli import main
from novelctl.engine import run_sync
from novelctl.workspace import init_workspace

from support import fill_specs, make_scene, register_character, replace_monolith_with_scenes


class NovelCtlCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run_cli(self, *argv: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                exit_code = main(list(argv))
            except SystemExit as exc:
                exit_code = int(exc.code)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _stdout_json(self, *argv: str) -> tuple[int, dict]:
        exit_code, stdout, stderr = self._run_cli(*argv)
        self.assertEqual(stderr.strip(), "")
        self.assertTrue(stdout.strip())
        return exit_code, json.loads(stdout)

    def test_init_and_check(self) -> None:
        exit_code, payload = self._stdout_json("init", self.workspace.as_posix())
        self.assertEqual(exit_code, 0)
        self.assertIn("WORK.md", "\n".join(payload["written"]))
        check_code, check_payload = self._stdout_json("check", self.workspace.as_posix())
        self.assertEqual(check_code, 0)
        self.assertEqual(check_payload["readiness"]["current"], "bootstrap-incomplete")

    def test_report_context_pack_profiles(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        register_character(self.workspace, "林野")
        replace_monolith_with_scenes(self.workspace, [make_scene(1, status="draft")])
        run_sync(self.workspace)
        for profile in ("draft", "check", "archive", "handoff"):
            exit_code, payload = self._stdout_json(
                "report",
                "context-pack",
                self.workspace.as_posix(),
                "--scene",
                "scene-0001",
                "--profile",
                profile,
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["profile"], profile)
            self.assertIn("project_state", payload)

    def test_archive_chapter_and_volume_dry_run(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        replace_monolith_with_scenes(self.workspace, [make_scene(1, status="ready"), make_scene(2, status="ready"), make_scene(3, status="ready")])
        run_sync(self.workspace)
        chapter_code, chapter_payload = self._stdout_json("archive", "chapter", self.workspace.as_posix(), "--dry-run", "--force")
        self.assertEqual(chapter_code, 0)
        self.assertTrue(chapter_payload["dry_run"])
        archive_code, _ = self._stdout_json("archive", "chapter", self.workspace.as_posix(), "--force")
        self.assertEqual(archive_code, 0)
        volume_code, volume_payload = self._stdout_json("archive", "volume", self.workspace.as_posix(), "--dry-run", "--force")
        self.assertEqual(volume_code, 0)
        self.assertTrue(volume_payload["dry_run"])

    def test_retrieve_source_browse(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        run_sync(self.workspace)
        exit_code, payload = self._stdout_json("retrieve", "source", self.workspace.as_posix(), "--browse")
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["browse_mode"])
        self.assertTrue(payload["results"])

    def test_help_text_and_removed_commands(self) -> None:
        exit_code, stdout, stderr = self._run_cli("init", "--help")
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.strip(), "")
        self.assertNotIn("--minimal", stdout)
        self.assertNotIn("--starter", stdout)
        self.assertNotIn("--active-draft-profile", stdout)

        exit_code, stdout, _ = self._run_cli("report", "context-pack", "--help")
        self.assertEqual(exit_code, 0)
        self.assertIn("--profile", stdout)
        self.assertIn("handoff", stdout)

        exit_code, _, stderr = self._run_cli("doctor", self.workspace.as_posix())
        self.assertNotEqual(exit_code, 0)
        self.assertTrue(stderr.strip())


if __name__ == "__main__":
    unittest.main()
