from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import yaml

from .llamaindex_adapter import persist_llamaindex_bundle
from .openai_compat import embed_texts, embedding_enabled, embedding_signature, reranker_enabled, reranker_signature
from .parser import (
    detect_source_kind,
    parse_chapter_file,
    parse_draft_file,
    parse_source_markdown,
    parse_volume_file,
    parse_work_file,
)
from .utils import (
    delete_matching_records,
    load_json,
    md5_file,
    md5_text,
    now_iso,
    read_jsonl_directory,
    stable_dumps,
    tokenize,
    write_json_if_changed,
    write_sharded_jsonl,
)
from .workspace import (
    embedding_cache_root,
    ensure_runtime_layout,
    load_config,
    runtime_freshness_path,
    runtime_index_root,
    runtime_llamaindex_root,
    runtime_manifest_root,
    runtime_report_root,
    runtime_root,
    source_file_paths,
)


def stable_yaml(data: dict) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def config_md5(config: dict) -> str:
    return md5_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=True))


def manifest_path(workspace: Path, dataset: str) -> Path:
    return runtime_manifest_root(workspace) / dataset


def index_path(workspace: Path, dataset: str) -> Path:
    return runtime_index_root(workspace) / dataset


def report_path(workspace: Path, name: str) -> Path:
    return runtime_report_root(workspace) / name


def load_runtime_dataset(workspace: Path, dataset: str, *, kind: str = "manifest") -> list[dict]:
    base = manifest_path(workspace, dataset) if kind == "manifest" else index_path(workspace, dataset)
    return read_jsonl_directory(base)


def runtime_complete(workspace: Path) -> bool:
    if not runtime_root(workspace).exists():
        return False
    for dataset in ("source-docs", "documents", "scenes", "chapters", "volumes", "plotlines"):
        if not manifest_path(workspace, dataset).exists():
            return False
    return runtime_freshness_path(workspace).exists()


def source_inventory(workspace: Path, config: dict) -> dict[str, dict]:
    inventory: dict[str, dict] = {}
    for path in source_file_paths(workspace, config):
        rel_path = path.relative_to(workspace).as_posix()
        inventory[rel_path] = {
            "source_path": rel_path,
            "source_kind": detect_source_kind(path, workspace),
            "source_file_md5": md5_file(path),
        }
    return inventory


def inventory_diff(previous: dict, current: dict) -> tuple[list[str], list[str], list[str]]:
    previous_files = previous.get("files", {}) if isinstance(previous, dict) else {}
    changed: list[str] = []
    unchanged: list[str] = []
    removed = sorted(set(previous_files) - set(current))
    for rel_path, item in sorted(current.items()):
        if previous_files.get(rel_path, {}).get("source_file_md5") == item["source_file_md5"]:
            unchanged.append(rel_path)
        else:
            changed.append(rel_path)
    return changed, unchanged, removed


def parse_source_file(path: Path, workspace: Path) -> dict[str, list[dict]]:
    source_kind = detect_source_kind(path, workspace)
    result = {"source_docs": [], "scenes": [], "chapters": [], "volumes": []}
    if source_kind == "setting":
        result["source_docs"].append(parse_source_markdown(path, workspace, "setting"))
    elif source_kind == "character":
        result["source_docs"].append(parse_source_markdown(path, workspace, "character"))
    elif source_kind == "project-work":
        result["source_docs"].append(parse_work_file(path, workspace))
    elif source_kind == "draft":
        result["scenes"].extend(parse_draft_file(path, workspace))
    elif source_kind == "chapter":
        chapter, scenes = parse_chapter_file(path, workspace)
        result["chapters"].append(chapter)
        result["scenes"].extend(scenes)
    elif source_kind == "volume":
        result["volumes"].append(parse_volume_file(path, workspace))
    return result


def sort_records(records: list[dict], key_fields: tuple[str, ...]) -> list[dict]:
    return sorted(records, key=lambda item: tuple(str(item.get(field, "")) for field in key_fields))


