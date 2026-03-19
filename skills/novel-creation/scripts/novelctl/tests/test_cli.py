from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from novelctl.cli import main
from novelctl.engine import run_sync
from novelctl.workspace import init_workspace


class NovelCtlCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        init_workspace(self.workspace)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run_cli(self, *argv: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                exit_code = main(list(argv))
            except SystemExit as exc:  # argparse --help / parse errors
                exit_code = int(exc.code)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _stdout_json(self, *argv: str) -> tuple[int, dict]:
        exit_code, stdout, stderr = self._run_cli(*argv)
        self.assertEqual(stderr.strip(), "")
        self.assertTrue(stdout.strip())
        return exit_code, json.loads(stdout)

    def _stderr_json(self, *argv: str) -> tuple[int, dict]:
        exit_code, stdout, stderr = self._run_cli(*argv)
        self.assertEqual(stdout.strip(), "")
        self.assertTrue(stderr.strip())
        return exit_code, json.loads(stderr)

    def _update_config(self, updater) -> None:
        config_path = self.workspace / ".novel" / "config.yaml"
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        updater(data)
        config_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def _touch_draft(self) -> None:
        draft_path = self.workspace / "正文创作区.md"
        draft_text = draft_path.read_text(encoding="utf-8")
        draft_path.write_text(draft_text.replace("待补充", "林野", 1), encoding="utf-8")

    def _fill_required_specs(self) -> None:
        (self.workspace / "设定" / "世界观.md").write_text(
            """---
record_id: spec-world
record_type: spec
status: active
summary: 故事世界观与底层规则
tags:
  - spec
  - world
refs: []
updated_at: 2026-03-19
---

# 世界观

## 核心命题

- 人与黑石遗迹的关系决定城市权力结构。

## 世界规则

- rule-world-001: 黑石只能在月食后被安全搬运。

## 能力与限制

- constraint-001: 使用黑石的人会逐步失去近期记忆。

## 冻结项

- 暂无
""",
            encoding="utf-8",
        )
        (self.workspace / "设定" / "主线规格.md").write_text(
            """---
record_id: spec-main-plot
record_type: spec
status: active
summary: 主线目标、核心冲突与闭合条件
tags:
  - spec
  - plot
refs: []
updated_at: 2026-03-19
---

# 主线规格

## 主目标

- 林野需要查明黑石港失控的真正原因。

## 核心冲突

- 城邦议会希望封锁真相，而林野必须公开证据。

## 主要情节线

- plot-main-001: 查明黑石失控源头并阻止下一次月食事故。

## 阶段性闭合条件

- 第一阶段以确认失控来源和掌握运输名单为闭合条件。
""",
            encoding="utf-8",
        )

    def test_status_marks_seed_workspace_as_not_ready(self) -> None:
        exit_code, payload = self._stdout_json("status", self.workspace.as_posix())
        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["gates"]["spec"]["passed"])
        self.assertFalse(payload["gates"]["scene"]["passed"])
        self.assertIn("设定/世界观.md#核心命题", payload["gates"]["spec"]["details"][0])

    def test_spec_gate_passes_after_required_sections_are_filled(self) -> None:
        self._fill_required_specs()
        exit_code, payload = self._stdout_json("status", self.workspace.as_posix())
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["gates"]["spec"]["passed"])
        self.assertFalse(payload["gates"]["scene"]["passed"])

    def test_check_strict_blocks_on_review_required(self) -> None:
        exit_code, payload = self._stdout_json("check", self.workspace.as_posix(), "--strict")
        self.assertEqual(exit_code, 1)
        self.assertTrue(payload["review_required"])
        self.assertIn("next_actions", payload)

    def test_context_pack_unknown_scene_returns_structured_error(self) -> None:
        exit_code, payload = self._stderr_json(
            "report",
            "context-pack",
            self.workspace.as_posix(),
            "--scene",
            "does-not-exist",
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["error"]["code"], "SceneNotFoundError")
        self.assertEqual(payload["error"]["details"]["scene_id"], "does-not-exist")

    def test_retrieve_text_requires_query_or_browse(self) -> None:
        exit_code, payload = self._stderr_json("retrieve", "text", self.workspace.as_posix())
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["error"]["code"], "ValidationError")
        self.assertIn("--browse", payload["error"]["hint"])

    def test_retrieve_browse_marks_browse_mode_and_uses_config_default_limit(self) -> None:
        self._update_config(lambda data: data.setdefault("retrieval", {}).__setitem__("default_limit", 1))
        exit_code, payload = self._stdout_json("retrieve", "text", self.workspace.as_posix(), "--browse")
        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["browse_mode"])
        self.assertEqual(len(payload["results"]), 1)

    def test_retrieve_unresolved_allows_empty_query(self) -> None:
        exit_code, payload = self._stdout_json("retrieve", "unresolved", self.workspace.as_posix())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["mode"], "unresolved")
        self.assertIn("results", payload)

    def test_auto_sync_off_surfaces_stale_status_and_freshness(self) -> None:
        run_sync(self.workspace)
        self._update_config(lambda data: data.setdefault("freshness", {}).__setitem__("auto_sync_on_read", False))
        self._touch_draft()
        status_code, status_payload = self._stdout_json("status", self.workspace.as_posix())
        self.assertEqual(status_code, 0)
        self.assertTrue(status_payload["freshness"]["stale"])
        self.assertFalse(status_payload["freshness"]["auto_sync_on_read"])
        freshness_code, freshness_payload = self._stdout_json("report", "freshness", self.workspace.as_posix())
        self.assertEqual(freshness_code, 0)
        self.assertTrue(freshness_payload["stale"])
        self.assertIn("next_actions", freshness_payload)

    def test_auto_sync_off_blocks_retrieve_check_context_and_archive(self) -> None:
        run_sync(self.workspace)
        self._update_config(lambda data: data.setdefault("freshness", {}).__setitem__("auto_sync_on_read", False))
        self._touch_draft()
        for argv in [
            ("retrieve", "text", self.workspace.as_posix(), "林野"),
            ("check", self.workspace.as_posix()),
            ("report", "context-pack", self.workspace.as_posix(), "--scene", "scene-0001"),
            ("archive", "chapter", self.workspace.as_posix()),
        ]:
            exit_code, payload = self._stderr_json(*argv)
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["error"]["code"], "StaleRuntimeError")

    def test_auto_sync_on_read_true_keeps_status_fresh(self) -> None:
        run_sync(self.workspace)
        self._touch_draft()
        exit_code, payload = self._stdout_json("status", self.workspace.as_posix())
        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["freshness"]["stale"])

    def test_help_text_is_descriptive(self) -> None:
        exit_code, stdout, stderr = self._run_cli("retrieve", "text", "--help")
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.strip(), "")
        self.assertIn("--browse", stdout)
        self.assertIn("Query string", stdout)

        exit_code, stdout, _ = self._run_cli("report", "context-pack", "--help")
        self.assertEqual(exit_code, 0)
        self.assertIn("--scene", stdout)
        self.assertIn("context pack", stdout.lower())

        exit_code, stdout, _ = self._run_cli("archive", "chapter", "--help")
        self.assertEqual(exit_code, 0)
        self.assertIn("leading ready scenes", stdout.lower())


if __name__ == "__main__":
    unittest.main()
