from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from novelctl.engine import archive_chapter, report_context_pack, retrieve, run_check, run_sync, status
from novelctl.workspace import init_workspace, load_config, runtime_root


class NovelCtlRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        init_workspace(self.workspace)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _draft_path(self) -> Path:
        return self.workspace / "正文创作区.md"

    def _append_ready_scenes(self) -> None:
        draft_path = self._draft_path()
        draft_text = draft_path.read_text(encoding="utf-8").replace("status: draft", "status: ready", 1)
        draft_text += """

## scene-0002 第二场景
```yaml
scene_id: scene-0002
status: ready
pov: 林野
time: time-0002
location: 黑石城
characters:
  - 林野
plotlines:
  - plot-main-001
goal: 推进主线
outcome: 发现线索
continuity_refs:
  - scene-0001
summary: >
  第二场景摘要。
beats:
  - 第二场景 beat
new_facts:
  - id: fact-scene-0002-001
    subject: 林野
    predicate: 发现
    object: 黑石碎片
state_changes:
  - entity: 林野
    field: 认知
    from: 不知道线索
    to: 知道黑石碎片重要
foreshadow:
  - id: hook-scene-0002-001
    note: 黑石碎片后续会回收
payoff_refs: []
open_loops:
  - loop-scene-0002-001
```
正文:

这里是第二场景。

## scene-0003 第三场景
```yaml
scene_id: scene-0003
status: ready
pov: 林野
time: time-0003
location: 黑石城
characters:
  - 林野
plotlines:
  - plot-main-001
goal: 推进主线
outcome: 获得阶段成果
continuity_refs:
  - scene-0002
summary: >
  第三场景摘要。
beats:
  - 第三场景 beat
new_facts:
  - id: fact-scene-0003-001
    subject: 林野
    predicate: 获得
    object: 阶段成果
state_changes:
  - entity: 林野
    field: 目标
    from: 追查线索
    to: 准备进入下一阶段
foreshadow:
  - id: hook-scene-0003-001
    note: 下一卷伏笔
payoff_refs:
  - hook-scene-0002-001
open_loops:
  - loop-scene-0003-001
```
正文:

这里是第三场景。
"""
        draft_path.write_text(draft_text, encoding="utf-8")

    def test_sync_builds_runtime_outputs(self) -> None:
        result = run_sync(self.workspace)
        self.assertIn("counts", result)
        self.assertTrue((runtime_root(self.workspace) / "freshness.json").exists())
        self.assertTrue((runtime_root(self.workspace) / "reports" / "status.json").exists())

    def test_sync_dry_run_has_no_runtime_side_effects(self) -> None:
        dry_run_result = run_sync(self.workspace, dry_run=True)
        self.assertTrue(dry_run_result["dry_run"])
        self.assertFalse((runtime_root(self.workspace) / "freshness.json").exists())

    def test_status_auto_sync_after_source_change(self) -> None:
        run_sync(self.workspace)
        draft_path = self._draft_path()
        draft_path.write_text(draft_path.read_text(encoding="utf-8").replace("待补充", "林野", 1), encoding="utf-8")
        result = status(self.workspace, run_sync)
        self.assertIn("freshness", result)
        self.assertIn("counts", result)

    def test_archive_chapter_and_context_pack(self) -> None:
        self._append_ready_scenes()
        run_sync(self.workspace)
        check_result = run_check(self.workspace)
        self.assertFalse(check_result["errors"])
        archive_result = archive_chapter(self.workspace, force=True)
        self.assertEqual(archive_result["chapter_id"], "chapter-0001")
        pack = report_context_pack(self.workspace, "scene-0001", run_sync)
        self.assertEqual(pack["scene"]["scene_id"], "scene-0001")

    def test_runtime_rebuild_after_deletion(self) -> None:
        run_sync(self.workspace)
        shutil.rmtree(runtime_root(self.workspace))
        result = retrieve(self.workspace, "text", "开场", 5, load_config(self.workspace), run_sync)
        self.assertIn("results", result)


if __name__ == "__main__":
    unittest.main()
