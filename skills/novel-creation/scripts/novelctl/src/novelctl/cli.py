from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import archive_chapter, archive_volume, report_conflicts, report_context_pack, report_freshness, report_gates, report_summary, report_unresolved, retrieve, run_check, run_sync, status
from .workspace import init_workspace


def add_common_workspace_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("workspace", help="Novel workspace path.")


def error_payload(exc: Exception) -> dict:
    return {"error": {"code": exc.__class__.__name__, "message": str(exc), "hint": "检查工作区结构、配置和运行时索引状态。"}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="novelctl")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a novel workspace.")
    add_common_workspace_arg(init_parser)
    init_parser.add_argument("--force", action="store_true", help="Overwrite template files when possible.")
    init_parser.add_argument("--dry-run", action="store_true", help="Preview workspace initialization.")

    sync_parser = subparsers.add_parser("sync", help="Sync runtime manifests, indexes, and reports.")
    add_common_workspace_arg(sync_parser)
    sync_parser.add_argument("--full", action="store_true", help="Force a full rebuild.")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview sync changes.")

    check_parser = subparsers.add_parser("check", help="Run deterministic consistency checks.")
    add_common_workspace_arg(check_parser)
    check_parser.add_argument("--strict", action="store_true", help="Treat warnings and review_required as blocking in exit code.")

    retrieve_parser = subparsers.add_parser("retrieve", help="Run typed retrieval.")
    retrieve_subparsers = retrieve_parser.add_subparsers(dest="mode", required=True)
    for mode in ["text", "entity", "timeline", "plotline", "fact", "relation", "unresolved", "conflict-candidates"]:
        mode_parser = retrieve_subparsers.add_parser(mode)
        add_common_workspace_arg(mode_parser)
        mode_parser.add_argument("query", nargs="?", default="", help="Query string.")
        mode_parser.add_argument("--limit", type=int, default=8)

    archive_parser = subparsers.add_parser("archive", help="Archive scenes into chapters or chapters into volumes.")
    archive_subparsers = archive_parser.add_subparsers(dest="archive_mode", required=True)
    archive_chapter_parser = archive_subparsers.add_parser("chapter")
    add_common_workspace_arg(archive_chapter_parser)
    archive_chapter_parser.add_argument("--force", action="store_true")
    archive_chapter_parser.add_argument("--dry-run", action="store_true")
    archive_volume_parser = archive_subparsers.add_parser("volume")
    add_common_workspace_arg(archive_volume_parser)
    archive_volume_parser.add_argument("--force", action="store_true")
    archive_volume_parser.add_argument("--dry-run", action="store_true")

    status_parser = subparsers.add_parser("status", help="Show current status.")
    add_common_workspace_arg(status_parser)
    status_parser.add_argument("--json", action="store_true", help="Reserved for compatibility; output is JSON by default.")

    report_parser = subparsers.add_parser("report", help="Generate reports.")
    report_subparsers = report_parser.add_subparsers(dest="report_mode", required=True)
    for name in ["summary", "conflicts", "gates", "unresolved", "freshness"]:
        report_mode_parser = report_subparsers.add_parser(name)
        add_common_workspace_arg(report_mode_parser)
    report_context_parser = report_subparsers.add_parser("context-pack")
    add_common_workspace_arg(report_context_parser)
    report_context_parser.add_argument("--scene", required=True, dest="scene_id")

    args = parser.parse_args(argv)
    try:
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
            from .workspace import load_config

            result = retrieve(Path(args.workspace), args.mode, args.query, args.limit, load_config(Path(args.workspace)), run_sync)
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
        print(json.dumps(error_payload(exc), ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
