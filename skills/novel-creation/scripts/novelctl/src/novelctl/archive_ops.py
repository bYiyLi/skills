from __future__ import annotations

import re
from pathlib import Path

from .errors import ThresholdError
from .parser import render_scene
from .runtime_ops import ensure_fresh_runtime, load_runtime_snapshot, stable_yaml
from .utils import now_iso, write_text_if_changed
from .workspace import (
    current_volume_chapters_dir,
    current_volume_summary_path,
    draft_file_path,
    load_work_contract,
    update_work_frontmatter,
)

ID_SUFFIX_RE = re.compile(r"-(\d+)$")


def draft_scenes_in_order(workspace: Path) -> list[dict]:
    snapshot = load_runtime_snapshot(workspace)
    return sorted(
        [scene for scene in snapshot["manifests"]["scenes"] if scene["source_kind"] == "draft"],
        key=lambda item: (item["source_order"], item["scene_id"]),
    )


def _render_draft_document(scenes: list[dict]) -> str:
    prefix = "# 正文创作区\n\n"
    if not scenes:
        return prefix + "等待下一场。\n"
    return prefix + "\n".join(render_scene(scene) for scene in scenes).strip() + "\n"


def _next_id(prefix: str, values: list[str]) -> str:
    highest = 0
    for value in values:
        match = ID_SUFFIX_RE.search(value)
        if not match:
            continue
        highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:04d}"


def archive_chapter(workspace: Path, config: dict, run_sync_callable, *, force: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="archive chapter")
    snapshot = load_runtime_snapshot(workspace, config)
    draft_scenes = sorted(
        [scene for scene in snapshot["manifests"]["scenes"] if scene["source_kind"] == "draft"],
        key=lambda item: (item["source_order"], item["scene_id"]),
    )
    ready_scenes: list[dict] = []
    for scene in draft_scenes:
        if scene["status"] == "ready":
            ready_scenes.append(scene)
        else:
            break
    if not ready_scenes:
        raise ThresholdError("No leading ready scenes found in 正文创作区.md.")
    min_scenes = int(config.get("workspace", {}).get("chapter_ready_scene_threshold", 3))
    min_chars = int(config.get("workspace", {}).get("chapter_ready_char_threshold", 6000))
    total_chars = sum(len(scene["body"]) for scene in ready_scenes)
    threshold_met = len(ready_scenes) >= min_scenes or total_chars >= min_chars
    if not force and not threshold_met:
        raise ThresholdError("Ready scenes do not meet chapter archive threshold. Use --force to override.")

    project_work = snapshot["manifests"]["project_work"]
    current_volume = project_work.get("current_volume", "") or "volume-0001"
    existing_chapter_ids = [chapter["chapter_id"] for chapter in snapshot["manifests"]["chapters"]]
    chapter_id = _next_id("chapter", existing_chapter_ids)
    title = f"第{int(chapter_id.split('-')[-1]):04d}章 {ready_scenes[0]['title']}".strip()
    summary = " / ".join(scene["summary"] for scene in ready_scenes if scene["summary"])[:400]
    frontmatter = {
        "record_id": chapter_id,
        "record_type": "chapter",
        "status": "archived",
        "summary": summary,
        "tags": ["chapter"],
        "refs": [],
        "updated_at": now_iso()[:10],
        "chapter_id": chapter_id,
        "volume_id": current_volume,
        "title": title,
        "scene_ids": [scene["scene_id"] for scene in ready_scenes],
    }
    chapter_text = f"---\n{stable_yaml(frontmatter)}---\n\n# {title}\n\n" + "\n".join(render_scene(scene) for scene in ready_scenes).strip() + "\n"
    chapter_path = current_volume_chapters_dir(workspace, current_volume) / f"{chapter_id}.md"
    remaining = draft_scenes[len(ready_scenes) :]
    next_chapter_id = _next_id("chapter", [*existing_chapter_ids, chapter_id])
    if dry_run:
        return {
            "workspace": workspace.as_posix(),
            "dry_run": True,
            "volume_id": current_volume,
            "chapter_id": chapter_id,
            "scene_ids": [scene["scene_id"] for scene in ready_scenes],
            "chapter_path": chapter_path.relative_to(workspace).as_posix(),
            "threshold_met": threshold_met,
            "remaining_scene_ids": [scene["scene_id"] for scene in remaining],
            "next_chapter_id": next_chapter_id,
        }

    write_text_if_changed(chapter_path, chapter_text)
    write_text_if_changed(draft_file_path(workspace), _render_draft_document(remaining))
    update_work_frontmatter(
        workspace,
        current_scene=remaining[0]["scene_id"] if remaining else "",
        current_chapter=next_chapter_id,
        current_volume=current_volume,
        next_step=(f"继续在 {draft_file_path(workspace).name} 中推进 {next_chapter_id}。" if remaining else "当前章已归档，可继续写下一章或刷新本卷总结。"),
    )
    return {
        "workspace": workspace.as_posix(),
        "volume_id": current_volume,
        "chapter_id": chapter_id,
        "scene_ids": [scene["scene_id"] for scene in ready_scenes],
        "chapter_path": chapter_path.relative_to(workspace).as_posix(),
        "remaining_scene_ids": [scene["scene_id"] for scene in remaining],
        "sync": run_sync_callable(workspace),
    }


