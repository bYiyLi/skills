from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .constants import (
    DRAFT_FILE,
    READINESS_ARCHIVE_READY,
    READINESS_BOOTSTRAP_INCOMPLETE,
    READINESS_DRAFT_READY,
    REQUIRED_SETTING_FILES,
    WORK_FILE,
)
from .parser import find_missing_scene_fields, has_placeholder
from .runtime_ops import report_path, runtime_complete, runtime_root
from .utils import load_json, now_iso, write_json_if_changed, write_text_if_changed
from .workspace import inspect_workspace_contract


def _meaningful_markdown(text: str) -> bool:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith("```"):
            continue
        normalized = stripped.lstrip("-*0123456789. ").strip()
        separator = ":" if ":" in normalized else "：" if "：" in normalized else ""
        if separator:
            _, tail = normalized.split(separator, 1)
            normalized = tail.strip() or normalized
        lines.append(normalized)
    if not lines:
        return False
    return any(not has_placeholder(line) for line in lines)


def _spec_state(source_docs: list[dict], stage: str) -> dict:
    by_path = {doc["source_path"]: doc for doc in source_docs if doc.get("kind") == "source" and doc.get("source_group") == "setting"}
    missing = [path for path in REQUIRED_SETTING_FILES if path not in by_path]
    placeholders = sorted(path for path in REQUIRED_SETTING_FILES if path in by_path and not _meaningful_markdown(by_path[path].get("body", "")))
    mode = "pending" if stage == "bootstrap" else "blocking"
    return {"missing": missing, "placeholders": placeholders, "mode": mode}


def _contiguous_ready_scenes(manifests: dict) -> list[dict]:
    draft_scenes = [scene for scene in manifests["scenes"] if scene["source_kind"] == "draft"]
    ready: list[dict] = []
    for scene in sorted(draft_scenes, key=lambda item: (item["source_order"], item["scene_id"])):
        if scene["status"] == "ready":
            ready.append(scene)
        else:
            break
    return ready


def _archive_threshold_met(config: dict, ready_scenes: list[dict]) -> bool:
    min_scenes = int(config.get("workspace", {}).get("chapter_ready_scene_threshold", 3))
    min_chars = int(config.get("workspace", {}).get("chapter_ready_char_threshold", 6000))
    total_chars = sum(len(scene["body"]) for scene in ready_scenes)
    return len(ready_scenes) >= min_scenes or total_chars >= min_chars


def next_actions(analysis: dict) -> list[str]:
    if analysis["blocking"]:
        return ["先修复 blocking 项，再继续 retrieve、draft 或 archive。"]
    if analysis["pending_by_stage"]:
        return [analysis["pending_by_stage"][0]["action"]]
    if analysis["review_required"]:
        return ["先处理 review_required 项，确认 WORK 索引、正文结构和归档边界一致。"]
    if analysis["readiness"]["current"] == READINESS_ARCHIVE_READY:
        return ["可以运行 `novelctl archive chapter <workspace>`，把前部连续 ready scenes 归档进当前卷。"]
    return ["继续当前创作路径，或先运行 `novelctl report context-pack <workspace> --scene <scene_id> --profile handoff` 准备接力。"]