def raw_snapshot_from_runtime(workspace: Path) -> dict:
    return {
        "source_docs": load_runtime_dataset(workspace, "source-docs"),
        "scenes": load_runtime_dataset(workspace, "scenes"),
        "chapters": load_runtime_dataset(workspace, "chapters"),
        "volumes": load_runtime_dataset(workspace, "volumes"),
    }


def with_generated_at(record: dict, generated_at: str) -> dict:
    output = dict(record)
    output["generated_at"] = generated_at
    return output


def _document_from_source(doc: dict, generated_at: str) -> dict:
    matched = ["title", "summary", "body"]
    if doc["kind"] == "work":
        text = "\n".join(
            [
                doc["title"],
                doc.get("summary", ""),
                doc.get("stage", ""),
                doc.get("current_task_type", ""),
                doc.get("current_scope", ""),
                " ".join(doc.get("blockers", [])),
                doc.get("next_step", ""),
                doc.get("body", ""),
            ]
        ).strip()
        matched.extend(["stage", "current_task_type", "current_scope", "blockers", "next_step"])
        kind = "work"
    else:
        text = "\n".join([doc["title"], doc.get("summary", ""), doc.get("body", "")]).strip()
        kind = "source"
    payload = {
        "id": doc["record_id"],
        "kind": kind,
        "title": doc["title"],
        "summary": doc.get("summary", ""),
        "text": text,
        "matched_fields": matched,
        "source_path": doc["source_path"],
        "source_ref": doc["record_id"],
        "source_file_md5": doc["source_file_md5"],
    }
    if kind == "source":
        payload["source_group"] = doc.get("source_group", "")
    return with_generated_at(payload, generated_at)


def _document_from_scene(scene: dict, generated_at: str) -> dict:
    return with_generated_at(
        {
            "id": scene["scene_id"],
            "kind": "scene",
            "title": scene["title"],
            "summary": scene["summary"],
            "text": "\n".join(
                [
                    scene["title"],
                    scene["summary"],
                    scene["pov"],
                    scene["time"],
                    scene["location"],
                    " ".join(scene["characters"]),
                    " ".join(scene["plotlines"]),
                    " ".join(scene["beats"]),
                    scene["goal"],
                    scene["outcome"],
                    scene["body"],
                ]
            ).strip(),
            "matched_fields": ["title", "summary", "pov", "time", "location", "characters", "plotlines", "beats", "goal", "outcome", "body"],
            "source_path": scene["source_path"],
            "source_ref": scene["scene_id"],
            "source_file_md5": scene["source_file_md5"],
        },
        generated_at,
    )


def _document_from_archive(record: dict, generated_at: str, kind: str) -> dict:
    return with_generated_at(
        {
            "id": record[f"{kind}_id"],
            "kind": kind,
            "title": record["title"],
            "summary": record.get("summary", ""),
            "text": "\n".join([record["title"], record.get("summary", ""), record.get("body", "")]).strip(),
            "matched_fields": ["title", "summary", "body"],
            "source_path": record["source_path"],
            "source_ref": record[f"{kind}_id"],
            "source_file_md5": record["source_file_md5"],
        },
        generated_at,
    )


