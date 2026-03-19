from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .constants import MAIN_PLOT_FILE, PLACEHOLDER_VALUES, SETTINGS_DIR, TIMELINE_FILE, WORLD_FILE
from .parser import find_missing_scene_fields, has_placeholder, parse_sections
from .runtime_ops import load_runtime_dataset, report_path, runtime_complete, runtime_root
from .utils import load_json, now_iso, write_json_if_changed, write_text_if_changed

REQUIRED_SPEC_SOURCE_PATHS = (
    f"{SETTINGS_DIR}/{WORLD_FILE}",
    f"{SETTINGS_DIR}/{MAIN_PLOT_FILE}",
    f"{SETTINGS_DIR}/{TIMELINE_FILE}",
)
SPEC_SECTION_REQUIREMENTS = {
    f"{SETTINGS_DIR}/{WORLD_FILE}": ("核心命题", "世界规则", "能力与限制"),
    f"{SETTINGS_DIR}/{MAIN_PLOT_FILE}": ("主目标", "核心冲突", "主要情节线", "阶段性闭合条件"),
    f"{SETTINGS_DIR}/{TIMELINE_FILE}": ("已确定时间点", "时间规则"),
}


def is_placeholderish_text(text: str) -> bool:
    value = text.strip().lower()
    if not value:
        return True
    if value in PLACEHOLDER_VALUES:
        return True
    return value.startswith(("待补充", "待定", "todo", "tbd", "pending"))


