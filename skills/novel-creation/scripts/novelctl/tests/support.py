from __future__ import annotations

import itertools
from pathlib import Path
import re

import yaml

from novelctl.parser import render_scene
from novelctl.workspace import current_volume_chapters_dir, current_volume_summary_path

SECTION_RE = re.compile(r"(^##\s+角色索引\s*$\n)(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)


def update_frontmatter(path: Path, updater) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} does not have frontmatter.")
    _, raw, body = text.split("---\n", 2)
    frontmatter = yaml.safe_load(raw) or {}
    updater(frontmatter)
    path.write_text(f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n{body}", encoding="utf-8")


def fill_specs(workspace: Path) -> None:
    (workspace / "设定" / "世界观.md").write_text(
        """# 世界观

## 核心命题

- 黑石资源决定城市秩序。

## 世界规则

- 月食后才能安全搬运黑石。

## 能力与限制

- 直接接触黑石会损耗近期记忆。
""",
        encoding="utf-8",
    )
    (workspace / "设定" / "主线规格.md").write_text(
        """# 主线规格

## 主目标

- 林野需要查明黑石码头失控的真正原因。

## 核心冲突

- 议会希望隐瞒事故，而林野必须找到运输名单。

## 主要情节线

- plot-main-001: 查明黑石码头失控真相。

## 阶段性闭合条件

- 掌握第一批涉事名单并确认失控源头。
""",
        encoding="utf-8",
    )
    (workspace / "设定" / "时间线.md").write_text(
        """# 时间线

## 已确定时间点

- time-0001: 夜港失控事件当夜。

## 时间规则

- 同一时间点不可让同一角色出现在两个地点。

## 未决时间问题

- 暂无
""",
        encoding="utf-8",
    )


def register_character(workspace: Path, name: str) -> None:
    path = workspace / "角色" / f"{name}.md"
    path.write_text(
        f"""# {name}

## 简介

- 关键角色卡。

## 当前状态

- 仍在调查。
""",
        encoding="utf-8",
    )
    work_path = workspace / "WORK.md"
    text = work_path.read_text(encoding="utf-8")
    replacement = f"## 角色索引\n\n- [{name}](角色/{name}.md)\n"
    text = SECTION_RE.sub(replacement, text)
    work_path.write_text(text, encoding="utf-8")


def make_scene(index: int, *, status: str = "ready", continuity_refs: list[str] | None = None, character: str = "林野") -> dict:
    scene_id = f"scene-{index:04d}"
    refs = continuity_refs if continuity_refs is not None else ([f"scene-{index - 1:04d}"] if index > 1 else [])
    open_loop_id = f"loop-{scene_id}-001"
    return {
        "scene_id": scene_id,
        "title": f"第{index:04d}场",
        "status": status,
        "pov": character,
        "time": f"time-{index:04d}",
        "location": "黑石城",
        "characters": [character],
        "plotlines": ["plot-main-001"],
        "goal": "推进主线",
        "outcome": f"完成第{index:04d}步",
        "continuity_refs": refs,
        "summary": f"{character}推进第{index:04d}步。",
        "beats": [f"beat-{index:04d}-1", f"beat-{index:04d}-2"],
        "new_facts": [
            {
                "id": f"fact-{scene_id}-001",
                "subject": "黑石码头",
                "predicate": "出现",
                "object": f"异常线索-{index:04d}",
            }
        ],
        "state_changes": [
            {
                "entity": character,
                "field": "调查进度",
                "from": f"step-{index - 1:04d}" if index > 1 else "none",
                "to": f"step-{index:04d}",
            }
        ],
        "foreshadow": [
            {
                "id": f"hook-{scene_id}-001",
                "note": f"伏笔-{index:04d}",
            }
        ],
        "payoff_refs": [f"loop-scene-{index - 1:04d}-001"] if index > 1 else [],
        "open_loops": [open_loop_id],
        "body": f"{character}在黑石城推进第{index:04d}步。",
    }


def replace_monolith_with_scenes(workspace: Path, scenes: list[dict]) -> None:
    content = "# 正文创作区\n\n"
    if scenes:
        content += "\n".join(render_scene(scene) for scene in scenes).strip() + "\n"
    else:
        content += "等待下一场。\n"
    (workspace / "正文创作区.md").write_text(content, encoding="utf-8")


def build_large_fixture(workspace: Path) -> None:
    scene_counter = itertools.count(1)
    volume_ids = ["volume-0001", "volume-0002"]
    for volume_index, volume_id in enumerate(volume_ids, start=1):
        chapter_ids: list[str] = []
        for local_index in range(1, 7):
            chapter_number = (volume_index - 1) * 6 + local_index
            chapter_id = f"chapter-{chapter_number:04d}"
            chapter_ids.append(chapter_id)
            scenes = [make_scene(next(scene_counter), status="ready") for _ in range(10)]
            frontmatter = {
                "record_id": chapter_id,
                "record_type": "chapter",
                "status": "archived",
                "summary": f"章节 {chapter_number}",
                "tags": ["chapter"],
                "refs": [],
                "updated_at": "2026-03-24",
                "chapter_id": chapter_id,
                "volume_id": volume_id,
                "title": f"第{chapter_number:04d}章",
                "scene_ids": [scene["scene_id"] for scene in scenes],
            }
            body = f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n\n# 第{chapter_number:04d}章\n\n"
            body += "\n".join(render_scene(scene) for scene in scenes).strip() + "\n"
            chapter_dir = current_volume_chapters_dir(workspace, volume_id)
            chapter_dir.mkdir(parents=True, exist_ok=True)
            (chapter_dir / f"{chapter_id}.md").write_text(body, encoding="utf-8")
        volume_frontmatter = {
            "record_id": volume_id,
            "record_type": "volume",
            "status": "archived",
            "summary": f"{volume_id} 总结",
            "tags": ["volume"],
            "refs": [],
            "updated_at": "2026-03-24",
            "volume_id": volume_id,
            "title": f"第{volume_index:04d}卷",
            "chapter_ids": chapter_ids,
        }
        body = f"---\n{yaml.safe_dump(volume_frontmatter, allow_unicode=True, sort_keys=False)}---\n\n# 第{volume_index:04d}卷\n\n## Chapters\n\n"
        body += "\n".join(f"- {chapter_id}" for chapter_id in chapter_ids) + "\n"
        volume_path = current_volume_summary_path(workspace, volume_id)
        volume_path.parent.mkdir(parents=True, exist_ok=True)
        volume_path.write_text(body, encoding="utf-8")
