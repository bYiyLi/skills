from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import archive_chapter, archive_volume, report_conflicts, report_context_pack, report_freshness, report_gates, report_summary, report_unresolved, retrieve, run_check, run_sync, status
from .errors import NovelCtlError
from .workspace import init_workspace, load_config

FORMATTER = argparse.RawDescriptionHelpFormatter
QUERY_REQUIRED_MODES = ("text", "entity", "timeline", "plotline", "fact", "relation")
RETRIEVE_MODE_HELP = {
    "text": "检索正文、章节、卷、实体和规格文档中的文本。",
    "entity": "检索角色、地点、势力、物件等实体记录。",
    "timeline": "检索时间线记录。",
    "plotline": "检索情节线记录。",
    "fact": "检索事实与状态变更记录。",
    "relation": "检索关系记录。",
    "unresolved": "列出未闭合的情节线和 open loops。",
    "conflict-candidates": "列出待人工核实的冲突候选。",
}
REPORT_MODE_HELP = {
    "summary": "读取汇总报告，包含状态、检查、gates 和 freshness。",
    "conflicts": "读取完整冲突候选列表。",
    "gates": "读取当前 gates 结果。",
    "unresolved": "读取未解决 plotline/open loop 汇总。",
    "freshness": "查看 runtime freshness；auto-sync 关闭时会显式标出 stale。",
}


def add_common_workspace_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("workspace", help="Novel workspace path.")


