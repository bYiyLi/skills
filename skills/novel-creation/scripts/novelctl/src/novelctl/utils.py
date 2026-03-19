from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def stable_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def md5_text(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def md5_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def stable_id(prefix: str, seed: str, length: int = 12) -> str:
    return f"{prefix}-{sha1_text(seed)[:length]}"


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text_if_changed(path: Path, text: str) -> bool:
    ensure_directory(path.parent)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def write_json_if_changed(path: Path, data: object) -> bool:
    return write_text_if_changed(path, stable_dumps(data))


def write_sharded_jsonl(directory: Path, records: Iterable[dict], key_field: str) -> dict[str, int]:
    ensure_directory(directory)
    grouped: dict[str, list[dict]] = {}
    for record in records:
        key = str(record[key_field])
        shard = sha1_text(key)[:2]
        grouped.setdefault(shard, []).append(record)

    changed = 0
    for shard, values in grouped.items():
        lines = [
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            for item in sorted(values, key=lambda item: str(item[key_field]))
        ]
        changed += int(write_text_if_changed(directory / f"{shard}.jsonl", "\n".join(lines) + ("\n" if lines else "")))

    for existing in directory.glob("*.jsonl"):
        if existing.stem not in grouped:
            existing.unlink()
            changed += 1

    return {"shards": len(grouped), "changed_files": changed}


def delete_matching_records(records: Iterable[dict], source_paths: set[str]) -> list[dict]:
    return [record for record in records if str(record.get("source_path", "")) not in source_paths]


def load_json(path: Path, default: object | None = None) -> object:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_directory(directory: Path) -> list[dict]:
    records: list[dict] = []
    if not directory.exists():
        return records
    for file_path in sorted(directory.glob("*.jsonl")):
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


_HAN_RE = re.compile(r"[\u4e00-\u9fff]+")
_WORD_RE = re.compile(r"[A-Za-z0-9_-]+")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    lowered = text.lower()
    tokens.extend(match.group(0) for match in _WORD_RE.finditer(lowered))
    for match in _HAN_RE.finditer(text):
        run = match.group(0)
        if len(run) == 1:
            tokens.append(run)
            continue
        tokens.append(run)
        for index in range(len(run) - 1):
            tokens.append(run[index : index + 2])
    return [token for token in tokens if token.strip()]


def score_text(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    haystack = text.lower()
    counts = Counter(tokenize(text))
    score = 0.0
    for token in query_tokens:
        if len(token) > 1 and token in haystack:
            score += 2.0
        score += counts.get(token, 0)
    return score


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
