from __future__ import annotations

import json
import os
from typing import Iterable
from urllib import request

from .utils import md5_text


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def embedding_config(config: dict) -> dict:
    return _mapping(config.get("embedding"))


def reranker_config(config: dict) -> dict:
    return _mapping(config.get("reranker"))


def retrieval_config(config: dict) -> dict:
    return _mapping(config.get("retrieval"))


def embedding_enabled(config: dict) -> bool:
    data = embedding_config(config)
    return bool(data.get("enabled")) and bool(data.get("base_url")) and bool(data.get("model"))


def reranker_enabled(config: dict) -> bool:
    data = reranker_config(config)
    return bool(data.get("enabled")) and bool(data.get("base_url")) and bool(data.get("model"))


def embedding_signature(config: dict) -> str:
    data = embedding_config(config)
    signature = {
        "provider": data.get("provider", "openai-compatible"),
        "base_url": data.get("base_url", ""),
        "model": data.get("model", ""),
        "dimensions": data.get("dimensions", ""),
    }
    return md5_text(json.dumps(signature, ensure_ascii=False, sort_keys=True))


def reranker_signature(config: dict) -> str:
    data = reranker_config(config)
    signature = {
        "provider": data.get("provider", "openai-compatible"),
        "base_url": data.get("base_url", ""),
        "model": data.get("model", ""),
        "top_k": data.get("top_k", 20),
    }
    return md5_text(json.dumps(signature, ensure_ascii=False, sort_keys=True))


def _api_headers(api_key_env: str) -> dict[str, str]:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"Missing API key from environment variable: {api_key_env}")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: int) -> dict:
    req = request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def embed_texts(texts: Iterable[str], config: dict) -> list[list[float]]:
    data = embedding_config(config)
    if not embedding_enabled(config):
        return []
    payload = {
        "model": data["model"],
        "input": list(texts),
    }
    if data.get("dimensions"):
        payload["dimensions"] = data["dimensions"]
    timeout = int(data.get("timeout", 60))
    batch_size = max(1, int(data.get("batch_size", 32)))
    headers = _api_headers(str(data.get("api_key_env", "OPENAI_API_KEY")))
    base_url = str(data["base_url"]).rstrip("/")

    vectors: list[list[float]] = []
    inputs = payload["input"]
    for start in range(0, len(inputs), batch_size):
        batch_payload = dict(payload)
        batch_payload["input"] = inputs[start : start + batch_size]
        body = _post_json(f"{base_url}/embeddings", batch_payload, headers, timeout)
        items = body.get("data", [])
        vectors.extend(item.get("embedding", []) for item in items)
    return vectors


def rerank_candidates(query: str, documents: list[str], config: dict) -> list[dict]:
    data = reranker_config(config)
    if not reranker_enabled(config) or not documents:
        return []
    headers = _api_headers(str(data.get("api_key_env", "OPENAI_API_KEY")))
    timeout = int(data.get("timeout", 60))
    base_url = str(data["base_url"]).rstrip("/")
    payload = {
        "model": data["model"],
        "query": query,
        "documents": documents,
        "top_n": min(len(documents), int(data.get("top_k", 20))),
    }
    body = _post_json(f"{base_url}/rerank", payload, headers, timeout)
    items = body.get("data") or body.get("results") or []
    ranked: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ranked.append(
            {
                "index": int(item.get("index", item.get("document_index", -1))),
                "score": float(item.get("relevance_score", item.get("score", 0.0))),
            }
        )
    return [item for item in ranked if item["index"] >= 0]