def add_limit_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max results to return. Defaults to `.novel/config.yaml` -> `retrieval.default_limit`.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novelctl",
        description="JSON-first CLI for long-form novel workspaces.",
        epilog=(
            "Examples:\n"
            "  novelctl init ./my-novel --dry-run\n"
            "  novelctl sync ./my-novel\n"
            "  novelctl retrieve text ./my-novel \"黑石碎片\"\n"
            "  novelctl retrieve text ./my-novel --browse\n"
            "  novelctl report context-pack ./my-novel --scene scene-0003"
        ),
        formatter_class=FORMATTER,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a novel workspace.",
        description="Initialize a novel workspace from the bundled templates.",
        epilog="Example:\n  novelctl init ./my-novel --dry-run",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(init_parser)
    init_parser.add_argument("--force", action="store_true", help="Overwrite template files when possible.")
    init_parser.add_argument("--dry-run", action="store_true", help="Preview workspace initialization without writing files.")

    sync_parser = subparsers.add_parser(
        "sync",
        help="Sync runtime manifests, indexes, and reports.",
        description="Rebuild runtime manifests, indexes, embeddings, and generated reports from source Markdown.",
        epilog="Example:\n  novelctl sync ./my-novel --full",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(sync_parser)
    sync_parser.add_argument("--full", action="store_true", help="Force a full rebuild instead of an incremental sync.")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview sync changes without touching runtime files.")

    check_parser = subparsers.add_parser(
        "check",
        help="Run deterministic consistency checks.",
        description="Run consistency checks against the latest runtime snapshot.",
        epilog="Example:\n  novelctl check ./my-novel --strict",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(check_parser)
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings and review_required as blocking for the process exit code.",
    )

    retrieve_parser = subparsers.add_parser(
        "retrieve",
        help="Run typed retrieval.",
        description="Retrieve typed context from the runtime index or browse supported datasets explicitly.",
        epilog="Example:\n  novelctl retrieve fact ./my-novel \"林野\"\n  novelctl retrieve text ./my-novel --browse",
        formatter_class=FORMATTER,
    )
    retrieve_subparsers = retrieve_parser.add_subparsers(dest="mode", required=True, metavar="MODE")
    for mode, help_text in RETRIEVE_MODE_HELP.items():
        mode_parser = retrieve_subparsers.add_parser(
            mode,
            help=help_text,
            description=help_text,
            formatter_class=FORMATTER,
        )
        add_common_workspace_arg(mode_parser)
        mode_parser.add_argument(
            "query",
            nargs="?",
            default="",
            help="Query string. Required for query-driven modes unless `--browse` is passed.",
        )
        add_limit_arg(mode_parser)
        if mode in QUERY_REQUIRED_MODES:
            mode_parser.add_argument(
                "--browse",
                action="store_true",
                help="Browse the dataset without a query. Output includes `browse_mode: true`.",
            )

    archive_parser = subparsers.add_parser(
        "archive",
        help="Archive scenes into chapters or chapters into volumes.",
        description="Archive leading ready scenes into chapters, or eligible chapters into volumes.",
        epilog="Example:\n  novelctl archive chapter ./my-novel\n  novelctl archive volume ./my-novel --force",
        formatter_class=FORMATTER,
    )
    archive_subparsers = archive_parser.add_subparsers(dest="archive_mode", required=True, metavar="TARGET")
    archive_chapter_parser = archive_subparsers.add_parser(
        "chapter",
        help="Archive leading ready scenes into a chapter.",
        description="Archive leading ready scenes from 正文创作区.md into a new chapter file.",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(archive_chapter_parser)
    archive_chapter_parser.add_argument("--force", action="store_true", help="Override chapter threshold checks.")
    archive_chapter_parser.add_argument("--dry-run", action="store_true", help="Preview chapter archive changes.")
    archive_volume_parser = archive_subparsers.add_parser(
        "volume",
        help="Archive eligible chapters into a volume.",
        description="Archive eligible chapters into a new volume file when thresholds and closure checks pass.",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(archive_volume_parser)
    archive_volume_parser.add_argument("--force", action="store_true", help="Override volume threshold checks.")
    archive_volume_parser.add_argument("--dry-run", action="store_true", help="Preview volume archive changes.")

    status_parser = subparsers.add_parser(
        "status",
        help="Show current workspace status.",
        description="Show the current workspace status. Output is JSON by default.",
        epilog="Example:\n  novelctl status ./my-novel",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(status_parser)
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="Compatibility no-op. Status already prints JSON by default.",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Read generated reports.",
        description="Read generated reports from `.novel/runtime/reports/`.",
        epilog="Example:\n  novelctl report summary ./my-novel\n  novelctl report context-pack ./my-novel --scene scene-0002",
        formatter_class=FORMATTER,
    )
    report_subparsers = report_parser.add_subparsers(dest="report_mode", required=True, metavar="REPORT")
    for name, help_text in REPORT_MODE_HELP.items():
        report_mode_parser = report_subparsers.add_parser(
            name,
            help=help_text,
            description=help_text,
            formatter_class=FORMATTER,
        )
        add_common_workspace_arg(report_mode_parser)
    report_context_parser = report_subparsers.add_parser(
        "context-pack",
        help="Build a scene context pack.",
        description="Build a focused context pack for a specific scene_id.",
        epilog="Example:\n  novelctl report context-pack ./my-novel --scene scene-0002",
        formatter_class=FORMATTER,
    )
    add_common_workspace_arg(report_context_parser)
    report_context_parser.add_argument("--scene", required=True, dest="scene_id", help="Target scene_id.")
    return parser


def error_payload(exc: Exception) -> dict:
    if isinstance(exc, NovelCtlError):
        return exc.payload()
    return {"error": {"code": exc.__class__.__name__, "message": str(exc), "hint": "检查工作区结构、配置、命令参数和 runtime 状态。"}}


def resolve_retrieve_limit(workspace: Path, explicit_limit: int | None) -> int:
    if explicit_limit is not None:
        return explicit_limit
    config = load_config(workspace)
    retrieval = config.get("retrieval", {})
    if not isinstance(retrieval, dict):
        return 8
    return int(retrieval.get("default_limit", 8))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        workspace = Path(args.workspace) if hasattr(args, "workspace") else None
        if args.command == "init":
            result = init_workspace(Path(args.workspace), force=args.force, dry_run=args.dry_run)
        elif args.command == "sync":
            result = run_sync(Path(args.workspace), full=args.full, dry_run=args.dry_run)
        elif args.command == "check":
            result = run_check(Path(args.workspace), strict=args.strict)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            has_blocking = bool(result.get("errors")) or (args.strict and (result.get("warnings") or result.get("review_required")))
            return 1 if has_blocking else 0
        elif args.command == "retrieve":
            config = load_config(workspace)
            limit = resolve_retrieve_limit(workspace, args.limit)
            result = retrieve(
                workspace,
                args.mode,
                args.query,
                limit,
                config,
                run_sync,
                browse=getattr(args, "browse", False),
            )
        elif args.command == "archive" and args.archive_mode == "chapter":
            result = archive_chapter(Path(args.workspace), force=args.force, dry_run=args.dry_run)
        elif args.command == "archive" and args.archive_mode == "volume":
            result = archive_volume(Path(args.workspace), force=args.force, dry_run=args.dry_run)
        elif args.command == "status":
            result = status(Path(args.workspace), run_sync)
        elif args.command == "report" and args.report_mode == "summary":
            result = report_summary(Path(args.workspace), run_sync)
        elif args.command == "report" and args.report_mode == "context-pack":
            result = report_context_pack(Path(args.workspace), args.scene_id, run_sync)
        elif args.command == "report" and args.report_mode == "conflicts":
            result = report_conflicts(Path(args.workspace), run_sync)
        elif args.command == "report" and args.report_mode == "gates":
            result = report_gates(Path(args.workspace), run_sync)
        elif args.command == "report" and args.report_mode == "unresolved":
            result = report_unresolved(Path(args.workspace), run_sync)
        elif args.command == "report" and args.report_mode == "freshness":
            result = report_freshness(Path(args.workspace), run_sync)
        else:  # pragma: no cover
            parser.error("Unsupported command.")
            return 2
    except Exception as exc:
        payload = error_payload(exc)
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return exc.exit_code if isinstance(exc, NovelCtlError) else 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
