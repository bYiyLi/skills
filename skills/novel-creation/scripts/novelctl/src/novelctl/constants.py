from __future__ import annotations

SETTINGS_DIR = "\u8bbe\u5b9a"
CHARACTER_DIR = "\u89d2\u8272"
FACTION_DIR = "\u52bf\u529b"
LOCATION_DIR = "\u5730\u70b9"
ITEM_DIR = "\u7269\u4ef6"
PROGRESS_DIR = "\u8fdb\u5c55"
ARCHIVE_DIR = "\u5f52\u6863"
CHAPTER_DIR = "\u7ae0\u8282"
VOLUME_DIR = "\u5377"

WORLD_FILE = "\u4e16\u754c\u89c2.md"
MAIN_PLOT_FILE = "\u4e3b\u7ebf\u89c4\u683c.md"
TIMELINE_FILE = "\u65f6\u95f4\u7ebf.md"
PROJECT_STATUS_FILE = "\u9879\u76ee\u72b6\u6001.md"
CHANGELOG_FILE = "\u53d8\u66f4\u8bb0\u5f55.md"
DRAFT_FILE = "\u6b63\u6587\u521b\u4f5c\u533a.md"

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
    "facts",
    "entities",
    "timelines",
    "plotlines",
    "chapters",
    "volumes",
    "progress",
]

RUNTIME_INDEX_DATASETS = [
    "inverted",
    "entity-map",
    "timeline",
    "plotline",
    "relation",
    "state",
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

PLACEHOLDER_VALUES = {
    "",
    "tbd",
    "todo",
    "pending",
    "none",
    "\u5f85\u8865\u5145",
    "\u5f85\u5b9a",
    "\u6682\u65e0",
    "\u672a\u5b9a",
}

ENTITY_DIRS = {
    CHARACTER_DIR: "\u89d2\u8272",
    FACTION_DIR: "\u52bf\u529b",
    LOCATION_DIR: "\u5730\u70b9",
    ITEM_DIR: "\u7269\u4ef6",
}

TEXT_SEARCH_KINDS = {
    "scene",
    "chapter",
    "volume",
    "entity",
    "spec",
}

