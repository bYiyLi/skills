from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import yaml

from .constants import RUNTIME_INDEX_DATASETS, RUNTIME_MANIFEST_DATASETS, TEXT_SEARCH_KINDS
from .errors import StaleRuntimeError
from .llamaindex_adapter import persist_llamaindex_bundle
from .openai_compat import embed_texts, embedding_enabled, embedding_signature, reranker_enabled, reranker_signature
from .parser import detect_source_kind, parse_chapter_file, parse_draft_file, parse_markdown_title, parse_progress, parse_project_agents, parse_setting_file, parse_volume_file, split_frontmatter
from .utils import delete_matching_records, load_json, md5_file, md5_text, now_iso, read_jsonl_directory, relative_posix, stable_dumps, stable_id, tokenize, write_json_if_changed, write_sharded_jsonl
from .workspace import embedding_cache_root, ensure_runtime_layout, load_config, runtime_freshness_path, runtime_index_root, runtime_llamaindex_root, runtime_manifest_root, runtime_report_root, runtime_root, source_file_paths


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
    for dataset in ("source-docs", "documents", "scenes", "chapters", "volumes"):
        if not manifest_path(workspace, dataset).exists():
            return False
    return runtime_freshness_path(workspace).exists()


def auto_sync_on_read(config: dict) -> bool:
    freshness = config.get("freshness", {})
    if not isinstance(freshness, dict):
        return True
    return bool(freshness.get("auto_sync_on_read", True))


def source_inventory(workspace: Path) -> dict[str, dict]:
    inventory: dict[str, dict] = {}
    for path in source_file_paths(workspace):
        rel_path = relative_posix(path, workspace)
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


def generic_doc_from_markdown(path: Path, workspace: Path, default_kind: str) -> dict:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    title = parse_markdown_title(body, path.stem)
    rel_path = relative_posix(path, workspace)
    record_id = str(frontmatter.get("record_id") or stable_id("doc", rel_path))
    return {
        "id": record_id,
        "record_id": record_id,
        "record_type": str(frontmatter.get("record_type", default_kind)),
        "kind": default_kind,
        "title": title,
        "summary": str(frontmatter.get("summary", "")).strip(),
        "status": str(frontmatter.get("status", "active")),
        "tags": [str(item).strip() for item in frontmatter.get("tags", []) if str(item).strip()] if isinstance(frontmatter.get("tags"), list) else [],
        "refs": [str(item).strip() for item in frontmatter.get("refs", []) if str(item).strip()] if isinstance(frontmatter.get("refs"), list) else [],
        "body": body.strip(),
        "source_path": rel_path,
        "source_file_md5": md5_file(path),
    }


def parse_source_file(path: Path, workspace: Path) -> dict[str, list[dict]]:
    source_kind = detect_source_kind(path, workspace)
    result = {"source-docs": [], "scenes": [], "chapters": [], "volumes": []}
    if source_kind == "setting":
        result["source-docs"].append(parse_setting_file(path, workspace))
        return result
    if source_kind == "project-agents":
        result["source-docs"].append(parse_project_agents(path, workspace))
        return result
    if source_kind == "project-progress":
        result["source-docs"].append(parse_progress(path, workspace))
        return result
    if source_kind == "draft":
        result["scenes"].extend(parse_draft_file(path, workspace))
        return result
    if source_kind == "chapter":
        chapter, scenes = parse_chapter_file(path, workspace)
        result["chapters"].append(chapter)
        result["scenes"].extend(scenes)
        return result
    if source_kind == "volume":
        result["volumes"].append(parse_volume_file(path, workspace))
        return result
    result["source-docs"].append(generic_doc_from_markdown(path, workspace, source_kind))
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


def build_documents_from_specs(spec_docs: list[dict], generated_at: str) -> list[dict]:
    documents: list[dict] = []
    for doc in spec_docs:
        documents.append(
            with_generated_at(
                {
                    "id": doc["record_id"],
                    "kind": doc["kind"],
                    "title": doc["title"],
                    "summary": doc.get("summary", ""),
                    "text": "\n".join([doc["title"], doc.get("summary", ""), doc.get("body", "")]).strip(),
                    "matched_fields": ["title", "summary", "body"],
                    "source_path": doc["source_path"],
                    "source_ref": doc["record_id"],
                    "source_file_md5": doc["source_file_md5"],
                },
                generated_at,
            )
        )
    return documents


