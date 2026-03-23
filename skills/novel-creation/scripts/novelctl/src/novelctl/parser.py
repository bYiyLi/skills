from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import yaml

from .constants import ARCHIVE_DIR, CHARACTERS_DIR, CHAPTERS_DIR, DRAFT_FILE, PLACEHOLDER_VALUES, SETTINGS_DIR, VOLUMES_DIR, WORK_FILE
from .utils import md5_file, relative_posix, stable_id
from .workspace import parse_work_body, split_frontmatter_text, volumes_root

SCENE_BLOCK_RE = re.compile(
    r"^##\s+(?P<heading>[^\n]+)\r?\n```yaml\r?\n(?P<meta>.*?)\r?\n```\r?\n(?P<body>.*?)(?=^##\s+[^\n]+\r?\n```yaml|\Z)",
    re.MULTILINE | re.DOTALL,
)
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

REQUIRED_SCENE_FIELDS = {
    "scene_id",
    "status",
    "pov",
    "time",
    "location",
    "characters",
    "plotlines",
    "goal",
    "outcome",
    "continuity_refs",
    "summary",
    "beats",
    "new_facts",
    "state_changes",
    "foreshadow",
    "payoff_refs",
    "open_loops",
}

ALLOW_EMPTY_LIST_FIELDS = {"continuity_refs", "payoff_refs"}


def split_frontmatter(text: str) -> tuple[dict, str]:
    frontmatter, body = split_frontmatter_text(text)
    if frontmatter and not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML mapping.")
    return frontmatter, body


def parse_markdown_title(text: str, fallback: str) -> str:
    match = HEADING_RE.search(text)
    return match.group(1).strip() if match else fallback


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"__root__": []}
    current = "__root__"
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = match.group(1).strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _normalize_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalize_mapping_list(value: object) -> list[dict]:
    return [item for item in _normalize_list(value) if isinstance(item, dict)]


def _single_doc_record(
    *,
    path: Path,
    workspace: Path,
    body: str,
    frontmatter: dict,
    record_id: str,
    record_type: str,
    title: str,
    summary: str = "",
    kind: str = "",
    extra: dict | None = None,
) -> dict:
    rel_path = relative_posix(path, workspace)
    record = {
        "id": record_id,
        "record_id": record_id,
        "record_type": record_type,
        "title": title,
        "summary": summary or str(frontmatter.get("summary", "")).strip(),
        "status": str(frontmatter.get("status", "active")),
        "tags": [str(item) for item in _normalize_list(frontmatter.get("tags")) if str(item).strip()],
        "refs": [str(item) for item in _normalize_list(frontmatter.get("refs")) if str(item).strip()],
        "body": body.strip(),
        "source_path": rel_path,
        "source_file_md5": md5_file(path),
    }
    if kind:
        record["kind"] = kind
    if extra:
        record.update(extra)
    return record


