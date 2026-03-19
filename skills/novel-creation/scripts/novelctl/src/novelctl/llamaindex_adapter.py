from __future__ import annotations

from pathlib import Path

from .utils import write_json_if_changed, write_sharded_jsonl


def persist_llamaindex_bundle(output_dir: Path, documents: list[dict], semantic_available: bool) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    document_info = write_sharded_jsonl(output_dir / "documents", documents, "id")
    manifest = {
        "document_count": len(documents),
        "semantic_available": semantic_available,
        "status": "rebuildable-runtime-bundle",
        "notes": [
            "This directory is a runtime artifact and can be rebuilt from novel source files plus embedding cache.",
            "novelctl writes normalized documents here so LlamaIndex-compatible ingestion can be reconstructed on demand.",
        ],
    }
    write_json_if_changed(output_dir / "manifest.json", manifest)
    return {
        "document_count": len(documents),
        "shards": document_info["shards"],
        "semantic_available": semantic_available,
        "status": "rebuildable-runtime-bundle",
    }