def normalize_section_lines(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        text = line.strip()
        if not text or text.startswith("```"):
            continue
        text = text.lstrip("-*0123456789. ").strip()
        if not text:
            continue
        separator = ":" if ":" in text else "：" if "：" in text else ""
        if separator:
            _, tail = text.split(separator, 1)
            candidate = tail.strip()
            normalized.append(candidate or text)
            continue
        normalized.append(text)
    return normalized


def section_has_meaningful_content(lines: list[str]) -> bool:
    normalized = normalize_section_lines(lines)
    if not normalized:
        return False
    return any(not is_placeholderish_text(item) for item in normalized)


def spec_requirements(spec_docs: list[dict]) -> dict:
    by_path = {str(doc.get("source_path", "")): doc for doc in spec_docs}
    missing = [path for path in REQUIRED_SPEC_SOURCE_PATHS if path not in by_path]
    incomplete_sections: list[dict] = []
    for path, required_sections in SPEC_SECTION_REQUIREMENTS.items():
        doc = by_path.get(path)
        if not doc:
            continue
        sections = parse_sections(str(doc.get("body", "")))
        for section_name in required_sections:
            if not section_has_meaningful_content(sections.get(section_name, [])):
                incomplete_sections.append({"source_path": path, "section": section_name})
    placeholders = sorted({item["source_path"] for item in incomplete_sections})
    return {"missing": missing, "placeholders": placeholders, "incomplete_sections": incomplete_sections}


def next_actions(analysis: dict, manifests: dict) -> list[str]:
    if analysis["errors"]:
        return ["先修复 blocking errors，再继续续写或归档。"]
    if analysis["spec_requirements"]["missing"] or analysis["spec_requirements"]["placeholders"]:
        return ["补齐 `设定/` 下缺失或仍含占位值的世界观、主线规格、时间线文档。"]
    if analysis["review_required"]:
        return ["处理场景占位值与 review_required 项，确认正文与结构化字段一致。"]
    if analysis["conflict_candidates"]:
        return ["运行 `novelctl report conflicts <workspace>` 查看冲突候选，并人工核实后再继续。"]
    ready_scenes = [scene for scene in manifests["scenes"] if scene["source_kind"] == "draft" and scene["status"] == "ready"]
    if len(ready_scenes) >= 3:
        return ["可以考虑运行 novelctl archive chapter。"]
    return ["继续推进当前场景，或使用 novelctl report context-pack 准备续写。"]


def analyze_snapshot(manifests: dict) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    review_required: list[dict] = []
    conflict_candidates: list[dict] = []
    seen_scene_ids: set[str] = set()
    seen_fact_ids: set[str] = set()
    seen_hook_ids: set[str] = set()
    seen_loop_ids: set[str] = set()
    frozen_lines = set(manifests["project_agents"].get("frozen_lines", []))
    scene_map = {scene["scene_id"]: scene for scene in manifests["scenes"]}
    for scene in manifests["scenes"]:
        missing = find_missing_scene_fields(scene)
        if missing:
            errors.append({"kind": "missing-scene-fields", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "fields": missing})
        if scene["scene_id"] in seen_scene_ids:
            errors.append({"kind": "duplicate-scene-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"]})
        seen_scene_ids.add(scene["scene_id"])
        for field in ("pov", "time", "location", "goal", "outcome", "summary"):
            if has_placeholder(scene.get(field)):
                review_required.append({"kind": "scene-placeholder", "scene_id": scene["scene_id"], "field": field, "source_path": scene["source_path"]})
        for ref in scene["continuity_refs"]:
            if ref and ref not in scene_map:
                errors.append({"kind": "missing-continuity-ref", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "missing_ref": ref})
        for hook in scene["foreshadow"]:
            hook_id = str(hook.get("id", "")).strip()
            if not hook_id:
                warnings.append({"kind": "missing-hook-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"]})
                continue
            if hook_id in seen_hook_ids:
                errors.append({"kind": "duplicate-hook-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "hook_id": hook_id})
            seen_hook_ids.add(hook_id)
        for loop in scene["open_loops"]:
            loop_id = loop if isinstance(loop, str) else str(loop.get("id", "")).strip()
            if not loop_id:
                warnings.append({"kind": "missing-loop-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"]})
                continue
            if loop_id in seen_loop_ids:
                errors.append({"kind": "duplicate-loop-id", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "loop_id": loop_id})
            seen_loop_ids.add(loop_id)
        blob = "\n".join([scene["summary"], scene["body"]])
        for frozen_line in frozen_lines:
            if frozen_line and frozen_line in blob:
                conflict_candidates.append({"kind": "frozen-setting-overlap", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "frozen_line": frozen_line})
    hook_ids = {fact["id"] for fact in manifests["facts"] if fact["kind"] == "hook"}
    loop_ids = {fact["id"] for fact in manifests["facts"] if fact["kind"] == "open-loop"}
    for fact in manifests["facts"]:
        if fact["id"] in seen_fact_ids:
            errors.append({"kind": "duplicate-fact-id", "fact_id": fact["id"], "source_path": fact["source_path"]})
        seen_fact_ids.add(fact["id"])
    for scene in manifests["scenes"]:
        for payoff_ref in scene["payoff_refs"]:
            if payoff_ref not in hook_ids and payoff_ref not in loop_ids:
                errors.append({"kind": "missing-payoff-ref", "scene_id": scene["scene_id"], "source_path": scene["source_path"], "missing_ref": payoff_ref})
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
        if plotline["status"] == "active" and plotline["open_loops"]:
            unresolved_plotlines.append({"plotline_id": plotline["plotline_id"], "open_loops": plotline["open_loops"], "scene_ids": plotline["scene_ids"]})
            conflict_candidates.append({"kind": "unresolved-plotline", "plotline_id": plotline["plotline_id"], "open_loops": plotline["open_loops"]})
    chapter_scene_ids = [scene_id for chapter in manifests["chapters"] for scene_id in chapter.get("scene_ids", [])]
    if len(set(chapter_scene_ids)) != len(chapter_scene_ids):
        errors.append({"kind": "duplicate-scene-across-chapters", "scene_ids": chapter_scene_ids})
    for chapter in manifests["chapters"]:
        actual_scene_ids = [scene["scene_id"] for scene in manifests["scenes"] if scene["source_path"] == chapter["source_path"]]
        if chapter.get("scene_ids") and actual_scene_ids and chapter["scene_ids"] != actual_scene_ids:
            errors.append({"kind": "chapter-scene-id-mismatch", "chapter_id": chapter["chapter_id"], "source_path": chapter["source_path"], "declared_scene_ids": chapter["scene_ids"], "actual_scene_ids": actual_scene_ids})
    chapter_ids = {item["chapter_id"] for item in manifests["chapters"]}
    for volume in manifests["volumes"]:
        missing_chapters = [chapter_id for chapter_id in volume.get("chapter_ids", []) if chapter_id not in chapter_ids]
        if missing_chapters:
            errors.append({"kind": "missing-volume-chapter-ref", "volume_id": volume["volume_id"], "source_path": volume["source_path"], "missing_chapter_ids": missing_chapters})
    spec_docs = [doc for doc in manifests["source_docs"] if doc.get("kind") == "spec"]
    spec_state = spec_requirements(spec_docs)
    scene_placeholders = [item for item in review_required if item["kind"] == "scene-placeholder"]
    gates = {
        "workspace": {"passed": True, "details": []},
        "spec": {
            "passed": not spec_state["missing"] and not spec_state["placeholders"],
            "details": [],
        },
        "scene": {
            "passed": not any(item["kind"] == "missing-scene-fields" for item in errors) and not scene_placeholders,
            "details": [],
        },
        "index": {"passed": True, "details": []},
        "consistency": {"passed": not errors, "details": []},
        "archive": {"passed": True, "details": []},
    }
    if not manifests["project_agents"]:
        gates["workspace"]["passed"] = False
        gates["workspace"]["details"].append("Missing AGENTS.md machine-readable state.")
    if not manifests["project_progress"]:
        gates["workspace"]["details"].append("Project status document is missing or not parsed.")
    if spec_state["missing"]:
        gates["spec"]["details"].append(f"Missing required spec docs: {', '.join(spec_state['missing'])}.")
    if spec_state["incomplete_sections"]:
        labels = [f"{item['source_path']}#{item['section']}" for item in spec_state["incomplete_sections"]]
        gates["spec"]["details"].append(f"Required spec sections still need real content: {', '.join(labels)}.")
    if scene_placeholders:
        gates["scene"]["details"].append("Scene placeholders still exist in required fields.")
    if review_required and len(review_required) != len(scene_placeholders):
        gates["scene"]["details"].append("Additional review_required items need manual confirmation.")
    if errors:
        gates["consistency"]["details"].append("Blocking consistency errors remain.")
    if warnings:
        gates["consistency"]["details"].append(f"{len(warnings)} warnings remain.")
    if review_required:
        gates["consistency"]["details"].append(f"{len(review_required)} review_required items remain.")
    if conflict_candidates:
        gates["consistency"]["details"].append(f"{len(conflict_candidates)} conflict candidates need review; run `novelctl report conflicts <workspace>` for details.")
    return {
        "generated_at": now_iso(),
        "errors": errors,
        "warnings": warnings,
        "review_required": review_required,
        "conflict_candidates": conflict_candidates,
        "spec_requirements": spec_state,
        "unresolved": {"plotlines": unresolved_plotlines, "open_loop_ids": sorted(loop_ids - {ref for scene in manifests["scenes"] for ref in scene["payoff_refs"]})},
        "gates": gates,
    }


def write_analysis_reports(workspace: Path, analysis: dict, manifests: dict, freshness: dict, semantic: dict, llamaindex_info: dict) -> dict:
    next_steps = next_actions(analysis, manifests)
    check_summary = {
        "generated_at": analysis["generated_at"],
        "stage": manifests["project_agents"].get("stage", "bootstrap"),
        "errors": analysis["errors"],
        "warnings": analysis["warnings"],
        "review_required": analysis["review_required"],
        "candidate_conflict_count": len(analysis["conflict_candidates"]),
        "conflict_candidates": analysis["conflict_candidates"],
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
        "stage": manifests["project_agents"].get("stage", "bootstrap"),
        "freshness": {"last_synced_changed_files": freshness["changed_files"], "last_synced_removed_files": freshness["removed_files"], "stale": False},
        "runtime": {"root": runtime_root(workspace).as_posix(), "complete": runtime_complete(workspace)},
        "semantic": {**semantic, "llamaindex": llamaindex_info},
        "counts": {"source_docs": len(manifests["source_docs"]), "documents": len(manifests["documents"]), "scenes": len(manifests["scenes"]), "facts": len(manifests["facts"]), "entities": len(manifests["entities"]), "chapters": len(manifests["chapters"]), "volumes": len(manifests["volumes"]), "plotlines": len(manifests["plotlines"])},
        "gates": analysis["gates"],
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
