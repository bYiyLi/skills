from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from string import Template
import re

import yaml

from .constants import (
    ARCHIVE_DIR,
    CACHE_DIR,
    CHARACTERS_DIR,
    CHAPTERS_DIR,
    DRAFT_FILE,
    EMBEDDINGS_DIR,
    INDEXES_DIR,
    LLAMAINDEX_DIR,
    LOGS_DIR,
    MAIN_PLOT_FILE,
    MANIFESTS_DIR,
    NOVEL_DIR,
    REPORTS_DIR,
    REQUIRED_SETTING_FILES,
    REQUIRED_WORK_FRONTMATTER,
    REQUIRED_WORK_SECTIONS,
    RUNTIME_DIR,
    RUNTIME_INDEX_DATASETS,
    RUNTIME_MANIFEST_DATASETS,
    SETTINGS_DIR,
    TIMELINE_FILE,
    TMP_DIR,
    VOLUMES_DIR,
    WORK_FILE,
    WORLD_FILE,
)
from .errors import ConfigError, WorkspaceError
from .utils import ensure_directory, write_text_if_changed

SECTION_RE = re.compile(r"^##\s+(.+)$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

DEFAULT_CONFIG = {
    "workspace": {
        "locale": "zh-CN",
        "chapter_ready_scene_threshold": 3,
        "chapter_ready_char_threshold": 6000,
        "volume_ready_chapter_threshold": 3,
        "volume_ready_char_threshold": 20000,
    },
    "retrieval": {
        "default_limit": 8,
        "lexical_weight": 1.0,
        "semantic_weight": 0.35,
        "rerank_weight": 1.0,
    },
    "embedding": {
        "enabled": False,
        "provider": "openai-compatible",
        "base_url": "https://api.example.com",
        "model": "text-embedding-3-small",
        "api_key_env": "OPENAI_API_KEY",
        "batch_size": 32,
        "timeout": 60,
    },
    "reranker": {
        "enabled": False,
        "provider": "openai-compatible",
        "base_url": "https://api.example.com",
        "model": "rerank-1",
        "api_key_env": "OPENAI_API_KEY",
        "top_k": 20,
        "timeout": 60,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def resolve_config(raw_config: dict | None = None) -> dict:
    raw = raw_config if isinstance(raw_config, dict) else {}
    return _deep_merge(DEFAULT_CONFIG, raw)


def find_skill_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "SKILL.md").exists() and (candidate / "assets" / "workspace").exists():
            return candidate
    raise WorkspaceError("Unable to locate skill root from installed package.")


def template_dir() -> Path:
    return find_skill_root() / "assets" / "workspace"


def load_template_text(name: str) -> str:
    path = template_dir() / name
    if not path.exists():
        raise WorkspaceError(f"Missing template: {name}")
    return path.read_text(encoding="utf-8")


def render_template(name: str, variables: dict[str, object] | None = None) -> str:
    raw = load_template_text(name)
    if not variables:
        return raw
    payload = {key: str(value) for key, value in variables.items()}
    return Template(raw).safe_substitute(payload)


def _normalize_yaml_value(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _normalize_yaml_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def split_frontmatter_text(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    marker = "\n---\n"
    end_index = text.find(marker, 4)
    if end_index == -1:
        return {}, text
    raw = text[4:end_index]
    data = _normalize_yaml_value(yaml.safe_load(raw) or {})
    if not isinstance(data, dict):
        return {}, text
    return data, text[end_index + len(marker) :]


def parse_work_body(body: str) -> dict:
    sections: dict[str, list[str]] = {"__root__": []}
    current = "__root__"
    for line in body.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = match.group(1).strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)

    def link_items(section_name: str) -> list[dict]:
        items: list[dict] = []
        for line in sections.get(section_name, []):
            match = LINK_RE.search(line)
            if not match:
                continue
            items.append({"label": match.group(1).strip(), "path": match.group(2).strip()})
        return items

    return {
        "sections": sections,
        "current_focus_lines": sections.get("Current Focus", []),
        "blocker_lines": sections.get("Blockers", []),
        "next_step_lines": sections.get("Next Step", []),
        "setting_links": link_items("设定索引"),
        "character_links": link_items("角色索引"),
    }


def novel_root(workspace: Path) -> Path:
    return workspace / NOVEL_DIR


def cache_root(workspace: Path) -> Path:
    return novel_root(workspace) / CACHE_DIR


def embedding_cache_root(workspace: Path) -> Path:
    return cache_root(workspace) / EMBEDDINGS_DIR


def runtime_root(workspace: Path) -> Path:
    return novel_root(workspace) / RUNTIME_DIR


def runtime_manifest_root(workspace: Path) -> Path:
    return runtime_root(workspace) / MANIFESTS_DIR


def runtime_index_root(workspace: Path) -> Path:
    return runtime_root(workspace) / INDEXES_DIR


def runtime_report_root(workspace: Path) -> Path:
    return runtime_root(workspace) / REPORTS_DIR


def runtime_llamaindex_root(workspace: Path) -> Path:
    return runtime_root(workspace) / LLAMAINDEX_DIR


def runtime_freshness_path(workspace: Path) -> Path:
    return runtime_root(workspace) / "freshness.json"


def work_file_path(workspace: Path) -> Path:
    return workspace / WORK_FILE


def draft_file_path(workspace: Path) -> Path:
    return workspace / DRAFT_FILE


def settings_root(workspace: Path) -> Path:
    return workspace / SETTINGS_DIR


def characters_root(workspace: Path) -> Path:
    return workspace / CHARACTERS_DIR


def archive_root(workspace: Path) -> Path:
    return workspace / ARCHIVE_DIR


def volumes_root(workspace: Path) -> Path:
    return archive_root(workspace) / VOLUMES_DIR


def current_volume_dir(workspace: Path, volume_id: str) -> Path:
    return volumes_root(workspace) / volume_id


def current_volume_chapters_dir(workspace: Path, volume_id: str) -> Path:
    return current_volume_dir(workspace, volume_id) / CHAPTERS_DIR


def current_volume_summary_path(workspace: Path, volume_id: str) -> Path:
    return current_volume_dir(workspace, volume_id) / "卷.md"


def source_file_paths(workspace: Path, config: dict) -> list[Path]:
    workspace = workspace.resolve()
    paths: list[Path] = [
        work_file_path(workspace),
        draft_file_path(workspace),
    ]
    if settings_root(workspace).exists():
        paths.extend(sorted(path for path in settings_root(workspace).rglob("*.md") if path.is_file()))
    if characters_root(workspace).exists():
        paths.extend(sorted(path for path in characters_root(workspace).rglob("*.md") if path.is_file()))
    if volumes_root(workspace).exists():
        paths.extend(sorted(path for path in volumes_root(workspace).rglob("*.md") if path.is_file()))
    ordered: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        key = path.resolve().as_posix()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered


def default_workspace_layout(workspace: Path) -> list[Path]:
    layout = [
        settings_root(workspace),
        characters_root(workspace),
        archive_root(workspace),
        volumes_root(workspace),
        embedding_cache_root(workspace),
        runtime_root(workspace),
        runtime_report_root(workspace),
        runtime_llamaindex_root(workspace),
        novel_root(workspace) / TMP_DIR,
        novel_root(workspace) / LOGS_DIR,
    ]
    layout.extend(runtime_manifest_root(workspace) / dataset for dataset in RUNTIME_MANIFEST_DATASETS)
    layout.extend(runtime_index_root(workspace) / dataset for dataset in RUNTIME_INDEX_DATASETS)
    return layout


def ensure_runtime_layout(workspace: Path) -> None:
    for directory in default_workspace_layout(workspace):
        ensure_directory(directory)


def expected_required_files(workspace: Path) -> list[Path]:
    return [
        work_file_path(workspace),
        draft_file_path(workspace),
        settings_root(workspace) / WORLD_FILE,
        settings_root(workspace) / MAIN_PLOT_FILE,
        settings_root(workspace) / TIMELINE_FILE,
        novel_root(workspace) / "config.yaml",
    ]


def _normalize_registry_path(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    candidate = Path(text)
    if candidate.is_absolute():
        return ""
    if ".." in candidate.parts:
        return ""
    return candidate.as_posix()


def _registry_report(paths: list[str], *, expected_prefix: str) -> dict:
    duplicates: list[str] = []
    invalid: list[str] = []
    out_of_scope: list[str] = []
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in paths:
        cleaned = _normalize_registry_path(raw)
        if not cleaned:
            invalid.append(raw)
            continue
        if not cleaned.endswith(".md"):
            invalid.append(raw)
            continue
        if cleaned in seen:
            duplicates.append(cleaned)
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
        if not cleaned.startswith(f"{expected_prefix}/"):
            out_of_scope.append(cleaned)
    return {
        "normalized": normalized,
        "duplicates": sorted(duplicates),
        "invalid": sorted(invalid),
        "out_of_scope": sorted(out_of_scope),
    }


def inspect_workspace_contract(workspace: Path, config: dict) -> dict:
    workspace = workspace.resolve()
    required_paths = expected_required_files(workspace)
    missing_required_files = [path.relative_to(workspace).as_posix() for path in required_paths if not path.exists()]

    work_frontmatter: dict = {}
    body = ""
    registry = {
        "sections": {},
        "current_focus_lines": [],
        "blocker_lines": [],
        "next_step_lines": [],
        "setting_links": [],
        "character_links": [],
    }
    missing_frontmatter: list[str] = []
    missing_sections: list[str] = []
    work_path = work_file_path(workspace)
    if work_path.exists():
        work_frontmatter, body = split_frontmatter_text(work_path.read_text(encoding="utf-8"))
        registry = parse_work_body(body)
        missing_frontmatter = [field for field in REQUIRED_WORK_FRONTMATTER if field not in work_frontmatter]
        missing_sections = [section for section in REQUIRED_WORK_SECTIONS if section not in registry["sections"]]
    else:
        missing_frontmatter = list(REQUIRED_WORK_FRONTMATTER)
        missing_sections = list(REQUIRED_WORK_SECTIONS)

    setting_registry = _registry_report([item["path"] for item in registry["setting_links"]], expected_prefix=SETTINGS_DIR)
    character_registry = _registry_report([item["path"] for item in registry["character_links"]], expected_prefix=CHARACTERS_DIR)

    registered_settings = sorted(setting_registry["normalized"])
    registered_characters = sorted(character_registry["normalized"])
    actual_settings = sorted(
        path.relative_to(workspace).as_posix()
        for path in settings_root(workspace).rglob("*.md")
        if path.is_file()
    ) if settings_root(workspace).exists() else []
    actual_characters = sorted(
        path.relative_to(workspace).as_posix()
        for path in characters_root(workspace).rglob("*.md")
        if path.is_file()
    ) if characters_root(workspace).exists() else []

    broken_setting_links = sorted(path for path in registered_settings if not (workspace / path).exists())
    broken_character_links = sorted(path for path in registered_characters if not (workspace / path).exists())
    unregistered_settings = sorted(path for path in actual_settings if path not in set(registered_settings))
    unregistered_characters = sorted(path for path in actual_characters if path not in set(registered_characters))
    missing_required_setting_links = sorted(path for path in REQUIRED_SETTING_FILES if path not in set(registered_settings))

    contract_mismatches: list[str] = []
    if missing_frontmatter:
        contract_mismatches.append(f"WORK.md is missing required frontmatter fields: {', '.join(missing_frontmatter)}.")
    if missing_sections:
        contract_mismatches.append(f"WORK.md is missing required sections: {', '.join(missing_sections)}.")
    if setting_registry["invalid"]:
        contract_mismatches.append(f"WORK.md has invalid setting links: {', '.join(setting_registry['invalid'])}.")
    if setting_registry["out_of_scope"]:
        contract_mismatches.append(f"WORK.md setting links must stay under `{SETTINGS_DIR}/`: {', '.join(setting_registry['out_of_scope'])}.")
    if broken_setting_links:
        contract_mismatches.append(f"WORK.md points to missing setting files: {', '.join(broken_setting_links)}.")
    if character_registry["invalid"]:
        contract_mismatches.append(f"WORK.md has invalid character links: {', '.join(character_registry['invalid'])}.")
    if character_registry["out_of_scope"]:
        contract_mismatches.append(f"WORK.md character links must stay under `{CHARACTERS_DIR}/`: {', '.join(character_registry['out_of_scope'])}.")
    if broken_character_links:
        contract_mismatches.append(f"WORK.md points to missing character files: {', '.join(broken_character_links)}.")
    if setting_registry["duplicates"]:
        contract_mismatches.append(f"WORK.md contains duplicate setting links: {', '.join(setting_registry['duplicates'])}.")
    if character_registry["duplicates"]:
        contract_mismatches.append(f"WORK.md contains duplicate character links: {', '.join(character_registry['duplicates'])}.")
    if missing_required_setting_links:
        contract_mismatches.append(f"WORK.md setting index must register required files: {', '.join(missing_required_setting_links)}.")
    if unregistered_settings:
        contract_mismatches.append(f"Unregistered setting files exist under `{SETTINGS_DIR}/`: {', '.join(unregistered_settings)}.")
    if unregistered_characters:
        contract_mismatches.append(f"Unregistered character files exist under `{CHARACTERS_DIR}/`: {', '.join(unregistered_characters)}.")

    return {
        "required_files": [path.relative_to(workspace).as_posix() for path in required_paths],
        "missing_required_files": missing_required_files,
        "work_frontmatter": work_frontmatter,
        "work_body": body,
        "missing_frontmatter": missing_frontmatter,
        "missing_sections": missing_sections,
        "setting_registry": setting_registry,
        "character_registry": character_registry,
        "broken_setting_links": broken_setting_links,
        "broken_character_links": broken_character_links,
        "unregistered_settings": unregistered_settings,
        "unregistered_characters": unregistered_characters,
        "missing_required_setting_links": missing_required_setting_links,
        "actual_settings": actual_settings,
        "actual_characters": actual_characters,
        "registered_settings": registered_settings,
        "registered_characters": registered_characters,
        "contract_mismatches": contract_mismatches,
    }


def init_workspace(workspace: Path, *, force: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    directories = [path.as_posix() for path in default_workspace_layout(workspace)]
    copies = {
        "WORK.md.tmpl": work_file_path(workspace),
        "世界观.md.tmpl": settings_root(workspace) / WORLD_FILE,
        "主线规格.md.tmpl": settings_root(workspace) / MAIN_PLOT_FILE,
        "时间线.md.tmpl": settings_root(workspace) / TIMELINE_FILE,
        "正文创作区.md.tmpl": draft_file_path(workspace),
        "config.yaml.tmpl": novel_root(workspace) / "config.yaml",
        "dot-gitignore.tmpl": workspace / ".gitignore",
        "dot-gitattributes.tmpl": workspace / ".gitattributes",
    }
    if dry_run:
        return {
            "workspace": workspace.as_posix(),
            "dry_run": True,
            "directories": directories,
            "planned_files": [path.as_posix() for path in copies.values()],
        }
    ensure_runtime_layout(workspace)
    written: list[str] = []
    skipped: list[str] = []
    for template_name, destination in copies.items():
        content = render_template(template_name)
        if destination.exists() and not force:
            skipped.append(destination.as_posix())
            continue
        write_text_if_changed(destination, content)
        written.append(destination.as_posix())
    return {
        "workspace": workspace.as_posix(),
        "written": written,
        "skipped": skipped,
        "runtime_root": runtime_root(workspace).as_posix(),
        "embedding_cache_root": embedding_cache_root(workspace).as_posix(),
    }


def load_config(workspace: Path, *, allow_missing: bool = False) -> dict:
    config_path = novel_root(workspace) / "config.yaml"
    if not config_path.exists():
        if allow_missing:
            return resolve_config({})
        raise ConfigError(
            f"Missing config: {config_path}",
            details={"config_path": config_path.as_posix()},
        )
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(
            f"Config is not valid YAML: {config_path}",
            details={"config_path": config_path.as_posix()},
        ) from exc
    if not isinstance(data, dict):
        raise ConfigError(
            "Config must be a YAML mapping.",
            details={"config_path": config_path.as_posix()},
        )
    return resolve_config(data)


def dump_config(config: dict) -> str:
    return yaml.safe_dump(resolve_config(config), allow_unicode=True, sort_keys=False)


def load_work_contract(workspace: Path) -> tuple[dict, str, dict]:
    path = work_file_path(workspace)
    if not path.exists():
        raise WorkspaceError(f"Missing WORK contract: {path}")
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter_text(text)
    return frontmatter, body, parse_work_body(body)


def _dump_work_contract(frontmatter: dict, body: str) -> str:
    payload = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)
    normalized_body = body.strip("\n")
    return f"---\n{payload}---\n\n{normalized_body}\n"


def write_work_contract(workspace: Path, frontmatter: dict, body: str) -> bool:
    return write_text_if_changed(work_file_path(workspace), _dump_work_contract(frontmatter, body))


def update_work_frontmatter(workspace: Path, **updates: object) -> bool:
    frontmatter, body, _ = load_work_contract(workspace)
    frontmatter.update(updates)
    registry = parse_work_body(body)
    setting_lines = registry["sections"].get("设定索引", ["- [世界观](设定/世界观.md)", "- [主线规格](设定/主线规格.md)", "- [时间线](设定/时间线.md)"])
    character_lines = registry["sections"].get("角色索引", ["- 暂无"])
    body_lines = [
        "# WORK",
        "",
        "## Current Focus",
        "",
        f"- stage: {frontmatter.get('stage', 'bootstrap')}",
        f"- current-task: {frontmatter.get('current_task_type', 'bootstrap')}",
        f"- current-scope: {frontmatter.get('current_scope', '') or '待补充'}",
        "",
        "## Blockers",
        "",
        *([f"- {item}" for item in frontmatter.get("blockers", []) if str(item).strip()] or ["- 暂无"]),
        "",
        "## Next Step",
        "",
        f"- {frontmatter.get('next_step', '') or '待补充'}",
        "",
        "## 设定索引",
        "",
        *(setting_lines or ["- 暂无"]),
        "",
        "## 角色索引",
        "",
        *(character_lines or ["- 暂无"]),
    ]
    return write_work_contract(workspace, frontmatter, "\n".join(body_lines) + "\n")