def analyze_snapshot(workspace: Path, manifests: dict, config: dict) -> dict:
    workspace = workspace.resolve()
    contract = inspect_workspace_contract(workspace, config)
    blocking: list[dict] = []
    warnings: list[dict] = []
    review_required: list[dict] = []
    conflict_candidates: list[dict] = []
    pending_by_stage: list[dict] = []
    scene_map = {scene["scene_id"]: scene for scene in manifests["scenes"]}
    project_work = manifests.get("project_work", {})
    stage = project_work.get("stage", "bootstrap") or "bootstrap"
    current_task_type = project_work.get("current_task_type", stage) or stage

    for path in contract["missing_required_files"]:
        if path == WORK_FILE or path == ".novel/config.yaml":
            blocking.append({"kind": "missing-required-file", "source_path": path})
            continue
        if path in REQUIRED_SETTING_FILES or path == DRAFT_FILE:
            if stage == "bootstrap":
                pending_by_stage.append(
                    {
                        "kind": "missing-required-file",
                        "stage": stage,
                        "source_path": path,
                        "action": "先补齐最小真源：世界观、主线规格、时间线和正文创作区。",
                    }
                )
            else:
                blocking.append({"kind": "missing-required-file", "source_path": path})

    for path in contract["broken_setting_links"]:
        blocking.append({"kind": "broken-setting-link", "source_path": path})
    for path in contract["broken_character_links"]:
        blocking.append({"kind": "broken-character-link", "source_path": path})
    for path in contract["setting_registry"]["invalid"]:
        blocking.append({"kind": "invalid-setting-link", "source_path": path or WORK_FILE})
    for path in contract["character_registry"]["invalid"]:
        blocking.append({"kind": "invalid-character-link", "source_path": path or WORK_FILE})
    for path in contract["setting_registry"]["out_of_scope"]:
        blocking.append({"kind": "out-of-scope-setting-link", "source_path": path})
    for path in contract["character_registry"]["out_of_scope"]:
        blocking.append({"kind": "out-of-scope-character-link", "source_path": path})
    for section in contract["missing_sections"]:
        blocking.append({"kind": "missing-work-section", "section": section, "source_path": WORK_FILE})
    for field in contract["missing_frontmatter"]:
        blocking.append({"kind": "missing-work-frontmatter", "field": field, "source_path": WORK_FILE})

    for path in contract["setting_registry"]["duplicates"]:
        review_required.append({"kind": "duplicate-setting-link", "source_path": path})
    for path in contract["character_registry"]["duplicates"]:
        review_required.append({"kind": "duplicate-character-link", "source_path": path})
    for path in contract["unregistered_settings"]:
        review_required.append({"kind": "unregistered-setting", "source_path": path})
    for path in contract["unregistered_characters"]:
        review_required.append({"kind": "unregistered-character", "source_path": path})
    for path in contract["missing_required_setting_links"]:
        review_required.append({"kind": "missing-required-setting-link", "source_path": path})

    spec_state = _spec_state(manifests["source_docs"], stage)
    if spec_state["missing"] or spec_state["placeholders"]:
        if spec_state["mode"] == "pending":
            pending_by_stage.append(
                {
                    "kind": "spec-incomplete",
                    "stage": stage,
                    "missing": spec_state["missing"],
                    "placeholders": spec_state["placeholders"],
                    "action": "继续补齐设定真源，并在 WORK.md 的设定索引里登记清楚。",
                }
            )
        else:
            blocking.append(
                {
                    "kind": "spec-incomplete",
                    "missing": spec_state["missing"],
                    "placeholders": spec_state["placeholders"],
                }
            )

    seen_scene_ids: set[str] = set()
    hook_ids: set[str] = set()
    loop_ids: set[str] = set()
    for scene in manifests["scenes"]:
        missing = find_missing_scene_fields(scene)
        if missing:
            blocking.append({"kind": "missing-scene-fields", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "fields": missing})
        if scene["scene_id"] in seen_scene_ids:
            blocking.append({"kind": "duplicate-scene-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"]})
        seen_scene_ids.add(scene["scene_id"])
        for field in ("pov", "time", "location", "goal", "outcome", "summary"):
            if has_placeholder(scene.get(field)):
                review_required.append({"kind": "scene-placeholder", "scene_id": scene["scene_id"], "field": field, "source_path": scene["source_path"]})
        for ref in scene["continuity_refs"]:
            if ref and ref not in scene_map:
                blocking.append({"kind": "missing-continuity-ref", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "missing_ref": ref})
        for hook in scene["foreshadow"]:
            hook_id = str(hook.get("id", "")).strip()
            if not hook_id:
                review_required.append({"kind": "missing-hook-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"]})
                continue
            hook_ids.add(hook_id)
        for loop in scene["open_loops"]:
            if isinstance(loop, str):
                loop_id = loop.strip()
            else:
                loop_id = str(loop.get("id", "")).strip()
            if not loop_id:
                review_required.append({"kind": "missing-loop-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"]})
                continue
            loop_ids.add(loop_id)
    for scene in manifests["scenes"]:
        for payoff_ref in scene["payoff_refs"]:
            if payoff_ref not in hook_ids and payoff_ref not in loop_ids:
                blocking.append({"kind": "missing-payoff-ref", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "missing_ref": payoff_ref})

    character_time_map: dict[tuple[str, str], set[str]] = defaultdict(set)
    for scene in manifests["scenes"]:
        for character in scene["characters"]:
            if character and scene["time"] and scene["location"]:
                character_time_map[(character, scene["time"])].add(scene["location"])
    for (character, scene_time), locations in sorted(character_time_map.items()):
        if len(locations) > 1:
            conflict_candidates.append({"kind": "character-multi-location", "character": character, "time": scene_time, "locations": sorted(locations)})

    unresolved_plotlines: list[dict] = []
    for plotline in manifests["plotlines"]:
        if plotline["open_loops"]:
            unresolved_plotlines.append({"plotline_id": plotline["plotline_id"], "open_loops": plotline["open_loops"], "scene_ids": plotline["scene_ids"]})

    chapter_scene_ids = [scene_id for chapter in manifests["chapters"] for scene_id in chapter.get("scene_ids", [])]
    if len(set(chapter_scene_ids)) != len(chapter_scene_ids):
        blocking.append({"kind": "duplicate-scene-across-chapters", "scene_ids": chapter_scene_ids})
    for chapter in manifests["chapters"]:
        actual_scene_ids = [scene["scene_id"] for scene in manifests["scenes"] if scene["source_path"] == chapter["source_path"]]
        if chapter.get("scene_ids") and actual_scene_ids and chapter["scene_ids"] != actual_scene_ids:
            blocking.append(
                {
                    "kind": "chapter-scene-id-mismatch",
                    "chapter_id": chapter["chapter_id"],
                    "source_path": chapter["source_path"],
                    "declared_scene_ids": chapter["scene_ids"],
                    "actual_scene_ids": actual_scene_ids,
                }
            )
    chapter_ids = {item["chapter_id"] for item in manifests["chapters"]}
    for volume in manifests["volumes"]:
        missing_chapters = [chapter_id for chapter_id in volume.get("chapter_ids", []) if chapter_id not in chapter_ids]
        if missing_chapters:
            blocking.append({"kind": "missing-volume-chapter-ref", "volume_id": volume["volume_id"], "source_path": volume["source_path"], "missing_chapter_ids": missing_chapters})

    ready_scenes = _contiguous_ready_scenes(manifests)
    archive_threshold_met = _archive_threshold_met(config, ready_scenes)

    gates = {
        "workspace": {"status": "passed", "passed": True, "details": []},
        "spec": {"status": "passed", "passed": True, "details": []},
        "scene": {"status": "passed", "passed": True, "details": []},
        "consistency": {"status": "passed", "passed": True, "details": []},
        "archive": {"status": "passed", "passed": True, "details": []},
    }

    if any(item["kind"].startswith("missing-work") or item["kind"].endswith("link") for item in blocking):
        gates["workspace"]["status"] = "blocking"
        gates["workspace"]["passed"] = False
    elif contract["contract_mismatches"]:
        gates["workspace"]["status"] = "review-required"
        gates["workspace"]["passed"] = False
    if contract["contract_mismatches"]:
        gates["workspace"]["details"].extend(contract["contract_mismatches"])

    if spec_state["missing"] or spec_state["placeholders"]:
        gates["spec"]["status"] = "pending" if spec_state["mode"] == "pending" else "blocking"
        gates["spec"]["passed"] = False
        if spec_state["missing"]:
            gates["spec"]["details"].append(f"Missing required setting docs: {', '.join(spec_state['missing'])}.")
        if spec_state["placeholders"]:
            gates["spec"]["details"].append(f"Setting docs still need real content: {', '.join(spec_state['placeholders'])}.")

    scene_placeholders = [item for item in review_required if item["kind"] == "scene-placeholder"]
    if scene_placeholders:
        gates["scene"]["status"] = "review-required"
        gates["scene"]["passed"] = False
        gates["scene"]["details"].append("Scene placeholders still exist in required fields.")
    if any(item["kind"] == "missing-scene-fields" for item in blocking):
        gates["scene"]["status"] = "blocking"
        gates["scene"]["passed"] = False
    if not manifests["scenes"] and stage == "bootstrap":
        gates["scene"]["status"] = "pending"
        gates["scene"]["passed"] = False
        pending_by_stage.append(
            {
                "kind": "draft-not-started",
                "stage": stage,
                "action": "先在正文创作区建立第一个 scene block，再进入 retrieve 或 draft。",
            }
        )

    if blocking:
        gates["consistency"]["status"] = "blocking"
        gates["consistency"]["passed"] = False
        gates["consistency"]["details"].append("Blocking consistency issues remain.")
    elif review_required:
        gates["consistency"]["status"] = "review-required"
        gates["consistency"]["passed"] = False
        gates["consistency"]["details"].append(f"{len(review_required)} review_required items remain.")
    elif pending_by_stage:
        gates["consistency"]["status"] = "pending"
        gates["consistency"]["passed"] = False
    if conflict_candidates:
        gates["consistency"]["details"].append(f"{len(conflict_candidates)} conflict candidates need manual review.")

    if not ready_scenes:
        gates["archive"]["status"] = "pending"
        gates["archive"]["passed"] = False
        gates["archive"]["details"].append("No leading ready scenes are currently available.")
    elif not archive_threshold_met:
        gates["archive"]["status"] = "pending"
        gates["archive"]["passed"] = False
        gates["archive"]["details"].append("Leading ready scenes exist, but the chapter archive threshold is not met yet.")
    if blocking:
        gates["archive"]["status"] = "blocking"
        gates["archive"]["passed"] = False

    if blocking:
        readiness = "blocked"
    elif ready_scenes and archive_threshold_met and not review_required and gates["spec"]["status"] == "passed":
        readiness = READINESS_ARCHIVE_READY
    elif pending_by_stage and stage == "bootstrap":
        readiness = READINESS_BOOTSTRAP_INCOMPLETE
    else:
        readiness = READINESS_DRAFT_READY

    return {
        "generated_at": now_iso(),
        "stage": stage,
        "current_task_type": current_task_type,
        "blocking": blocking,
        "warnings": warnings,
        "review_required": review_required,
        "pending_by_stage": pending_by_stage,
        "conflict_candidates": conflict_candidates,
        "spec_requirements": spec_state,
        "unresolved": {"plotlines": unresolved_plotlines, "open_loop_ids": sorted(loop_ids - {ref for scene in manifests["scenes"] for ref in scene["payoff_refs"]})},
        "gates": gates,
        "workspace_contract": contract,
        "readiness": {
            "current": readiness,
            "ready_for_archive": readiness == READINESS_ARCHIVE_READY,
            "ready_for_draft": readiness in {READINESS_DRAFT_READY, READINESS_ARCHIVE_READY},
        },
    }