def archive_volume(workspace: Path, config: dict, run_sync_callable, *, force: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="archive volume")
    snapshot = load_runtime_snapshot(workspace, config)
    project_work = snapshot["manifests"]["project_work"]
    current_volume = project_work.get("current_volume", "") or "volume-0001"
    chapters = [chapter for chapter in snapshot["manifests"]["chapters"] if chapter.get("volume_id") == current_volume]
    if not chapters:
        raise ThresholdError("Current volume has no archived chapters yet.")

    min_chapters = int(config.get("workspace", {}).get("volume_ready_chapter_threshold", 3))
    min_chars = int(config.get("workspace", {}).get("volume_ready_char_threshold", 20000))
    scene_map = {scene["scene_id"]: scene for scene in snapshot["manifests"]["scenes"]}
    total_chars = sum(len(scene_map[scene_id]["body"]) for chapter in chapters for scene_id in chapter.get("scene_ids", []) if scene_id in scene_map)
    if not force and not (len(chapters) >= min_chapters or total_chars >= min_chars):
        raise ThresholdError("Current volume does not meet volume archive threshold. Use --force to override.")

    related_plotlines = {}
    for scene in snapshot["manifests"]["scenes"]:
        if scene["source_kind"] != "chapter":
            continue
        if scene["source_path"] not in {chapter["source_path"] for chapter in chapters}:
            continue
        for plotline_id in scene["plotlines"]:
            related_plotlines.setdefault(plotline_id, {"scene_ids": [], "open_loops": set(), "payoff_refs": set()})
            related_plotlines[plotline_id]["scene_ids"].append(scene["scene_id"])
            for loop in scene["open_loops"]:
                if isinstance(loop, str):
                    loop_id = loop.strip()
                else:
                    loop_id = str(loop.get("id", "")).strip()
                if loop_id:
                    related_plotlines[plotline_id]["open_loops"].add(loop_id)
            for ref in scene["payoff_refs"]:
                if ref:
                    related_plotlines[plotline_id]["payoff_refs"].add(ref)

    unresolved = {
        plotline_id: sorted(data["open_loops"] - data["payoff_refs"])
        for plotline_id, data in related_plotlines.items()
    }
    frontmatter = {
        "record_id": current_volume,
        "record_type": "volume",
        "status": "archived",
        "summary": " / ".join(chapter.get("summary", "") for chapter in chapters if chapter.get("summary"))[:400],
        "tags": ["volume"],
        "refs": [],
        "updated_at": now_iso()[:10],
        "volume_id": current_volume,
        "title": f"第{int(current_volume.split('-')[-1]):04d}卷",
        "chapter_ids": [chapter["chapter_id"] for chapter in chapters],
    }
    lines = [
        f"# {frontmatter['title']}",
        "",
        "## Chapters",
        "",
        *[f"- {chapter['chapter_id']}" for chapter in chapters],
        "",
        "## Plotlines",
        "",
        *([f"- {plotline_id}" for plotline_id in sorted(related_plotlines)] or ["- 暂无"]),
        "",
        "## Unresolved",
        "",
        *([f"- {plotline_id}: {', '.join(items) if items else '已闭合'}" for plotline_id, items in sorted(unresolved.items())] or ["- 暂无"]),
    ]
    volume_path = current_volume_summary_path(workspace, current_volume)
    if dry_run:
        return {
            "workspace": workspace.as_posix(),
            "dry_run": True,
            "volume_id": current_volume,
            "chapter_ids": [chapter["chapter_id"] for chapter in chapters],
            "volume_path": volume_path.relative_to(workspace).as_posix(),
        }

    write_text_if_changed(volume_path, f"---\n{stable_yaml(frontmatter)}---\n\n" + "\n".join(lines) + "\n")
    update_work_frontmatter(workspace, current_volume=current_volume, next_step="本卷总结已刷新，可继续当前卷后续章节，或手动切到下一卷。")
    return {
        "workspace": workspace.as_posix(),
        "volume_id": current_volume,
        "chapter_ids": [chapter["chapter_id"] for chapter in chapters],
        "volume_path": volume_path.relative_to(workspace).as_posix(),
        "sync": run_sync_callable(workspace),
    }
