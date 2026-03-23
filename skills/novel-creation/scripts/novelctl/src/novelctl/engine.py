from __future__ import annotations

from pathlib import Path

from .analysis_ops import analyze_snapshot, report_summary_file, write_analysis_reports
from .archive_ops import archive_chapter as archive_chapter_impl
from .archive_ops import archive_volume as archive_volume_impl
from .retrieval_ops import report_conflicts, report_context_pack, report_freshness, report_gates, report_summary, report_unresolved, retrieve, status
from .runtime_ops import config_md5, ensure_fresh_runtime, inventory_diff, load_config, run_sync_core, runtime_complete, semantic_status, source_inventory, write_runtime_files
from .utils import load_json
from .workspace import runtime_freshness_path


def run_sync(workspace: Path, full: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    config = load_config(workspace)
    if dry_run:
        current_inventory = source_inventory(workspace, config)
        previous_state = load_json(runtime_freshness_path(workspace), {"files": {}})
        changed_files, unchanged_files, removed_files = inventory_diff(previous_state, current_inventory)
        effective_full = full or not runtime_complete(workspace) or previous_state.get("config_md5") != config_md5(config)
        return {
            "workspace": workspace.as_posix(),
            "dry_run": True,
            "full_rebuild": effective_full,
            "changed_files": changed_files if not effective_full else sorted(current_inventory),
            "removed_files": removed_files,
            "unchanged_files": unchanged_files,
        }
    raw, manifests, indexes, freshness, embedding_records, embedding_info, llamaindex_info, meta = run_sync_core(workspace, force_full=full)
    analysis = analyze_snapshot(workspace, manifests, meta["config"])
    write_runtime_files(workspace, raw, manifests, indexes, analysis, freshness, embedding_records, embedding_info, llamaindex_info)
    status_payload = write_analysis_reports(workspace, analysis, manifests, freshness, semantic_status(meta["config"], embedding_records), llamaindex_info, meta["config"])
    return {
        "workspace": meta["workspace"],
        "generated_at": meta["generated_at"],
        "full_rebuild": meta["full_rebuild"] or full,
        "changed_files": meta["changed_files"],
        "removed_files": meta["removed_files"],
        "counts": {
            "source_docs": len(raw["source_docs"]),
            "documents": len(manifests["documents"]),
            "scenes": len(manifests["scenes"]),
            "chapters": len(raw["chapters"]),
            "volumes": len(raw["volumes"]),
            "plotlines": len(manifests["plotlines"]),
        },
        "embedding": embedding_info,
        "llamaindex": llamaindex_info,
        "status": status_payload,
    }


def run_check(workspace: Path, strict: bool = False) -> dict:
    workspace = workspace.resolve()
    ensure_fresh_runtime(workspace, run_sync, command_name="check", force_full=False)
    summary = report_summary_file(workspace)
    check = summary.get("check", {})
    check["strict"] = strict
    return check


def archive_chapter(workspace: Path, force: bool = False, dry_run: bool = False) -> dict:
    return archive_chapter_impl(workspace, load_config(workspace), run_sync, force=force, dry_run=dry_run)


def archive_volume(workspace: Path, force: bool = False, dry_run: bool = False) -> dict:
    return archive_volume_impl(workspace, load_config(workspace), run_sync, force=force, dry_run=dry_run)
