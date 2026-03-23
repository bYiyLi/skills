from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from novelctl.engine import archive_chapter, archive_volume, report_context_pack, run_check, run_sync, status
from novelctl.runtime_ops import load_runtime_dataset
from novelctl.workspace import init_workspace

from support import build_large_fixture, fill_specs, make_scene, register_character, replace_monolith_with_scenes, update_frontmatter


class NovelCtlRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_minimal_workspace_status_is_stage_pending_not_blocking(self) -> None:
        init_workspace(self.workspace)
        result = status(self.workspace, run_sync)
        self.assertEqual(result["readiness"]["current"], "bootstrap-incomplete")
        self.assertFalse(result["blocking"])
        self.assertEqual(result["gates"]["spec"]["status"], "pending")
        self.assertEqual(result["gates"]["scene"]["status"], "pending")
        self.assertTrue(result["pending_by_stage"])

    def test_check_flags_missing_work_sections_as_blocking(self) -> None:
        init_workspace(self.workspace)
        work_path = self.workspace / "WORK.md"
        text = work_path.read_text(encoding="utf-8")
        text = text.replace("## 角色索引\n\n- 暂无\n", "")
        work_path.write_text(text, encoding="utf-8")
        result = run_check(self.workspace)
        kinds = {item["kind"] for item in result["blocking"]}
        self.assertIn("missing-work-section", kinds)

    def test_check_reports_unregistered_character_as_review_required(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        (self.workspace / "角色" / "林野.md").write_text("# 林野\n\n## 简介\n\n- 关键角色。\n", encoding="utf-8")
        result = run_check(self.workspace)
        kinds = {item["kind"] for item in result["review_required"]}
        self.assertIn("unregistered-character", kinds)

    def test_context_pack_handoff_includes_state_and_next_step(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        register_character(self.workspace, "林野")
        replace_monolith_with_scenes(self.workspace, [make_scene(1, status="draft")])
        update_frontmatter(self.workspace / "WORK.md", lambda data: data.update({"current_scene": "scene-0001", "stage": "draft", "current_task_type": "draft"}))
        run_sync(self.workspace)
        pack = report_context_pack(self.workspace, "scene-0001", run_sync, profile="handoff")
        self.assertEqual(pack["profile"], "handoff")
        self.assertEqual(pack["project_state"]["stage"], "draft")
        self.assertEqual(pack["handoff"]["reentry_scene"], "scene-0001")
        self.assertTrue(pack["focus_sources"])

    def test_archive_chapter_writes_into_current_volume_tree_and_updates_work(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        ready_scenes = [make_scene(index, status="ready") for index in range(1, 4)]
        replace_monolith_with_scenes(self.workspace, ready_scenes)
        run_sync(self.workspace)
        result = archive_chapter(self.workspace, force=True)
        self.assertEqual(result["chapter_id"], "chapter-0001")
        self.assertIn("归档/卷/volume-0001/章节/chapter-0001.md", result["chapter_path"])
        draft_text = (self.workspace / "正文创作区.md").read_text(encoding="utf-8")
        self.assertNotIn("scene-0001", draft_text)
        status_payload = status(self.workspace, run_sync)
        self.assertEqual(status_payload["stage"], "bootstrap")
        self.assertEqual(status_payload["workspace_contract"]["work_frontmatter"]["current_chapter"], "chapter-0002")

    def test_archive_volume_refreshes_volume_summary(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        ready_scenes = [make_scene(index, status="ready") for index in range(1, 4)]
        replace_monolith_with_scenes(self.workspace, ready_scenes)
        run_sync(self.workspace)
        archive_chapter(self.workspace, force=True)
        result = archive_volume(self.workspace, force=True)
        self.assertEqual(result["volume_id"], "volume-0001")
        volume_text = (self.workspace / "归档" / "卷" / "volume-0001" / "卷.md").read_text(encoding="utf-8")
        self.assertIn("chapter-0001", volume_text)

    def test_large_fixture_sync_counts(self) -> None:
        init_workspace(self.workspace)
        fill_specs(self.workspace)
        build_large_fixture(self.workspace)
        run_sync(self.workspace)
        summary = status(self.workspace, run_sync)
        self.assertGreaterEqual(summary["counts"]["scenes"], 120)
        self.assertGreaterEqual(summary["counts"]["chapters"], 12)
        self.assertGreaterEqual(summary["counts"]["volumes"], 2)
        self.assertGreaterEqual(len(load_runtime_dataset(self.workspace, "plotlines")), 1)


if __name__ == "__main__":
    unittest.main()