def _normalize_loop_id(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(value.get("id") or value.get("summary") or "").strip()
    return ""


def build_manifests(raw: dict, inventory: dict[str, dict], generated_at: str, config: dict) -> dict:
    source_docs = sort_records(raw["source_docs"], ("source_path", "record_id"))
    scenes = sort_records(raw["scenes"], ("source_path", "source_order", "scene_id"))
    chapters = sort_records(raw["chapters"], ("chapter_id",))
    volumes = sort_records(raw["volumes"], ("volume_id",))

    project_work = next((item for item in source_docs if item.get("kind") == "work"), {})
    documents: list[dict] = []
    plotline_map: dict[str, dict] = {}

    for doc in source_docs:
        documents.append(_document_from_source(doc, generated_at))

    for scene in scenes:
        documents.append(_document_from_scene(scene, generated_at))
        for plotline_id in scene["plotlines"]:
            if not plotline_id:
                continue
            plotline = plotline_map.setdefault(
                plotline_id,
                with_generated_at(
                    {
                        "plotline_id": plotline_id,
                        "title": plotline_id,
                        "scene_ids": [],
                        "open_loops": [],
                        "payoff_refs": [],
                        "status": "active",
                    },
                    generated_at,
                ),
            )
            plotline["scene_ids"].append(scene["scene_id"])
            plotline["open_loops"].extend(loop for loop in (_normalize_loop_id(item) for item in scene["open_loops"]) if loop)
            plotline["payoff_refs"].extend(ref for ref in scene["payoff_refs"] if ref)

    for plotline in plotline_map.values():
        open_ids = sorted(set(plotline["open_loops"]))
        payoff_ids = sorted(set(plotline["payoff_refs"]))
        unresolved = sorted(loop_id for loop_id in open_ids if loop_id not in set(payoff_ids))
        plotline["open_loops"] = unresolved
        plotline["payoff_refs"] = payoff_ids
        plotline["status"] = "resolved" if plotline["scene_ids"] and not unresolved else "active"

    for chapter in chapters:
        documents.append(_document_from_archive(chapter, generated_at, "chapter"))
    for volume in volumes:
        documents.append(_document_from_archive(volume, generated_at, "volume"))

    return {
        "source_docs": source_docs,
        "documents": sort_records(documents, ("kind", "id")),
        "scenes": scenes,
        "plotlines": sort_records(list(plotline_map.values()), ("plotline_id",)),
        "chapters": chapters,
        "volumes": volumes,
        "project_work": project_work,
        "registered_sources": {
            "settings": list(project_work.get("setting_index", [])) if project_work else [],
            "characters": list(project_work.get("character_index", [])) if project_work else [],
        },
        "inventory": inventory,
    }


def build_indexes(manifests: dict, generated_at: str) -> dict:
    inverted: dict[str, dict] = {}
    for doc in manifests["documents"]:
        for token in set(tokenize(doc["text"])):
            entry = inverted.setdefault(token, {"token": token, "refs": [], "generated_at": generated_at})
            entry["refs"].append(
                {
                    "kind": doc["kind"],
                    "id": doc["id"],
                    "title": doc["title"],
                    "source_path": doc["source_path"],
                    "source_ref": doc["source_ref"],
                }
            )
    return {
        "inverted": sort_records(list(inverted.values()), ("token",)),
    }


def embedding_cache_path(workspace: Path, key: str) -> Path:
    return embedding_cache_root(workspace) / key[:2] / f"{key}.json"


def embedding_cache_key(record: dict, config: dict) -> str:
    payload = {
        "source_file_md5": record.get("source_file_md5", ""),
        "source_ref": record.get("source_ref", record.get("id", "")),
        "provider": "openai-compatible",
        "base_url": str(config.get("embedding", {}).get("base_url", "")),
        "model": str(config.get("embedding", {}).get("model", "")),
        "dimensions": str(config.get("embedding", {}).get("dimensions", "")),
    }
    return md5_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def load_embedding_cache(cache_path: Path) -> list[float] | None:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data.get("vector", []) if isinstance(data.get("vector"), list) else None


def build_embedding_records(workspace: Path, documents: list[dict], config: dict) -> tuple[list[dict], dict]:
    if not embedding_enabled(config):
        return [], {"enabled": False, "count": 0, "cache_hits": 0, "cache_misses": 0}
    cache_hits = 0
    cache_misses = 0
    pending_docs: list[dict] = []
    pending_keys: list[str] = []
    vectors: dict[str, list[float]] = {}
    for doc in documents:
        cache_key = embedding_cache_key(doc, config)
        vector = load_embedding_cache(embedding_cache_path(workspace, cache_key))
        if vector is not None:
            cache_hits += 1
            vectors[doc["id"]] = vector
        else:
            cache_misses += 1
            pending_docs.append(doc)
            pending_keys.append(cache_key)
    if pending_docs:
        new_vectors = embed_texts([doc["text"] for doc in pending_docs], config)
        for doc, cache_key, vector in zip(pending_docs, pending_keys, new_vectors):
            cache_path = embedding_cache_path(workspace, cache_key)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                stable_dumps(
                    {
                        "cache_key": cache_key,
                        "source_path": doc["source_path"],
                        "source_ref": doc["source_ref"],
                        "source_file_md5": doc["source_file_md5"],
                        "embedding_signature": embedding_signature(config),
                        "vector": vector,
                    }
                ),
                encoding="utf-8",
            )
            vectors[doc["id"]] = vector
    records = sort_records(
        [
            {
                "id": doc["id"],
                "kind": doc["kind"],
                "source_path": doc["source_path"],
                "source_ref": doc["source_ref"],
                "source_file_md5": doc["source_file_md5"],
                "vector": vectors.get(doc["id"], []),
                "generated_at": now_iso(),
            }
            for doc in documents
            if vectors.get(doc["id"])
        ],
        ("kind", "id"),
    )
    return records, {
        "enabled": True,
        "count": len(records),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "signature": embedding_signature(config),
    }


