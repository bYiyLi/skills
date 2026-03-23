from __future__ import annotations

SETTINGS_DIR = "设定"
CHARACTERS_DIR = "角色"
ARCHIVE_DIR = "归档"
VOLUMES_DIR = "卷"
CHAPTERS_DIR = "章节"

WORLD_FILE = "世界观.md"
MAIN_PLOT_FILE = "主线规格.md"
TIMELINE_FILE = "时间线.md"
DRAFT_FILE = "正文创作区.md"
WORK_FILE = "WORK.md"

NOVEL_DIR = ".novel"
CACHE_DIR = "cache"
EMBEDDINGS_DIR = "embeddings"
RUNTIME_DIR = "runtime"
MANIFESTS_DIR = "manifests"
INDEXES_DIR = "indexes"
REPORTS_DIR = "reports"
LLAMAINDEX_DIR = "llamaindex"
TMP_DIR = "tmp"
LOGS_DIR = "logs"

RUNTIME_MANIFEST_DATASETS = [
    "source-docs",
    "documents",
    "scenes",
    "plotlines",
    "chapters",
    "volumes",
]

RUNTIME_INDEX_DATASETS = [
    "inverted",
    "embedding",
]

REPORT_FILES = [
    "status.json",
    "check-summary.json",
    "conflict-candidates.json",
    "conflict-candidates.md",
    "gates.json",
    "unresolved.json",
    "freshness.json",
    "summary.json",
]

REQUIRED_WORK_FRONTMATTER = [
    "stage",
    "current_task_type",
    "current_scope",
    "current_scene",
    "current_chapter",
    "current_volume",
    "blockers",
    "next_step",
]

REQUIRED_WORK_SECTIONS = [
    "Current Focus",
    "Blockers",
    "Next Step",
    "设定索引",
    "角色索引",
]

REQUIRED_SETTING_FILES = [
    f"{SETTINGS_DIR}/{WORLD_FILE}",
    f"{SETTINGS_DIR}/{MAIN_PLOT_FILE}",
    f"{SETTINGS_DIR}/{TIMELINE_FILE}",
]

PLACEHOLDER_VALUES = {
    "",
    "tbd",
    "todo",
    "pending",
    "none",
    "待补充",
    "待定",
    "暂无",
    "未定",
}

READINESS_BOOTSTRAP_INCOMPLETE = "bootstrap-incomplete"
READINESS_DRAFT_READY = "draft-ready"
READINESS_ARCHIVE_READY = "archive-ready"
