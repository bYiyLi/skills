from __future__ import annotations

from pathlib import Path

import yaml

from .constants import (
    ARCHIVE_DIR,
    CACHE_DIR,
    CHANGELOG_FILE,
    CHARACTER_DIR,
    CHAPTER_DIR,
    DRAFT_FILE,
    EMBEDDINGS_DIR,
    FACTION_DIR,
    ITEM_DIR,
    INDEXES_DIR,
    LLAMAINDEX_DIR,
    LOCATION_DIR,
    LOGS_DIR,
    MAIN_PLOT_FILE,
    MANIFESTS_DIR,
    NOVEL_DIR,
    PROJECT_STATUS_FILE,
    PROGRESS_DIR,
    REPORTS_DIR,
    RUNTIME_DIR,
    RUNTIME_INDEX_DATASETS,
    RUNTIME_MANIFEST_DATASETS,
    SETTINGS_DIR,
    TIMELINE_FILE,
    TMP_DIR,
    VOLUME_DIR,
    WORLD_FILE,
)
from .utils import ensure_directory, write_text_if_changed

FALLBACK_TEMPLATES = {
    "AGENTS.md.tmpl": """---
record_id: project-agents
record_type: project-agents
status: active
summary: 当前项目协作约束
tags:
  - project
  - agents
refs: []
updated_at: 2026-03-19
stage: bootstrap
active_plotlines:
  - plot-main-001
frozen_rules: []
retrieval_priority:
  - novelctl report context-pack --scene <scene_id>
  - novelctl retrieve fact "<query>"
archive_rules:
  - 只归档正文前部连续 ready 场景
---

# 小说项目 AGENTS.md

## 当前阶段

- stage: bootstrap
- last-sync: pending
- last-check: pending

## 活跃情节线

- plot-main-001

## 冻结设定与禁改项

- 暂无

## 当前创作约束

- 先补齐设定，再进入正文创作。
- 正文与结构化字段必须写在同一个文件里。
- 结构化字段更新后，正文也要同步体现。

## 检索优先路径

- 续写前先运行 `novelctl report context-pack --scene <scene_id>`。
- 查事实时优先用 `novelctl retrieve fact "<query>"`。
- 查角色、地点、势力时优先用 `novelctl retrieve entity "<query>"`。

## 归档规则

- 只归档正文前部连续 `ready` 场景。
- 归档后重新运行 `novelctl sync` 与 `novelctl check`。

## 下一步建议

- 补齐 `设定/` 下的世界观、主线规格和时间线。
""",
    "世界观.md.tmpl": """---
record_id: spec-world
record_type: spec
status: draft
summary: 故事世界观与底层规则
tags:
  - spec
  - world
refs: []
updated_at: 2026-03-19
---

# 世界观

## 核心命题

- 待补充

## 世界规则

- rule-world-001: 待补充

## 能力与限制

- constraint-001: 待补充

## 冻结项

- 暂无
""",
    "主线规格.md.tmpl": """---
record_id: spec-main-plot
record_type: spec
status: draft
summary: 主线目标、核心冲突与闭合条件
tags:
  - spec
  - plot
refs: []
updated_at: 2026-03-19
---

# 主线规格

## 主目标

- 待补充

## 核心冲突

- 待补充

## 主要情节线

- plot-main-001: 待补充

## 阶段性闭合条件

- 待补充
""",
    "时间线.md.tmpl": """---
record_id: spec-timeline
record_type: spec
status: draft
summary: 已确定时间点与时间规则
tags:
  - spec
  - timeline
refs: []
updated_at: 2026-03-19
---

# 时间线

## 已确定时间点

- time-0001: 故事开始

## 时间规则

- 使用相对时间或绝对纪年时保持一致。

## 未决时间问题

- 暂无
""",
    "项目状态.md.tmpl": """---
record_id: project-progress
record_type: project-progress
status: active
summary: 当前项目进展状态
tags:
  - project
  - progress
refs: []
updated_at: 2026-03-19
current_scene: none
current_chapter: none
current_volume: none
---

# 项目状态

## 当前推进位置

- current-scene: none
- current-chapter: none
- current-volume: none

## 最近同步

- last-sync: pending
- last-check: pending

## 未解决冲突候选

- 暂无

## 下一步建议

- 先补设定，再创建第一个场景块。
""",
    "变更记录.md.tmpl": """---
record_id: project-changelog
record_type: project-note
status: active
summary: 记录重要创作与归档变更
tags:
  - project
  - changelog
refs: []
updated_at: 2026-03-19
---

# 变更记录

## 2026-03-19

- 初始化小说工作区。
""",
    "正文创作区.md.tmpl": """# 正文创作区

## scene-0001 开场场景
```yaml
scene_id: scene-0001
status: draft
pov: 待补充
time: time-0001
location: 待补充
characters:
  - 待补充
plotlines:
  - plot-main-001
goal: 待补充
outcome: 待补充
continuity_refs: []
summary: >
  用 2 到 4 句概括本场景。
beats:
  - 待补充
new_facts:
  - id: fact-scene-0001-001
    subject: 待补充
    predicate: 待补充
    object: 待补充
state_changes:
  - entity: 待补充
    field: 待补充
    from: 待补充
    to: 待补充
foreshadow:
  - id: hook-scene-0001-001
    note: 待补充
payoff_refs: []
open_loops:
  - loop-scene-0001-001
```
正文:

在这里开始写第一个场景。
""",
    "config.yaml.tmpl": """workspace:
  locale: zh-CN
  chapter_ready_scene_threshold: 3
  chapter_ready_char_threshold: 6000
  volume_ready_chapter_threshold: 10
  volume_ready_char_threshold: 80000

freshness:
  auto_sync_on_read: true

retrieval:
  default_limit: 8
  lexical_weight: 1.0
  semantic_weight: 0.35
  rerank_weight: 1.0

embedding:
  enabled: false
  provider: openai-compatible
  base_url: https://api.example.com/v1
  model: text-embedding-3-small
  api_key_env: OPENAI_API_KEY
  batch_size: 32
  timeout: 60

reranker:
  enabled: false
  provider: openai-compatible
  base_url: https://api.example.com/v1
  model: rerank-1
  api_key_env: OPENAI_API_KEY
  top_k: 20
  timeout: 60
""",
    "chapter.md.tmpl": """---
record_id: chapter-0001
record_type: chapter
status: archived
summary: 本章摘要
tags:
  - chapter
refs: []
updated_at: 2026-03-19
chapter_id: chapter-0001
title: 第0001章 标题待补充
scene_ids:
  - scene-0001
---

# 第0001章 标题待补充
""",
    "volume.md.tmpl": """---
record_id: volume-0001
record_type: volume
status: archived
summary: 本卷摘要
tags:
  - volume
refs: []
updated_at: 2026-03-19
volume_id: volume-0001
title: 第0001卷 标题待补充
chapter_ids:
  - chapter-0001
closed_plotlines: []
unresolved_loops: []
---

# 第0001卷 标题待补充

## Chapters

- chapter-0001
""",
    "dot-gitignore.tmpl": """.novel/runtime/
.novel/tmp/
.novel/logs/
.novel/**/*.lock
""",
    "dot-gitattributes.tmpl": """.novel/cache/embeddings/** filter=lfs diff=lfs merge=lfs -text
""",
}