def build_manifests(raw: dict, inventory: dict[str, dict], generated_at: str) -> dict:
    source_docs = sort_records(raw["source_docs"], ("source_path", "record_id"))
    scenes = sort_records(raw["scenes"], ("source_path", "source_order", "scene_id"))
    chapters = sort_records(raw["chapters"], ("chapter_id",))
    volumes = sort_records(raw["volumes"], ("volume_id",))
    entities_by_name: dict[str, dict] = {}
    facts: list[dict] = []
    timelines: list[dict] = []
    plotline_map: dict[str, dict] = {}
    relations_map: dict[tuple[str, str, str], dict] = {}
    documents: list[dict] = []
    state_records: list[dict] = []
    project_agents = next((item for item in source_docs if item.get("record_type") == "project-agents"), None)
    project_progress = next((item for item in source_docs if item.get("record_type") == "project-progress"), None)
    spec_docs = [item for item in source_docs if item.get("kind") == "spec"]
    entity_docs = [item for item in source_docs if item.get("kind") == "entity"]
    for entity in entity_docs:
        entities_by_name[entity["title"]] = with_generated_at({"id": entity["entity_id"], "entity_id": entity["entity_id"], "name": entity["title"], "entity_kind": entity.get("entity_kind", "实体"), "summary": entity.get("summary", ""), "aliases": entity.get("aliases", []), "current_state": entity.get("current_state", ""), "mention_scene_ids": [], "source_path": entity["source_path"], "source_file_md5": entity["source_file_md5"], "source_record_id": entity["record_id"], "frozen": bool(entity.get("frozen", False))}, generated_at)
        documents.append(with_generated_at({"id": entity["entity_id"], "kind": "entity", "title": entity["title"], "summary": entity.get("summary", ""), "text": "\n".join([entity["title"], entity.get("summary", ""), entity.get("entity_kind", ""), entity.get("current_state", ""), entity.get("body", "")]).strip(), "matched_fields": ["title", "summary", "current_state", "body"], "source_path": entity["source_path"], "source_ref": entity["entity_id"], "source_file_md5": entity["source_file_md5"]}, generated_at))
    documents.extend(build_documents_from_specs(spec_docs, generated_at))
    hook_ids: set[str] = set()
    loop_ids: set[str] = set()
    scene_ids = {scene["scene_id"] for scene in scenes}
    for scene in scenes:
        documents.append(with_generated_at({"id": scene["scene_id"], "kind": "scene", "title": scene["title"], "summary": scene["summary"], "text": "\n".join([scene["title"], scene["summary"], " ".join(scene["beats"]), scene["goal"], scene["outcome"], scene["body"]]).strip(), "matched_fields": ["title", "summary", "beats", "goal", "outcome", "body"], "source_path": scene["source_path"], "source_ref": scene["scene_id"], "source_file_md5": scene["source_file_md5"]}, generated_at))
        for name in [scene["pov"], scene["location"], *scene["characters"]]:
            if not name:
                continue
            kind = "角色" if name != scene["location"] else "地点"
            entities_by_name.setdefault(name, with_generated_at({"id": stable_id("entity", name), "entity_id": stable_id("entity", name), "name": name, "entity_kind": kind, "summary": "", "aliases": [], "current_state": "", "mention_scene_ids": [], "source_path": scene["source_path"], "source_file_md5": scene["source_file_md5"], "source_record_id": scene["scene_id"], "frozen": False}, generated_at))["mention_scene_ids"].append(scene["scene_id"])
        timeline_record = with_generated_at({"id": stable_id("timeline", f"{scene['time']}::{scene['scene_id']}"), "kind": "timeline", "time": scene["time"], "scene_id": scene["scene_id"], "title": scene["time"] or scene["scene_id"], "summary": scene["summary"], "location": scene["location"], "characters": scene["characters"], "plotlines": scene["plotlines"], "source_path": scene["source_path"], "source_file_md5": scene["source_file_md5"], "source_record_id": scene["scene_id"]}, generated_at)
        timelines.append(timeline_record)
        documents.append(with_generated_at({"id": timeline_record["id"], "kind": "timeline", "title": timeline_record["title"], "summary": timeline_record["summary"], "text": "\n".join([timeline_record["title"], timeline_record["summary"], timeline_record["location"], " ".join(timeline_record["characters"]), " ".join(timeline_record["plotlines"])]).strip(), "matched_fields": ["time", "summary", "location", "characters", "plotlines"], "source_path": scene["source_path"], "source_ref": scene["scene_id"], "source_file_md5": scene["source_file_md5"]}, generated_at))
        for hook in scene["foreshadow"]:
            hook_id = str(hook.get("id") or stable_id("hook", f"{scene['scene_id']}:{json.dumps(hook, ensure_ascii=False, sort_keys=True)}"))
            hook_ids.add(hook_id)
            label = hook.get("note", hook_id)
            record = with_generated_at({"id": hook_id, "kind": "hook", "scene_id": scene["scene_id"], "title": label, "summary": label, "source_path": scene["source_path"], "source_file_md5": scene["source_file_md5"], "source_record_id": scene["scene_id"]}, generated_at)
            facts.append(record)
            documents.append(with_generated_at({"id": hook_id, "kind": "fact", "title": label, "summary": label, "text": label, "matched_fields": ["summary"], "source_path": scene["source_path"], "source_ref": scene["scene_id"], "source_file_md5": scene["source_file_md5"]}, generated_at))
        for loop in scene["open_loops"]:
            loop_id = loop if isinstance(loop, str) else str(loop.get("id") or stable_id("loop", f"{scene['scene_id']}:{json.dumps(loop, ensure_ascii=False, sort_keys=True)}"))
            loop_ids.add(loop_id)
            label = loop if isinstance(loop, str) else str(loop.get("summary", loop_id))
            record = with_generated_at({"id": loop_id, "kind": "open-loop", "scene_id": scene["scene_id"], "title": label, "summary": label, "source_path": scene["source_path"], "source_file_md5": scene["source_file_md5"], "source_record_id": scene["scene_id"]}, generated_at)
            facts.append(record)
            documents.append(with_generated_at({"id": loop_id, "kind": "fact", "title": label, "summary": label, "text": label, "matched_fields": ["summary"], "source_path": scene["source_path"], "source_ref": scene["scene_id"], "source_file_md5": scene["source_file_md5"]}, generated_at))
        for fact in scene["new_facts"]:
            fact_id = str(fact.get("id") or stable_id("fact", f"{scene['scene_id']}:{json.dumps(fact, ensure_ascii=False, sort_keys=True)}"))
            record = with_generated_at({"id": fact_id, "kind": "fact", "scene_id": scene["scene_id"], "title": str(fact.get("subject", fact_id)), "summary": json.dumps(fact, ensure_ascii=False, sort_keys=True), "subject": str(fact.get("subject", "")), "predicate": str(fact.get("predicate", "")), "object": str(fact.get("object", "")), "rule_refs": [str(item).strip() for item in fact.get("rule_refs", []) if str(item).strip()], "source_path": scene["source_path"], "source_file_md5": scene["source_file_md5"], "source_record_id": scene["scene_id"]}, generated_at)
            facts.append(record)
            documents.append(with_generated_at({"id": fact_id, "kind": "fact", "title": record["title"], "summary": record["summary"], "text": " ".join([record["subject"], record["predicate"], record["object"]]).strip(), "matched_fields": ["subject", "predicate", "object"], "source_path": scene["source_path"], "source_ref": scene["scene_id"], "source_file_md5": scene["source_file_md5"]}, generated_at))
            if record["subject"] and record["object"]:
                edge_key = (record["subject"], record["predicate"] or "related-to", record["object"])
                edge = relations_map.setdefault(edge_key, with_generated_at({"id": stable_id("relation", "::".join(edge_key)), "kind": "relation", "source": edge_key[0], "relation": edge_key[1], "target": edge_key[2], "scene_ids": [], "source_paths": [], "source_file_md5s": []}, generated_at))
                edge["scene_ids"].append(scene["scene_id"])
                edge["source_paths"].append(scene["source_path"])
                edge["source_file_md5s"].append(scene["source_file_md5"])
        for change in scene["state_changes"]:
            state_id = str(change.get("id") or stable_id("state", f"{scene['scene_id']}:{json.dumps(change, ensure_ascii=False, sort_keys=True)}"))
            record = with_generated_at({"id": state_id, "kind": "state-change", "scene_id": scene["scene_id"], "title": str(change.get("entity", state_id)), "summary": json.dumps(change, ensure_ascii=False, sort_keys=True), "entity": str(change.get("entity", "")), "field": str(change.get("field", "")), "from": str(change.get("from", "")), "to": str(change.get("to", "")), "source_path": scene["source_path"], "source_file_md5": scene["source_file_md5"], "source_record_id": scene["scene_id"]}, generated_at)
            facts.append(record)
            state_records.append(record)
            documents.append(with_generated_at({"id": state_id, "kind": "fact", "title": record["title"], "summary": record["summary"], "text": " ".join([record["entity"], record["field"], record["from"], record["to"]]).strip(), "matched_fields": ["entity", "field", "from", "to"], "source_path": scene["source_path"], "source_ref": scene["scene_id"], "source_file_md5": scene["source_file_md5"]}, generated_at))
        for plotline_id in scene["plotlines"]:
            plot = plotline_map.setdefault(plotline_id, with_generated_at({"id": plotline_id, "plotline_id": plotline_id, "scene_ids": [], "open_loops": [], "payoff_refs": [], "latest_outcome": "", "source_paths": []}, generated_at))
            plot["scene_ids"].append(scene["scene_id"])
            plot["open_loops"].extend([item if isinstance(item, str) else str(item.get("id", "")) for item in scene["open_loops"]])
            plot["payoff_refs"].extend(scene["payoff_refs"])
            plot["latest_outcome"] = scene["outcome"]
            plot["source_paths"].append(scene["source_path"])
        for character in scene["characters"]:
            if scene["location"]:
                edge_key = (character, "appears-in", scene["location"])
                edge = relations_map.setdefault(edge_key, with_generated_at({"id": stable_id("relation", "::".join(edge_key)), "kind": "relation", "source": edge_key[0], "relation": edge_key[1], "target": edge_key[2], "scene_ids": [], "source_paths": [], "source_file_md5s": []}, generated_at))
                edge["scene_ids"].append(scene["scene_id"])
                edge["source_paths"].append(scene["source_path"])
                edge["source_file_md5s"].append(scene["source_file_md5"])
    chapter_records = [with_generated_at(item, generated_at) for item in chapters]
    for chapter in chapter_records:
        documents.append(with_generated_at({"id": chapter["chapter_id"], "kind": "chapter", "title": chapter["title"], "summary": chapter.get("summary", ""), "text": "\n".join([chapter["title"], chapter.get("summary", "")]).strip(), "matched_fields": ["title", "summary"], "source_path": chapter["source_path"], "source_ref": chapter["chapter_id"], "source_file_md5": chapter["source_file_md5"]}, generated_at))
    volume_records = [with_generated_at(item, generated_at) for item in volumes]
    for volume in volume_records:
        documents.append(with_generated_at({"id": volume["volume_id"], "kind": "volume", "title": volume["title"], "summary": volume.get("summary", ""), "text": "\n".join([volume["title"], volume.get("summary", ""), volume.get("body", "")]).strip(), "matched_fields": ["title", "summary", "body"], "source_path": volume["source_path"], "source_ref": volume["volume_id"], "source_file_md5": volume["source_file_md5"]}, generated_at))
    plotlines: list[dict] = []
    for plotline_id, plot in sorted(plotline_map.items()):
        unresolved = sorted({item for item in plot["open_loops"] if item and item not in plot["payoff_refs"]})
        record = with_generated_at({"id": plotline_id, "plotline_id": plotline_id, "scene_ids": sorted(set(plot["scene_ids"])), "open_loops": unresolved, "payoff_refs": sorted(set(ref for ref in plot["payoff_refs"] if ref)), "latest_outcome": plot["latest_outcome"], "status": "closed" if plot["payoff_refs"] and not unresolved else "active", "source_paths": sorted(set(plot["source_paths"]))}, generated_at)
        plotlines.append(record)
        documents.append(with_generated_at({"id": plotline_id, "kind": "plotline", "title": plotline_id, "summary": record["latest_outcome"], "text": "\n".join([plotline_id, record["latest_outcome"], " ".join(record["open_loops"])]).strip(), "matched_fields": ["plotline_id", "latest_outcome", "open_loops"], "source_path": record["source_paths"][0] if record["source_paths"] else "", "source_ref": plotline_id, "source_file_md5": ""}, generated_at))
    relation_records = sort_records(list(relations_map.values()), ("id",))
    for relation in relation_records:
        documents.append(with_generated_at({"id": relation["id"], "kind": "relation", "title": f"{relation['source']} {relation['relation']} {relation['target']}", "summary": ",".join(sorted(set(relation["scene_ids"]))), "text": f"{relation['source']} {relation['relation']} {relation['target']}", "matched_fields": ["source", "relation", "target"], "source_path": relation["source_paths"][0] if relation["source_paths"] else "", "source_ref": relation["id"], "source_file_md5": relation["source_file_md5s"][0] if relation["source_file_md5s"] else ""}, generated_at))
    entities = sort_records(list(entities_by_name.values()), ("name",))
    progress_records = [with_generated_at({"id": "project-stage", "kind": "progress", "stage": project_agents.get("stage", "bootstrap") if project_agents else "bootstrap", "active_plotlines": project_agents.get("active_plotlines", []) if project_agents else [], "frozen_lines": project_agents.get("frozen_lines", []) if project_agents else [], "current_scene": project_progress.get("current_scene", "") if project_progress else "", "current_chapter": project_progress.get("current_chapter", "") if project_progress else "", "current_volume": project_progress.get("current_volume", "") if project_progress else "", "source_path": project_progress["source_path"] if project_progress else (project_agents["source_path"] if project_agents else ""), "source_file_md5": project_progress["source_file_md5"] if project_progress else (project_agents["source_file_md5"] if project_agents else ""), "source_record_id": project_progress["record_id"] if project_progress else (project_agents["record_id"] if project_agents else "project-stage")}, generated_at)]
    for rel_path, info in sorted(inventory.items()):
        progress_records.append(with_generated_at({"id": stable_id("source-file", rel_path), "kind": "source-file", "source_path": rel_path, "source_kind": info["source_kind"], "source_file_md5": info["source_file_md5"], "source_record_id": rel_path}, generated_at))
    return {"source_docs": source_docs, "documents": sort_records(documents, ("kind", "id")), "scenes": sort_records([with_generated_at(item, generated_at) for item in scenes], ("source_path", "source_order", "scene_id")), "facts": sort_records(facts, ("kind", "id")), "entities": entities, "timelines": sort_records(timelines, ("time", "scene_id", "id")), "plotlines": plotlines, "chapters": chapter_records, "volumes": volume_records, "progress": progress_records, "relations": relation_records, "state_records": sort_records(state_records, ("id",)), "project_agents": project_agents or {}, "project_progress": project_progress or {}, "hook_ids": sorted(hook_ids), "loop_ids": sorted(loop_ids), "scene_ids": sorted(scene_ids)}