def parse_scene_blocks(text: str, rel_path: str, source_kind: str, source_file_md5: str) -> list[dict]:
    scenes: list[dict] = []
    for order, match in enumerate(SCENE_BLOCK_RE.finditer(text), start=1):
        heading = match.group("heading").strip()
        metadata = yaml.safe_load(match.group("meta")) or {}
        if not isinstance(metadata, dict):
            raise ValueError(f"Scene metadata must be a mapping: {heading}")
        body = match.group("body").strip()
        if body.startswith("正文:"):
            body = body.split("\n", 1)[1].strip() if "\n" in body else ""
        scene_id = str(metadata.get("scene_id") or heading.split()[0].strip())
        title = heading[len(scene_id) :].strip() if heading.startswith(scene_id) else heading
        scenes.append(
            {
                "id": scene_id,
                "scene_id": scene_id,
                "title": title or scene_id,
                "status": str(metadata.get("status", "draft")),
                "pov": str(metadata.get("pov", "")).strip(),
                "time": str(metadata.get("time", "")).strip(),
                "location": str(metadata.get("location", "")).strip(),
                "characters": [str(item).strip() for item in _normalize_list(metadata.get("characters")) if str(item).strip()],
                "plotlines": [str(item).strip() for item in _normalize_list(metadata.get("plotlines")) if str(item).strip()],
                "goal": str(metadata.get("goal", "")).strip(),
                "outcome": str(metadata.get("outcome", "")).strip(),
                "continuity_refs": [str(item).strip() for item in _normalize_list(metadata.get("continuity_refs")) if str(item).strip()],
                "summary": str(metadata.get("summary", "")).strip(),
                "beats": [str(item).strip() for item in _normalize_list(metadata.get("beats")) if str(item).strip()],
                "new_facts": _normalize_mapping_list(metadata.get("new_facts")),
                "state_changes": _normalize_mapping_list(metadata.get("state_changes")),
                "foreshadow": _normalize_mapping_list(metadata.get("foreshadow")),
                "payoff_refs": [str(item).strip() for item in _normalize_list(metadata.get("payoff_refs")) if str(item).strip()],
                "open_loops": [item for item in _normalize_list(metadata.get("open_loops")) if item],
                "body": body,
                "source_kind": source_kind,
                "source_order": order,
                "source_path": rel_path,
                "source_file_md5": source_file_md5,
                "source_record_id": scene_id,
            }
        )
    return scenes


def render_scene(scene: dict) -> str:
    metadata = {
        "scene_id": scene["scene_id"],
        "status": scene["status"],
        "pov": scene["pov"],
        "time": scene["time"],
        "location": scene["location"],
        "characters": scene["characters"],
        "plotlines": scene["plotlines"],
        "goal": scene["goal"],
        "outcome": scene["outcome"],
        "continuity_refs": scene["continuity_refs"],
        "summary": scene["summary"],
        "beats": scene["beats"],
        "new_facts": scene["new_facts"],
        "state_changes": scene["state_changes"],
        "foreshadow": scene["foreshadow"],
        "payoff_refs": scene["payoff_refs"],
        "open_loops": scene["open_loops"],
    }
    heading = f"{scene['scene_id']} {scene['title']}".rstrip()
    yaml_text = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False).strip()
    return f"## {heading}\n```yaml\n{yaml_text}\n```\n正文:\n\n{scene['body'].strip()}\n"


def parse_source_markdown(path: Path, workspace: Path, kind: str) -> dict:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    title = parse_markdown_title(body, path.stem)
    record_id = str(frontmatter.get("record_id") or stable_id(kind, relative_posix(path, workspace)))
    source_group = "setting" if kind == "setting" else "character"
    return _single_doc_record(
        path=path,
        workspace=workspace,
        body=body,
        frontmatter=frontmatter,
        record_id=record_id,
        record_type=str(frontmatter.get("record_type", source_group)),
        title=str(frontmatter.get("name", title)),
        summary=str(frontmatter.get("summary", "")).strip(),
        kind="source",
        extra={
            "source_group": source_group,
            "source_title": path.stem,
        },
    )