def find_skill_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "SKILL.md").exists() and (candidate / "assets" / "workspace").exists():
            return candidate
    raise FileNotFoundError("Unable to locate skill root from installed package.")


def template_dir() -> Path:
    return find_skill_root() / "assets" / "workspace"


def load_template_text(name: str) -> str:
    if name in FALLBACK_TEMPLATES:
        return FALLBACK_TEMPLATES[name]
    try:
        path = template_dir() / name
        if path.exists():
            return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pass
    if name not in FALLBACK_TEMPLATES:
        raise FileNotFoundError(f"Missing template: {name}")
    return FALLBACK_TEMPLATES[name]


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


def source_file_paths(workspace: Path) -> list[Path]:
    settings = workspace / SETTINGS_DIR
    progress = workspace / PROGRESS_DIR
    archive = workspace / ARCHIVE_DIR
    paths = [
        workspace / "AGENTS.md",
        workspace / DRAFT_FILE,
        workspace / NOVEL_DIR / "config.yaml",
    ]
    if settings.exists():
        paths.extend(sorted(path for path in settings.rglob("*.md") if path.is_file()))
    if progress.exists():
        paths.extend(sorted(path for path in progress.rglob("*.md") if path.is_file()))
    if (archive / CHAPTER_DIR).exists():
        paths.extend(sorted(path for path in (archive / CHAPTER_DIR).glob("*.md") if path.is_file()))
    if (archive / VOLUME_DIR).exists():
        paths.extend(sorted(path for path in (archive / VOLUME_DIR).glob("*.md") if path.is_file()))
    return [path for path in paths if path.exists() and path.is_file()]