def build_indexes(manifests: dict, generated_at: str) -> dict:
    inverted: dict[str, dict] = {}
    for doc in manifests["documents"]:
        for token in set(tokenize(doc["text"])):
            entry = inverted.setdefault(token, {"token": token, "refs": [], "generated_at": generated_at})
            entry["refs"].append({"kind": doc["kind"], "id": doc["id"], "title": doc["title"], "source_path": doc["source_path"], "source_ref": doc["source_ref"]})
    return {"inverted": sort_records(list(inverted.values()), ("token",)), "entity-map": manifests["entities"], "timeline": manifests["timelines"], "plotline": manifests["plotlines"], "relation": manifests["relations"], "state": manifests["state_records"]}


def embedding_cache_path(workspace: Path, key: str) -> Path:
    return embedding_cache_root(workspace) / key[:2] / f"{key}.json"


def embedding_cache_key(record: dict, config: dict) -> str:
    payload = {"source_file_md5": record.get("source_file_md5", ""), "source_ref": record.get("source_ref", record.get("id", "")), "provider": "openai-compatible", "base_url": str(config.get("embedding", {}).get("base_url", "")), "model": str(config.get("embedding", {}).get("model", "")), "dimensions": str(config.get("embedding", {}).get("dimensions", ""))}
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
            cache_path.write_text(stable_dumps({"cache_key": cache_key, "source_path": doc["source_path"], "source_ref": doc["source_ref"], "source_file_md5": doc["source_file_md5"], "embedding_signature": embedding_signature(config), "vector": vector}), encoding="utf-8")
            vectors[doc["id"]] = vector
    records = sort_records([{"id": doc["id"], "kind": doc["kind"], "source_path": doc["source_path"], "source_ref": doc["source_ref"], "source_file_md5": doc["source_file_md5"], "vector": vectors.get(doc["id"], []), "generated_at": now_iso()} for doc in documents if vectors.get(doc["id"])], ("kind", "id"))
    return records, {"enabled": True, "count": len(records), "cache_hits": cache_hits, "cache_misses": cache_misses, "signature": embedding_signature(config)}


