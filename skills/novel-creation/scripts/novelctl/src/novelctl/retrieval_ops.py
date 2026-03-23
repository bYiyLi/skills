from __future__ import annotations

import json
from pathlib import Path

from .analysis_ops import report_conflicts_file, report_freshness_file, report_gates_file, report_summary_file, report_unresolved_file
from .errors import SceneNotFoundError, ValidationError
from .openai_compat import embed_texts, embedding_enabled, rerank_candidates, reranker_enabled, retrieval_config
from .runtime_ops import ensure_fresh_runtime, load_runtime_dataset, load_runtime_snapshot, report_path
from .utils import cosine_similarity, load_json, score_text, stable_id, write_json_if_changed
from .workspace import load_config

QUERY_REQUIRED_MODES = {"text", "scene", "chapter", "volume", "source", "work"}


def lexical_candidates(documents: list[dict], query: str) -> dict[str, dict]:
    candidates: dict[str, dict] = {}
    for doc in documents:
        matched_fields: list[str] = []
        lexical_score = 0.0
        for field in doc.get("matched_fields", []):
            value = doc["title"] if field == "title" else doc.get(field, "") if field in doc else doc.get("summary", "")
            if not isinstance(value, str):
                value = " ".join(str(item) for item in value) if isinstance(value, list) else json.dumps(value, ensure_ascii=False)
            field_score = score_text(query, value)
            if field_score > 0:
                lexical_score += field_score
                matched_fields.append(field)
        if lexical_score > 0:
            candidates[doc["id"]] = {
                "kind": doc["kind"],
                "id": doc["id"],
                "title": doc["title"],
                "source_path": doc["source_path"],
                "source_ref": doc["source_ref"],
                "matched_fields": matched_fields,
                "snippet": doc.get("summary", "")[:240] or doc.get("text", "")[:240],
                "lexical_score": lexical_score,
                "semantic_score": 0.0,
                "rerank_score": 0.0,
            }
    return candidates


def semantic_candidates(documents: list[dict], query: str, workspace: Path, config: dict, limit: int) -> dict[str, dict]:
    embedding_records = {item["id"]: item["vector"] for item in load_runtime_dataset(workspace, "embedding", kind="index")}
    if not query or not embedding_records or not embedding_enabled(config):
        return {}
    try:
        query_vector = embed_texts([query], config)[0]
    except Exception:
        return {}
    scored: list[tuple[float, dict]] = []
    for doc in documents:
        vector = embedding_records.get(doc["id"])
        if not vector:
            continue
        score = cosine_similarity(query_vector, vector)
        if score <= 0:
            continue
        payload = {
            "kind": doc["kind"],
            "id": doc["id"],
            "title": doc["title"],
            "source_path": doc["source_path"],
            "source_ref": doc["source_ref"],
            "matched_fields": ["semantic"],
            "snippet": doc.get("summary", "")[:240] or doc.get("text", "")[:240],
            "lexical_score": 0.0,
            "semantic_score": score,
            "rerank_score": 0.0,
        }
        scored.append((score, payload))
    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    return {item["id"]: item for _, item in scored[: max(limit * 3, 10)]}


def apply_rerank(query: str, records: list[dict], config: dict) -> None:
    if not records or not reranker_enabled(config):
        return
    try:
        reranked = rerank_candidates(query, [record["snippet"] for record in records], config)
    except Exception:
        return
    score_map = {item["index"]: item["score"] for item in reranked}
    for index, record in enumerate(records):
        record["rerank_score"] = score_map.get(index, 0.0)


def mode_kinds(mode: str) -> set[str]:
    mapping = {
        "text": {"scene", "chapter", "volume", "source", "work"},
        "scene": {"scene"},
        "chapter": {"chapter"},
        "volume": {"volume"},
        "source": {"source"},
        "work": {"work"},
    }
    return mapping.get(mode, set())