def default_workspace_layout(workspace: Path) -> list[Path]:
    paths = [
        workspace / SETTINGS_DIR,
        workspace / SETTINGS_DIR / CHARACTER_DIR,
        workspace / SETTINGS_DIR / FACTION_DIR,
        workspace / SETTINGS_DIR / LOCATION_DIR,
        workspace / SETTINGS_DIR / ITEM_DIR,
        workspace / PROGRESS_DIR,
        workspace / ARCHIVE_DIR,
        workspace / ARCHIVE_DIR / CHAPTER_DIR,
        workspace / ARCHIVE_DIR / VOLUME_DIR,
        embedding_cache_root(workspace),
        runtime_root(workspace),
        runtime_report_root(workspace),
        runtime_llamaindex_root(workspace),
        novel_root(workspace) / TMP_DIR,
        novel_root(workspace) / LOGS_DIR,
    ]
    paths.extend(runtime_manifest_root(workspace) / dataset for dataset in RUNTIME_MANIFEST_DATASETS)
    paths.extend(runtime_index_root(workspace) / dataset for dataset in RUNTIME_INDEX_DATASETS)
    return paths


def ensure_runtime_layout(workspace: Path) -> None:
    for directory in default_workspace_layout(workspace):
        ensure_directory(directory)


def init_workspace(workspace: Path, force: bool = False, dry_run: bool = False) -> dict:
    workspace = workspace.resolve()
    directories = [path.as_posix() for path in default_workspace_layout(workspace)]
    copies = {
        "AGENTS.md.tmpl": workspace / "AGENTS.md",
        "世界观.md.tmpl": workspace / SETTINGS_DIR / WORLD_FILE,
        "主线规格.md.tmpl": workspace / SETTINGS_DIR / MAIN_PLOT_FILE,
        "时间线.md.tmpl": workspace / SETTINGS_DIR / TIMELINE_FILE,
        "项目状态.md.tmpl": workspace / PROGRESS_DIR / PROJECT_STATUS_FILE,
        "变更记录.md.tmpl": workspace / PROGRESS_DIR / CHANGELOG_FILE,
        "正文创作区.md.tmpl": workspace / DRAFT_FILE,
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
        content = load_template_text(template_name)
        if destination.exists() and not force:
            skipped.append(destination.as_posix())
            continue
        write_text_if_changed(destination, content)
        written.append(destination.as_posix())

    for subdir in (CHARACTER_DIR, FACTION_DIR, LOCATION_DIR, ITEM_DIR):
        placeholder = workspace / SETTINGS_DIR / subdir / ".gitkeep"
        if not placeholder.exists():
            placeholder.write_text("", encoding="utf-8")

    return {
        "workspace": workspace.as_posix(),
        "written": written,
        "skipped": skipped,
        "runtime_root": runtime_root(workspace).as_posix(),
        "embedding_cache_root": embedding_cache_root(workspace).as_posix(),
    }


def load_config(workspace: Path) -> dict:
    config_path = novel_root(workspace) / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping.")
    return data