def semantic_status(config: dict, embedding_records: list[dict]) -> dict:
    return {
        "embedding_enabled": embedding_enabled(config),
        "embedding_records": len(embedding_records),
        "embedding_signature": embedding_signature(config) if embedding_enabled(config) else "",
        "reranker_enabled": reranker_enabled(config),
        "reranker_signature": reranker_signature(config) if reranker_enabled(config) else "",
    }


def build_runtime_state(workspace: Path, config: dict, inventory: dict[str, dict], changed_files: list[str], removed_files: list[str]) -> dict:
    generated_at = now_iso()
    state = {
        "generated_at": generated_at,
        "workspace": workspace.as_posix(),
        "config_md5": config_md5(config),
        "embedding_signature": embedding_signature(config) if embedding_enabled(config) else "",
        "reranker_signature": reranker_signature(config) if reranker_enabled(config) else "",
        "changed_files": changed_files,
        "removed_files": removed_files,
        "files": {
            rel_path: {**info, "last_synced_at": generated_at}
            for rel_path, info in sorted(inventory.items())
        },
    }
    write_json_if_changed(runtime_freshness_path(workspace), state)
    return state


def write_runtime_files(
    workspace: Path,
    raw: dict,
    manifests: dict,
    indexes: dict,
    analysis: dict,
    freshness: dict,
    embedding_records: list[dict],
    embedding_info: dict,
    llamaindex_info: dict,
) -> dict:
    manifest_outputs = {
        "source-docs": write_sharded_jsonl(manifest_path(workspace, "source-docs"), raw["source_docs"], "record_id"),
        "documents": write_sharded_jsonl(manifest_path(workspace, "documents"), manifests["documents"], "id"),
        "scenes": write_sharded_jsonl(manifest_path(workspace, "scenes"), manifests["scenes"], "scene_id"),
        "plotlines": write_sharded_jsonl(manifest_path(workspace, "plotlines"), manifests["plotlines"], "plotline_id"),
        "chapters": write_sharded_jsonl(manifest_path(workspace, "chapters"), raw["chapters"], "chapter_id"),
        "volumes": write_sharded_jsonl(manifest_path(workspace, "volumes"), raw["volumes"], "volume_id"),
    }
    index_outputs = {
        "inverted": write_sharded_jsonl(index_path(workspace, "inverted"), indexes["inverted"], "token"),
        "embedding": write_sharded_jsonl(index_path(workspace, "embedding"), embedding_records, "id"),
    }
    return {"manifest_outputs": manifest_outputs, "index_outputs": index_outputs}


def load_runtime_snapshot(workspace: Path, config: dict | None = None) -> dict:
    raw = raw_snapshot_from_runtime(workspace)
    effective_config = config or load_config(workspace)
    inventory = source_inventory(workspace, effective_config)
    manifests = build_manifests(raw, inventory, now_iso(), effective_config)
    indexes = {
        "inverted": load_runtime_dataset(workspace, "inverted", kind="index"),
        "embedding": load_runtime_dataset(workspace, "embedding", kind="index"),
    }
    return {"raw": raw, "inventory": inventory, "manifests": manifests, "indexes": indexes}


