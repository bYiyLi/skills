from __future__ import annotations

import argparse
import json
import sys

from .broker import (
    broker_status,
    daemon_main,
    send_existing_request,
    send_request,
    stop_broker,
)
from .common import emit, fail, operation_lock
from .doctor import run_doctor


def _json_object(value: str) -> dict:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="browser",
        description=(
            "Persistent bridge to the installed Codex/OpenAI "
            "cua_repl Browser Runtime"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "doctor",
        help="Diagnose the local Codex/OpenAI Browser Runtime",
    )

    run = sub.add_parser(
        "run",
        help="Execute JavaScript in the persistent Browser Runtime context",
    )
    run.add_argument(
        "code",
        help="JavaScript executed by the cua_repl js tool",
    )
    run.add_argument(
        "--title",
        default="Browser JavaScript",
        help="Short Runtime tool-call title",
    )
    run.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="JavaScript tool timeout in milliseconds",
    )

    sub.add_parser(
        "reset",
        help="Reset JS bindings while keeping the broker and browser open",
    )
    sub.add_parser(
        "stop",
        help="End the Browser Runtime lifecycle and stop the broker",
    )
    return parser


def build_internal_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="browser-internal",
        add_help=False,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("_broker", add_help=False)

    resume = sub.add_parser("_resume")
    resume.add_argument("--operation", required=True)
    resume.add_argument(
        "--decision",
        choices=["accept", "decline"],
        required=True,
    )
    resume.add_argument(
        "--content-json",
        dest="content",
        type=_json_object,
    )

    cancel = sub.add_parser("_cancel")
    cancel.add_argument("--operation", required=True)
    return parser


def _emit_response(response: dict) -> int:
    emit(response)
    if response.get("code") == "ok":
        return 0
    if response.get("code") == "confirmation_required":
        return 2
    return 1


def _run_internal(argv: list[str]) -> int | None:
    if not argv or argv[0] not in {"_broker", "_resume", "_cancel"}:
        return None

    ns = build_internal_parser().parse_args(argv)
    if ns.command == "_broker":
        return daemon_main()

    status = broker_status()
    if not status.get("running"):
        fail(
            "operation_lost",
            "nexum-browser broker is not running",
            retryable=False,
        )

    if ns.command == "_resume":
        args = {
            "operation": ns.operation,
            "decision": ns.decision,
        }
        if ns.content is not None:
            args["content"] = ns.content
        try:
            response = send_existing_request(
                "_resume",
                args,
                timeout=180,
            )
        except Exception as exc:
            fail(
                "runtime_unavailable",
                str(exc),
                retryable=True,
            )
        return _emit_response(response)

    try:
        response = send_existing_request(
            "_cancel",
            {"operation": ns.operation},
            timeout=60,
        )
    except Exception as exc:
        fail(
            "runtime_unavailable",
            str(exc),
            retryable=True,
        )
    return _emit_response(response)


def main(argv: list[str] | None = None) -> int:
    argsv = list(sys.argv[1:] if argv is None else argv)
    internal = _run_internal(argsv)
    if internal is not None:
        return internal

    ns = build_parser().parse_args(argsv)

    if ns.command == "doctor":
        result = run_doctor()
        if result.get("healthy"):
            emit({"code": "ok", "data": result})
            return 0
        emit(
            {
                "code": "doctor_failed",
                "message": "One or more Browser Runtime health checks failed",
                "retryable": False,
                "data": result,
            }
        )
        return 1

    if ns.command == "stop":
        try:
            with operation_lock(timeout=60):
                stopped = stop_broker()
        except Exception as exc:
            fail(
                "runtime_release_failed",
                str(exc),
                retryable=True,
            )
        emit(
            {
                "code": "ok",
                "data": {
                    "stopped": stopped,
                    "alreadyStopped": not stopped,
                },
            }
        )
        return 0

    if ns.command == "reset":
        status = broker_status()
        if not status.get("running"):
            emit(
                {
                    "code": "ok",
                    "data": {
                        "reset": False,
                        "alreadyReset": True,
                    },
                }
            )
            return 0

        try:
            with operation_lock(timeout=75):
                response = send_existing_request(
                    "reset",
                    {},
                    timeout=60,
                )
        except Exception as exc:
            fail("reset_failed", str(exc), retryable=True)
        return _emit_response(response)

    timeout_ms = int(ns.timeout_ms)
    if timeout_ms <= 0:
        fail(
            "invalid_request",
            "--timeout-ms must be greater than zero",
            retryable=False,
        )
    broker = broker_status()
    startup_allowance = (
        150
        if not (
            broker.get("running")
            and broker.get("runtimeActive")
        )
        else 30
    )
    request_timeout = max(
        startup_allowance,
        timeout_ms / 1000 + 30,
    )

    try:
        with operation_lock(timeout=request_timeout + 15):
            response = send_request(
                "run",
                {
                    "code": ns.code,
                    "title": ns.title,
                    "timeoutMs": timeout_ms,
                },
                timeout=request_timeout,
            )
    except Exception as exc:
        fail(
            "runtime_unavailable",
            str(exc),
            retryable=True,
        )
    return _emit_response(response)


if __name__ == "__main__":
    raise SystemExit(main())