def retrieve(
    workspace: Path,
    mode: str,
    query: str,
    limit: int,
    config: dict,
    run_sync_callable,
    *,
    browse: bool = False,
) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name=f"retrieve {mode}")
    browse_mode = bool(browse and not query and mode in QUERY_REQUIRED_MODES)
    if mode in QUERY_REQUIRED_MODES and not query and not browse_mode:
        raise ValidationError(
            f"Query is required for retrieve {mode}.",
            hint="为该检索模式提供非空查询，或传入 `--browse` 显式进入浏览模式。",
            details={"mode": mode},
        )
    documents = load_runtime_dataset(workspace, "documents")
    if mode == "unresolved":
        unresolved = report_unresolved_file(workspace)
        items = [
            {
                "kind": "unresolved",
                "id": item["plotline_id"],
                "title": item["plotline_id"],
                "source_path": "",
                "source_ref": item["plotline_id"],
                "matched_fields": ["open_loops"],
                "snippet": ", ".join(item["open_loops"]),
                "lexical_score": 1.0,
                "semantic_score": 0.0,
                "rerank_score": 0.0,
            }
            for item in unresolved.get("plotlines", [])
            if not query or score_text(query, json.dumps(item, ensure_ascii=False)) > 0
        ]
        return {"mode": mode, "query": query, "results": items[:limit]}
    if mode == "conflict-candidates":
        report = report_conflicts_file(workspace)
        items = []
        for item in report.get("items", []):
            text = json.dumps(item, ensure_ascii=False, sort_keys=True)
            lexical = score_text(query, text) if query else 1.0
            if lexical <= 0:
                continue
            items.append(
                {
                    "kind": item["kind"],
                    "id": stable_id("candidate", text),
                    "title": item["kind"],
                    "source_path": item.get("source_path", ""),
                    "source_ref": item.get("scene_id", item["kind"]),
                    "matched_fields": ["report"],
                    "snippet": text[:240],
                    "lexical_score": lexical,
                    "semantic_score": 0.0,
                    "rerank_score": 0.0,
                }
            )
        items.sort(key=lambda record: (-record["lexical_score"], record["id"]))
        return {"mode": mode, "query": query, "results": items[:limit]}
    kinds = mode_kinds(mode)
    mode_documents = [doc for doc in documents if doc["kind"] in kinds]
    lexical = lexical_candidates(mode_documents, query) if query else {}
    semantic = semantic_candidates(mode_documents, query, workspace, config, limit) if query else {}
    merged: dict[str, dict] = {}
    for record in mode_documents if browse_mode else []:
        merged[record["id"]] = {
            "kind": record["kind"],
            "id": record["id"],
            "title": record["title"],
            "source_path": record["source_path"],
            "source_ref": record["source_ref"],
            "matched_fields": [],
            "snippet": record.get("summary", "")[:240] or record.get("text", "")[:240],
            "lexical_score": 0.0,
            "semantic_score": 0.0,
            "rerank_score": 0.0,
        }
    for source in (lexical, semantic):
        for key, record in source.items():
            merged.setdefault(key, record)
            merged[key]["lexical_score"] = max(merged[key].get("lexical_score", 0.0), record.get("lexical_score", 0.0))
            merged[key]["semantic_score"] = max(merged[key].get("semantic_score", 0.0), record.get("semantic_score", 0.0))
            merged[key]["matched_fields"] = sorted(set(merged[key].get("matched_fields", []) + record.get("matched_fields", [])))
    weight_config = retrieval_config(config)
    records = list(merged.values())
    for record in records:
        record["score"] = float(weight_config.get("lexical_weight", 1.0)) * record["lexical_score"] + float(weight_config.get("semantic_weight", 0.35)) * record["semantic_score"]
    records.sort(key=lambda item: (-item["score"], item["id"]))
    candidates = records[: max(limit * 3, 10)]
    apply_rerank(query, candidates, config)
    for record in candidates:
        record["score"] += float(weight_config.get("rerank_weight", 1.0)) * record["rerank_score"]
    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    payload = {"mode": mode, "query": query, "results": candidates[:limit]}
    if browse_mode:
        payload["browse_mode"] = True
    if not embedding_enabled(config):
        payload["semantic_mode"] = "lexical-fallback"
    return payload