def inspect_runtime(workspace: Path) -> dict:
    workspace = workspace.resolve()
    config = load_config(workspace)
    current_inventory = source_inventory(workspace, config)
    previous_state = load_json(runtime_freshness_path(workspace), {"files": {}})
    changed_files, unchanged_files, removed_files = inventory_diff(previous_state, current_inventory)
    runtime_is_complete = runtime_complete(workspace)
    config_changed = previous_state.get("config_md5") != config_md5(config)
    return {
        "generated_at": now_iso(),
        "workspace": workspace.as_posix(),
        "changed_files": changed_files,
        "removed_files": removed_files,
        "unchanged_files": unchanged_files,
        "runtime_complete": runtime_is_complete,
        "config_changed": config_changed,
        "full_rebuild_required": (not runtime_is_complete) or config_changed,
        "stale": (not runtime_is_complete) or config_changed or bool(changed_files) or bool(removed_files),
        "last_synced_at": str(previous_state.get("generated_at", "")),
        "config": config,
    }


def ensure_fresh_runtime(
    workspace: Path,
    run_sync_callable,
    *,
    command_name: str = "read",
    allow_stale: bool = False,
    force_full: bool = False,
) -> dict:
    inspection = inspect_runtime(workspace)
    if force_full or inspection["stale"]:
        run_sync_callable(workspace, full=force_full or inspection["full_rebuild_required"], dry_run=False)
        return inspect_runtime(workspace)
    return inspection


def run_sync_core(workspace: Path, *, force_full: bool = False) -> tuple[dict, dict, dict, dict, list[dict], dict, dict, dict]:
    workspace = workspace.resolve()
    config = load_config(workspace)
    ensure_runtime_layout(workspace)
    previous_state = load_json(runtime_freshness_path(workspace), {"files": {}})
    current_inventory = source_inventory(workspace, config)
    changed_files, unchanged_files, removed_files = inventory_diff(previous_state, current_inventory)
    effective_full = force_full or not runtime_complete(workspace) or previous_state.get("config_md5") != config_md5(config)
    raw = {"source_docs": [], "scenes": [], "chapters": [], "volumes": []} if effective_full else raw_snapshot_from_runtime(workspace)
    affected_paths = set(changed_files) | set(removed_files)
    if affected_paths:
        raw["source_docs"] = delete_matching_records(raw["source_docs"], affected_paths)
        raw["scenes"] = delete_matching_records(raw["scenes"], affected_paths)
        raw["chapters"] = delete_matching_records(raw["chapters"], affected_paths)
        raw["volumes"] = delete_matching_records(raw["volumes"], affected_paths)
    for rel_path in changed_files if not effective_full else sorted(current_inventory):
        parsed = parse_source_file(workspace / rel_path, workspace)
        raw["source_docs"].extend(parsed["source_docs"])
        raw["scenes"].extend(parsed["scenes"])
        raw["chapters"].extend(parsed["chapters"])
        raw["volumes"].extend(parsed["volumes"])
    raw["source_docs"] = sort_records(raw["source_docs"], ("source_path", "record_id"))
    raw["scenes"] = sort_records(raw["scenes"], ("source_path", "source_order", "scene_id"))
    raw["chapters"] = sort_records(raw["chapters"], ("chapter_id",))
    raw["volumes"] = sort_records(raw["volumes"], ("volume_id",))
    generated_at = now_iso()
    manifests = build_manifests(raw, current_inventory, generated_at, config)
    indexes = build_indexes(manifests, generated_at)
    embedding_records, embedding_info = build_embedding_records(workspace, manifests["documents"], config)
    llamaindex_info = persist_llamaindex_bundle(runtime_llamaindex_root(workspace), manifests["documents"], bool(embedding_records))
    freshness = build_runtime_state(
        workspace,
        config,
        current_inventory,
        changed_files if not effective_full else sorted(current_inventory),
        removed_files,
    )
    meta = {
        "workspace": workspace.as_posix(),
        "generated_at": generated_at,
        "full_rebuild": effective_full,
        "changed_files": changed_files if not effective_full else sorted(current_inventory),
        "removed_files": removed_files,
        "unchanged_files": unchanged_files,
        "config": config,
    }
    return raw, manifests, indexes, freshness, embedding_records, embedding_info, llamaindex_info, meta
