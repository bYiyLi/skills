from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .constants import ARCHIVE_DIR, CHAPTER_DIR, DRAFT_FILE, VOLUME_DIR
from .parser import render_scene
from .runtime_ops import ensure_fresh_runtime, load_runtime_dataset, stable_yaml
from .utils import now_iso, relative_posix, write_text_if_changed


def draft_scenes_in_order(workspace: Path) -> list[dict]:
    scenes = load_runtime_dataset(workspace, "scenes")
    return sorted([scene for scene in scenes if scene["source_kind"] == "draft"], key=lambda item: (item["source_order"], item["scene_id"]))


def archive_chapter(workspace: Path, config: dict, run_sync_callable, *, force: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable)
    draft_scenes = draft_scenes_in_order(workspace)
    ready_scenes: list[dict] = []
    for scene in draft_scenes:
        if scene["status"] == "ready":
            ready_scenes.append(scene)
        else:
            break
    if not ready_scenes:
        raise ValueError("No leading ready scenes found in 正文创作区.md.")
    min_scenes = int(config.get("workspace", {}).get("chapter_ready_scene_threshold", 3))
    min_chars = int(config.get("workspace", {}).get("chapter_ready_char_threshold", 6000))
    total_chars = sum(len(scene["body"]) for scene in ready_scenes)
    threshold_met = len(ready_scenes) >= min_scenes or total_chars >= min_chars
    if not force and not threshold_met:
        raise ValueError("Ready scenes do not meet chapter archive threshold. Use --force to override.")
    existing_chapters = load_runtime_dataset(workspace, "chapters")
    next_index = len(existing_chapters) + 1
    chapter_id = f"chapter-{next_index:04d}"
    title = f"第{next_index:04d}章 {ready_scenes[0]['title']}".strip()
    summary = " / ".join(scene["summary"] for scene in ready_scenes if scene["summary"])[:400]
    frontmatter = {"record_id": chapter_id, "record_type": "chapter", "status": "archived", "summary": summary, "tags": ["chapter"], "refs": [], "updated_at": now_iso()[:10], "chapter_id": chapter_id, "title": title, "scene_ids": [scene["scene_id"] for scene in ready_scenes]}
    chapter_text = f"---\n{stable_yaml(frontmatter)}---\n\n# {title}\n\n" + "\n".join(render_scene(scene) for scene in ready_scenes).strip() + "\n"
    chapter_path = workspace / ARCHIVE_DIR / CHAPTER_DIR / f"{chapter_id}.md"
    remaining = draft_scenes[len(ready_scenes) :]
    draft_text = "# 正文创作区\n\n" + ("\n".join(render_scene(scene) for scene in remaining).strip() + "\n" if remaining else "")
    if dry_run:
        return {"workspace": workspace.as_posix(), "dry_run": True, "chapter_id": chapter_id, "scene_ids": [scene["scene_id"] for scene in ready_scenes], "chapter_path": relative_posix(chapter_path, workspace), "threshold_met": threshold_met, "remaining_scene_ids": [scene["scene_id"] for scene in remaining]}
    write_text_if_changed(chapter_path, chapter_text)
    write_text_if_changed(workspace / DRAFT_FILE, draft_text)
    return {"workspace": workspace.as_posix(), "chapter_id": chapter_id, "scene_ids": [scene["scene_id"] for scene in ready_scenes], "chapter_path": relative_posix(chapter_path, workspace), "remaining_scene_ids": [scene["scene_id"] for scene in remaining], "sync": run_sync_callable(workspace)}


def archive_volume(workspace: Path, config: dict, run_sync_callable, *, force: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable)
    chapters = load_runtime_dataset(workspace, "chapters")
    volumes = load_runtime_dataset(workspace, "volumes")
    scenes = {scene["scene_id"]: scene for scene in load_runtime_dataset(workspace, "scenes")}
    facts = {fact["id"] for fact in load_runtime_dataset(workspace, "facts")}
    assigned = {chapter_id for volume in volumes for chapter_id in volume.get("chapter_ids", [])}
    eligible = [chapter for chapter in chapters if chapter["chapter_id"] not in assigned]
    if not eligible:
        raise ValueError("No unassigned chapters available for volume extraction.")
    min_chapters = int(config.get("workspace", {}).get("volume_ready_chapter_threshold", 10))
    min_chars = int(config.get("workspace", {}).get("volume_ready_char_threshold", 80000))
    total_chars = sum(len(scenes[scene_id]["body"]) for chapter in eligible for scene_id in chapter.get("scene_ids", []) if scene_id in scenes)
    plotline_open: dict[str, set[str]] = defaultdict(set)
    plotline_payoff: dict[str, set[str]] = defaultdict(set)
    for chapter in eligible:
        for scene_id in chapter.get("scene_ids", []):
            scene = scenes.get(scene_id)
            if not scene:
                continue
            for plotline_id in scene["plotlines"]:
                plotline_open[plotline_id].update(item if isinstance(item, str) else str(item.get("id", "")) for item in scene["open_loops"])
                plotline_payoff[plotline_id].update(scene["payoff_refs"])
    closed_plotlines = sorted(plotline_id for plotline_id, open_loops in plotline_open.items() if open_loops and open_loops.issubset(plotline_payoff[plotline_id]))
    dangling_payoffs = [scene_id for chapter in eligible for scene_id in chapter.get("scene_ids", []) if any(ref not in facts for ref in scenes.get(scene_id, {}).get("payoff_refs", []))]
    threshold_met = len(eligible) >= min_chapters or total_chars >= min_chars
    if not force and (not threshold_met or not closed_plotlines or dangling_payoffs):
        raise ValueError("Volume extraction threshold not met. Use --force to override.")
    next_index = len(volumes) + 1
    volume_id = f"volume-{next_index:04d}"
    title = f"第{next_index:04d}卷"
    chapter_ids = [chapter["chapter_id"] for chapter in eligible]
    unresolved_loops = sorted({loop for plotline_id, loops in plotline_open.items() if plotline_id not in closed_plotlines for loop in loops})
    summary = " / ".join(chapter.get("summary", "") for chapter in eligible if chapter.get("summary"))[:400]
    frontmatter = {"record_id": volume_id, "record_type": "volume", "status": "archived", "summary": summary, "tags": ["volume"], "refs": [], "updated_at": now_iso()[:10], "volume_id": volume_id, "title": title, "chapter_ids": chapter_ids, "closed_plotlines": closed_plotlines, "unresolved_loops": unresolved_loops}
    body = [f"# {title}", "", "## Chapters", "", *[f"- {chapter_id}" for chapter_id in chapter_ids], "", "## 闭合情节线", "", *([f"- {plotline_id}" for plotline_id in closed_plotlines] or ["- 暂无"])]
    volume_path = workspace / ARCHIVE_DIR / VOLUME_DIR / f"{volume_id}.md"
    if dry_run:
        return {"workspace": workspace.as_posix(), "dry_run": True, "volume_id": volume_id, "chapter_ids": chapter_ids, "closed_plotlines": closed_plotlines, "unresolved_loops": unresolved_loops, "threshold_met": threshold_met, "dangling_payoffs": dangling_payoffs, "volume_path": relative_posix(volume_path, workspace)}
    write_text_if_changed(volume_path, f"---\n{stable_yaml(frontmatter)}---\n\n" + "\n".join(body) + "\n")
    return {"workspace": workspace.as_posix(), "volume_id": volume_id, "chapter_ids": chapter_ids, "closed_plotlines": closed_plotlines, "unresolved_loops": unresolved_loops, "volume_path": relative_posix(volume_path, workspace), "sync": run_sync_callable(workspace)}