def parse_work_file(path: Path, workspace: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    registry = parse_work_body(body)
    return _single_doc_record(
        path=path,
        workspace=workspace,
        body=body,
        frontmatter=frontmatter,
        record_id=str(frontmatter.get("record_id", "project-work")),
        record_type=str(frontmatter.get("record_type", "project-work")),
        title=str(frontmatter.get("title", "WORK")),
        summary=str(frontmatter.get("summary", "项目工作状态")).strip(),
        kind="work",
        extra={
            "stage": str(frontmatter.get("stage", "bootstrap")).strip() or "bootstrap",
            "current_task_type": str(frontmatter.get("current_task_type", "bootstrap")).strip() or "bootstrap",
            "current_scope": str(frontmatter.get("current_scope", "")).strip(),
            "current_scene": str(frontmatter.get("current_scene", "")).strip(),
            "current_chapter": str(frontmatter.get("current_chapter", "")).strip(),
            "current_volume": str(frontmatter.get("current_volume", "")).strip(),
            "blockers": [str(item).strip() for item in _normalize_list(frontmatter.get("blockers")) if str(item).strip()],
            "next_step": str(frontmatter.get("next_step", "")).strip(),
            "setting_index": [item["path"] for item in registry["setting_links"]],
            "character_index": [item["path"] for item in registry["character_links"]],
        },
    )


def parse_chapter_file(path: Path, workspace: Path) -> tuple[dict, list[dict]]:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    rel_path = relative_posix(path, workspace)
    file_md5 = md5_file(path)
    chapter_id = str(frontmatter.get("chapter_id") or frontmatter.get("record_id") or stable_id("chapter", rel_path))
    chapter = _single_doc_record(
        path=path,
        workspace=workspace,
        body=body,
        frontmatter=frontmatter,
        record_id=chapter_id,
        record_type=str(frontmatter.get("record_type", "chapter")),
        title=str(frontmatter.get("title", parse_markdown_title(body, path.stem))),
        summary=str(frontmatter.get("summary", "")).strip(),
        kind="chapter",
        extra={
            "chapter_id": chapter_id,
            "volume_id": str(frontmatter.get("volume_id", "")).strip(),
            "scene_ids": [str(item).strip() for item in _normalize_list(frontmatter.get("scene_ids")) if str(item).strip()],
            "source_file_md5": file_md5,
        },
    )
    scenes = parse_scene_blocks(body, rel_path, "chapter", file_md5)
    return chapter, scenes


def parse_volume_file(path: Path, workspace: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    rel_path = relative_posix(path, workspace)
    volume_id = str(frontmatter.get("volume_id") or frontmatter.get("record_id") or stable_id("volume", rel_path))
    return _single_doc_record(
        path=path,
        workspace=workspace,
        body=body,
        frontmatter=frontmatter,
        record_id=volume_id,
        record_type=str(frontmatter.get("record_type", "volume")),
        title=str(frontmatter.get("title", parse_markdown_title(body, path.stem))),
        summary=str(frontmatter.get("summary", "")).strip(),
        kind="volume",
        extra={
            "volume_id": volume_id,
            "chapter_ids": [str(item).strip() for item in _normalize_list(frontmatter.get("chapter_ids")) if str(item).strip()],
        },
    )


def parse_draft_file(path: Path, workspace: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    return parse_scene_blocks(text, relative_posix(path, workspace), "draft", md5_file(path))


def find_missing_scene_fields(scene: dict) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_SCENE_FIELDS:
        if field not in scene:
            missing.append(field)
            continue
        value = scene.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
            continue
        if isinstance(value, list) and not value and field not in ALLOW_EMPTY_LIST_FIELDS:
            missing.append(field)
    return sorted(missing)


def has_placeholder(value: object) -> bool:
    values = {item.lower() for item in PLACEHOLDER_VALUES}
    if isinstance(value, str):
        text = value.strip().lower()
        return not text or text in values
    if isinstance(value, list):
        return any(has_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(has_placeholder(item) for item in value.values())
    return False


def gather_markdown_files(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        return []
    return [path for path in sorted(directory.rglob("*.md")) if path.is_file()]


def detect_source_kind(path: Path, workspace: Path) -> str:
    rel = relative_posix(path, workspace)
    if rel == WORK_FILE:
        return "project-work"
    if rel == DRAFT_FILE:
        return "draft"
    if rel.startswith(f"{SETTINGS_DIR}/"):
        return "setting"
    if rel.startswith(f"{CHARACTERS_DIR}/"):
        return "character"
    if rel.startswith(f"{ARCHIVE_DIR}/{VOLUMES_DIR}/") and rel.endswith("/卷.md"):
        return "volume"
    if rel.startswith(f"{ARCHIVE_DIR}/{VOLUMES_DIR}/") and f"/{CHAPTERS_DIR}/" in rel:
        return "chapter"
    return "markdown"