def semantic_status(config: dict, embedding_records: list[dict]) -> dict:
    return {"embedding_enabled": embedding_enabled(config), "embedding_records": len(embedding_records), "embedding_signature": embedding_signature(config) if embedding_enabled(config) else "", "reranker_enabled": reranker_enabled(config), "reranker_signature": reranker_signature(config) if reranker_enabled(config) else ""}


def build_runtime_state(workspace: Path, config: dict, inventory: dict[str, dict], changed_files: list[str], removed_files: list[str]) -> dict:
    state = {"generated_at": now_iso(), "workspace": workspace.as_posix(), "config_md5": config_md5(config), "embedding_signature": embedding_signature(config) if embedding_enabled(config) else "", "reranker_signature": reranker_signature(config) if reranker_enabled(config) else "", "changed_files": changed_files, "removed_files": removed_files, "files": {rel_path: {**info, "last_synced_at": now_iso()} for rel_path, info in sorted(inventory.items())}}
    write_json_if_changed(runtime_freshness_path(workspace), state)
    return state


def write_runtime_files(workspace: Path, raw: dict, manifests: dict, indexes: dict, analysis: dict, freshness: dict, embedding_records: list[dict], embedding_info: dict, llamaindex_info: dict) -> dict:
    manifest_outputs = {"source-docs": write_sharded_jsonl(manifest_path(workspace, "source-docs"), raw["source_docs"], "record_id"), "documents": write_sharded_jsonl(manifest_path(workspace, "documents"), manifests["documents"], "id"), "scenes": write_sharded_jsonl(manifest_path(workspace, "scenes"), manifests["scenes"], "scene_id"), "facts": write_sharded_jsonl(manifest_path(workspace, "facts"), manifests["facts"], "id"), "entities": write_sharded_jsonl(manifest_path(workspace, "entities"), manifests["entities"], "id"), "timelines": write_sharded_jsonl(manifest_path(workspace, "timelines"), manifests["timelines"], "id"), "plotlines": write_sharded_jsonl(manifest_path(workspace, "plotlines"), manifests["plotlines"], "id"), "chapters": write_sharded_jsonl(manifest_path(workspace, "chapters"), raw["chapters"], "chapter_id"), "volumes": write_sharded_jsonl(manifest_path(workspace, "volumes"), raw["volumes"], "volume_id"), "progress": write_sharded_jsonl(manifest_path(workspace, "progress"), manifests["progress"], "id")}
    index_outputs = {"inverted": write_sharded_jsonl(index_path(workspace, "inverted"), indexes["inverted"], "token"), "entity-map": write_sharded_jsonl(index_path(workspace, "entity-map"), indexes["entity-map"], "id"), "timeline": write_sharded_jsonl(index_path(workspace, "timeline"), indexes["timeline"], "id"), "plotline": write_sharded_jsonl(index_path(workspace, "plotline"), indexes["plotline"], "id"), "relation": write_sharded_jsonl(index_path(workspace, "relation"), indexes["relation"], "id"), "state": write_sharded_jsonl(index_path(workspace, "state"), indexes["state"], "id"), "embedding": write_sharded_jsonl(index_path(workspace, "embedding"), embedding_records, "id")}
    return {"manifest_outputs": manifest_outputs, "index_outputs": index_outputs}