def report_context_pack(workspace: Path, scene_id: str, run_sync_callable, *, profile: str | None = None) -> dict:
    workspace = workspace.resolve()
    config = load_config(workspace)
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="report context-pack")
    snapshot = load_runtime_snapshot(workspace, config)
    scene_map = {scene["scene_id"]: scene for scene in snapshot["manifests"]["scenes"]}
    scene = scene_map.get(scene_id)
    if not scene:
        raise SceneNotFoundError(
            f"Unknown scene_id: {scene_id}",
            details={"scene_id": scene_id, "available_scene_ids": sorted(scene_map)[:20]},
        )
    selected_profile = profile or "draft"
    project_state = snapshot["manifests"]["project_work"]
    source_docs = [doc for doc in snapshot["manifests"]["source_docs"] if doc.get("kind") == "source"]
    focus_names = {scene["pov"], scene["location"], *scene["characters"]}
    focus_sources = [
        doc for doc in source_docs if doc["title"] in focus_names or doc["source_path"] in set(project_state.get("setting_index", []))
    ]
    recent_related = [scene_map[ref] for ref in scene["continuity_refs"] if ref in scene_map]
    chapters = [
        chapter
        for chapter in snapshot["manifests"]["chapters"]
        if chapter.get("volume_id") == project_state.get("current_volume")
        or any(ref in chapter.get("scene_ids", []) for ref in scene["continuity_refs"])
    ]
    conflicts = report_conflicts_file(workspace).get("items", [])
    conflict_hits = [item for item in conflicts if item.get("scene_id") == scene_id or scene["scene_id"] in json.dumps(item, ensure_ascii=False)]
    unresolved = report_unresolved_file(workspace)
    ready_frontier = [
        item["scene_id"]
        for item in snapshot["manifests"]["scenes"]
        if item["source_kind"] == "draft" and item["status"] == "ready"
    ]
    pack = {
        "profile": selected_profile,
        "scene": scene,
        "project_state": {
            "stage": project_state.get("stage", "bootstrap"),
            "current_task_type": project_state.get("current_task_type", "bootstrap"),
            "current_scope": project_state.get("current_scope", ""),
            "blockers": project_state.get("blockers", []),
            "next_step": project_state.get("next_step", ""),
            "current_scene": project_state.get("current_scene", ""),
            "current_chapter": project_state.get("current_chapter", ""),
            "current_volume": project_state.get("current_volume", ""),
        },
        "continuity_refs": recent_related,
        "related_chapters": chapters,
        "focus_sources": focus_sources,
        "unresolved": unresolved,
        "conflict_candidates": conflict_hits,
        "recommended_route": "archive" if scene["status"] == "ready" else "draft",
        "next_commands": [
            f'novelctl check "{workspace.as_posix()}"',
            f'novelctl report context-pack "{workspace.as_posix()}" --scene {scene_id} --profile handoff',
        ],
    }
    if selected_profile == "draft":
        pack["draft_focus"] = {
            "characters": scene["characters"],
            "location": scene["location"],
            "goal": scene["goal"],
            "recent_related_scenes": recent_related,
        }
    elif selected_profile == "check":
        pack["check_focus"] = {
            "scene_summary": scene["summary"],
            "conflict_candidates": conflict_hits,
            "blockers": project_state.get("blockers", []),
        }
    elif selected_profile == "archive":
        pack["archive_focus"] = {
            "ready_frontier": ready_frontier,
            "current_volume": project_state.get("current_volume", ""),
            "current_chapter": project_state.get("current_chapter", ""),
        }
        pack["next_commands"].insert(0, f'novelctl archive chapter "{workspace.as_posix()}" --dry-run')
    elif selected_profile == "handoff":
        pack["handoff"] = {
            "current_stage": project_state.get("stage", "bootstrap"),
            "current_blockers": project_state.get("blockers", []),
            "next_step": project_state.get("next_step", ""),
            "reentry_scene": scene_id,
            "last_verified_command": f'novelctl check "{workspace.as_posix()}"',
        }
    write_json_if_changed(report_path(workspace, f"context-pack-{scene_id}-{selected_profile}.json"), pack)
    return pack


def report_summary(workspace: Path, run_sync_callable) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="report summary")
    return report_summary_file(workspace)


def report_conflicts(workspace: Path, run_sync_callable) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="report conflicts")
    return report_conflicts_file(workspace)


def report_gates(workspace: Path, run_sync_callable) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="report gates")
    return report_gates_file(workspace)


def report_unresolved(workspace: Path, run_sync_callable) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="report unresolved")
    return report_unresolved_file(workspace)


def report_freshness(workspace: Path, run_sync_callable) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="report freshness")
    return report_freshness_file(workspace)


def status(workspace: Path, run_sync_callable) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync_callable, command_name="status")
    return load_json(report_path(workspace, "status.json"), {})