def write_analysis_reports(workspace: Path, analysis: dict, manifests: dict, freshness: dict, semantic: dict, llamaindex_info: dict, config: dict) -> dict:
    next_steps = next_actions(analysis)
    check_summary = {
        "generated_at": analysis["generated_at"],
        "stage": analysis["stage"],
        "current_task_type": analysis["current_task_type"],
        "readiness": analysis["readiness"],
        "blocking": analysis["blocking"],
        "warnings": analysis["warnings"],
        "pending_by_stage": analysis["pending_by_stage"],
        "review_required": analysis["review_required"],
        "candidate_conflict_count": len(analysis["conflict_candidates"]),
        "conflict_candidates": analysis["conflict_candidates"],
        "workspace_contract": analysis["workspace_contract"],
        "next_actions": next_steps,
    }
    write_json_if_changed(report_path(workspace, "check-summary.json"), check_summary)
    write_json_if_changed(report_path(workspace, "conflict-candidates.json"), {"generated_at": analysis["generated_at"], "items": analysis["conflict_candidates"]})
    lines = ["# Conflict Candidates", ""]
    lines.extend(["- none"] if not analysis["conflict_candidates"] else [f"- `{item['kind']}`: {json.dumps(item, ensure_ascii=False, sort_keys=True)}" for item in analysis["conflict_candidates"]])
    write_text_if_changed(report_path(workspace, "conflict-candidates.md"), "\n".join(lines) + "\n")
    write_json_if_changed(report_path(workspace, "gates.json"), analysis["gates"])
    write_json_if_changed(report_path(workspace, "unresolved.json"), analysis["unresolved"])
    write_json_if_changed(report_path(workspace, "freshness.json"), freshness)
    status_payload = {
        "generated_at": analysis["generated_at"],
        "stage": analysis["stage"],
        "current_task_type": analysis["current_task_type"],
        "readiness": analysis["readiness"],
        "freshness": {
            "last_synced_changed_files": freshness["changed_files"],
            "last_synced_removed_files": freshness["removed_files"],
            "stale": False,
            "last_synced_at": freshness.get("generated_at", ""),
        },
        "runtime": {"root": runtime_root(workspace).as_posix(), "complete": runtime_complete(workspace)},
        "semantic": {**semantic, "llamaindex": llamaindex_info},
        "counts": {
            "source_docs": len(manifests["source_docs"]),
            "documents": len(manifests["documents"]),
            "scenes": len(manifests["scenes"]),
            "chapters": len(manifests["chapters"]),
            "volumes": len(manifests["volumes"]),
            "plotlines": len(manifests["plotlines"]),
        },
        "gates": analysis["gates"],
        "workspace_contract": analysis["workspace_contract"],
        "pending_by_stage": analysis["pending_by_stage"],
        "blocking": analysis["blocking"],
        "review_required": analysis["review_required"],
        "warnings": analysis["warnings"],
        "next_actions": next_steps,
    }
    write_json_if_changed(report_path(workspace, "status.json"), status_payload)
    summary = {"status": status_payload, "check": check_summary, "gates": analysis["gates"], "unresolved": analysis["unresolved"], "freshness": freshness}
    write_json_if_changed(report_path(workspace, "summary.json"), summary)
    return status_payload


def report_summary_file(workspace: Path) -> dict:
    return load_json(report_path(workspace, "summary.json"), {})


def report_conflicts_file(workspace: Path) -> dict:
    return load_json(report_path(workspace, "conflict-candidates.json"), {"items": []})


def report_gates_file(workspace: Path) -> dict:
    return load_json(report_path(workspace, "gates.json"), {})


def report_unresolved_file(workspace: Path) -> dict:
    return load_json(report_path(workspace, "unresolved.json"), {})


def report_freshness_file(workspace: Path) -> dict:
    return load_json(report_path(workspace, "freshness.json"), {})