def load_runtime_snapshot(workspace: Path) -> dict:
    raw = raw_snapshot_from_runtime(workspace)
    inventory = source_inventory(workspace)
    manifests = build_manifests(raw, inventory, now_iso())
    indexes = {"inverted": load_runtime_dataset(workspace, "inverted", kind="index"), "entity-map": load_runtime_dataset(workspace, "entity-map", kind="index"), "timeline": load_runtime_dataset(workspace, "timeline", kind="index"), "plotline": load_runtime_dataset(workspace, "plotline", kind="index"), "relation": load_runtime_dataset(workspace, "relation", kind="index"), "state": load_runtime_dataset(workspace, "state", kind="index"), "embedding": load_runtime_dataset(workspace, "embedding", kind="index")}
    return {"raw": raw, "inventory": inventory, "manifests": manifests, "indexes": indexes}


def inspect_runtime(workspace: Path) -> dict:
    workspace = workspace.resolve()
    config = load_config(workspace)
    current_inventory = source_inventory(workspace)
    previous_state = load_json(runtime_freshness_path(workspace), {"files": {}})
    changed_files, unchanged_files, removed_files = inventory_diff(previous_state, current_inventory)
    runtime_is_complete = runtime_complete(workspace)
    config_changed = previous_state.get("config_md5") != config_md5(config)
    llamaindex_missing = not runtime_llamaindex_root(workspace).exists()
    return {
        "generated_at": now_iso(),
        "workspace": workspace.as_posix(),
        "changed_files": changed_files,
        "removed_files": removed_files,
        "unchanged_files": unchanged_files,
        "runtime_complete": runtime_is_complete,
        "config_changed": config_changed,
        "llamaindex_missing": llamaindex_missing,
        "auto_sync_on_read": auto_sync_on_read(config),
        "full_rebuild_required": (not runtime_is_complete) or config_changed,
        "stale": (not runtime_is_complete) or config_changed or bool(changed_files) or bool(removed_files) or llamaindex_missing,
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
        if inspection["auto_sync_on_read"]:
            run_sync_callable(workspace, full=force_full or inspection["full_rebuild_required"], dry_run=False)
            return inspect_runtime(workspace)
        if not allow_stale:
            raise StaleRuntimeError(
                workspace=inspection["workspace"],
                command_name=command_name,
                changed_files=inspection["changed_files"],
                removed_files=inspection["removed_files"],
                config_changed=inspection["config_changed"],
                runtime_complete=inspection["runtime_complete"],
                llamaindex_missing=inspection["llamaindex_missing"],
            )
    return inspection


def run_sync_core(workspace: Path, *, force_full: bool = False) -> tuple[dict, dict, dict, dict, list[dict], dict, dict, dict]:
    workspace = workspace.resolve()
    ensure_runtime_layout(workspace)
    config = load_config(workspace)
    previous_state = load_json(runtime_freshness_path(workspace), {"files": {}})
    current_inventory = source_inventory(workspace)
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
        raw["source_docs"].extend(parsed["source-docs"])
        raw["scenes"].extend(parsed["scenes"])
        raw["chapters"].extend(parsed["chapters"])
        raw["volumes"].extend(parsed["volumes"])
    raw["source_docs"] = sort_records(raw["source_docs"], ("source_path", "record_id"))
    raw["scenes"] = sort_records(raw["scenes"], ("source_path", "source_order", "scene_id"))
    raw["chapters"] = sort_records(raw["chapters"], ("chapter_id",))
    raw["volumes"] = sort_records(raw["volumes"], ("volume_id",))
    generated_at = now_iso()
    manifests = build_manifests(raw, current_inventory, generated_at)
    indexes = build_indexes(manifests, generated_at)
    embedding_records, embedding_info = build_embedding_records(workspace, manifests["documents"], config)
    llamaindex_info = persist_llamaindex_bundle(runtime_llamaindex_root(workspace), manifests["documents"], bool(embedding_records))
    freshness = build_runtime_state(workspace, config, current_inventory, changed_files if not effective_full else sorted(current_inventory), removed_files)
    meta = {"workspace": workspace.as_posix(), "generated_at": generated_at, "full_rebuild": effective_full, "changed_files": changed_files if not effective_full else sorted(current_inventory), "removed_files": removed_files, "unchanged_files": unchanged_files, "config": config}
    return raw, manifests, indexes, freshness, embedding_records, embedding_info, llamaindex_info, meta
