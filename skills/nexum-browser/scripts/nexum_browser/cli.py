from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

from .broker import (
    BrokerBusy,
    BrokerRequestOutcomeUnknown,
    BrokerRequestTimeout,
    BrokerRuntimeReleaseFailed,
    broker_status,
    daemon_main,
    send_existing_request,
    send_request,
    stop_broker,
)
from .common import emit, fail, operation_lock
from .doctor import run_doctor
from .runtime import (
    _BOOTSTRAP_ATTEMPTS,
    _DEFAULT_STARTUP_TIMEOUT,
    discover_launch_contract,
)


_WINDOWS_ARGV_SENTINEL = "__NEXUM_BROWSER_WINDOWS_ARGV__"
_WINDOWS_ARGV_ROOT_ENV = "NEXUM_BROWSER_ARGV_ROOT"
_WINDOWS_ARGV_FILE = re.compile(
    r"^nexum-browser-argv-[0-9a-f]{32}\.json$",
    re.IGNORECASE,
)


def _windows_argv_path(value: str, temp_root: str) -> Path:
    path = Path(value)
    try:
        in_temp_root = os.path.samefile(
            path.parent,
            temp_root,
        )
    except OSError:
        in_temp_root = False
    if (
        not in_temp_root
        or _WINDOWS_ARGV_FILE.fullmatch(path.name) is None
        or path.is_symlink()
    ):
        raise RuntimeError(
            "Windows launcher argv path is not a launcher-owned temp file"
        )
    return path


def _prepare_argv(argv: list[str]) -> list[str]:
    argsv = list(argv)
    if len(argsv) == 2 and argsv[0] == _WINDOWS_ARGV_SENTINEL:
        temp_root = os.environ.pop(_WINDOWS_ARGV_ROOT_ENV, None)
        if not temp_root:
            raise RuntimeError(
                f"{_WINDOWS_ARGV_ROOT_ENV} is unavailable for Windows launcher"
            )
        path = _windows_argv_path(argsv[1], temp_root)
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RuntimeError(
                f"Windows launcher argv file is unavailable: {exc}"
            ) from exc
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Windows launcher argv file is invalid JSON: {exc}"
            ) from exc
        if not isinstance(parsed, list) or not all(
            isinstance(item, str) for item in parsed
        ):
            raise RuntimeError(
                "Windows launcher argv file must contain a JSON string array"
            )
        argsv = parsed
    return argsv


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
    run.add_argument(
        "--no-startup-tab",
        action="store_true",
        help=(
            "Run only when an existing Runtime has already completed "
            "controlled-tab readiness; never create the bridge readiness tab"
        ),
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
    resume.add_argument("--elicitation", required=True)
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
    cancel.add_argument("--elicitation", required=True)
    return parser


def _emit_response(response: dict) -> int:
    emit(response)
    if response.get("code") == "ok":
        return 0
    if response.get("code") == "confirmation_required":
        return 2
    return 1


def _startup_timeout() -> float:
    try:
        return float(discover_launch_contract().startup_timeout)
    except Exception:
        return _DEFAULT_STARTUP_TIMEOUT


def _run_request_timeout(timeout_ms: int) -> float:
    execution = timeout_ms / 1000
    startup_timeout = _startup_timeout()
    return max(
        60.0,
        startup_timeout * (2 * _BOOTSTRAP_ATTEMPTS + 1)
        + execution * (_BOOTSTRAP_ATTEMPTS + 1)
        + 60.0,
    )


def _maintenance_request_timeout(tool_timeout: float) -> float:
    return max(
        60.0,
        _startup_timeout() + float(tool_timeout) + 30.0,
    )


def _continuation_request_timeout(status: dict) -> float:
    active = status.get("activeOperation")
    if not isinstance(active, dict):
        return 60.0
    try:
        timeout_ms = int(active.get("timeoutMs") or 0)
    except (TypeError, ValueError):
        timeout_ms = 0
    if timeout_ms <= 0:
        return 60.0
    return _run_request_timeout(timeout_ms)


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
            "elicitation": ns.elicitation,
            "decision": ns.decision,
        }
        if ns.content is not None:
            args["content"] = ns.content
        try:
            response = send_existing_request(
                "_resume",
                args,
                timeout=_continuation_request_timeout(status),
            )
        except BrokerRequestOutcomeUnknown as exc:
            fail(
                "run_outcome_unknown",
                str(exc),
                retryable=False,
                data={"outcomeUnknown": True},
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
            {
                "operation": ns.operation,
                "elicitation": ns.elicitation,
            },
            timeout=_continuation_request_timeout(status),
        )
    except BrokerRequestOutcomeUnknown as exc:
        fail(
            "run_outcome_unknown",
            str(exc),
            retryable=False,
            data={"outcomeUnknown": True},
        )
    except Exception as exc:
        fail(
            "runtime_unavailable",
            str(exc),
            retryable=True,
        )
    return _emit_response(response)


def main(argv: list[str] | None = None) -> int:
    try:
        argsv = _prepare_argv(
            list(sys.argv[1:] if argv is None else argv)
        )
    except RuntimeError as exc:
        fail(
            "invalid_request",
            str(exc),
            retryable=False,
        )
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
        request_timeout = _maintenance_request_timeout(15)
        try:
            with operation_lock(timeout=request_timeout + 15):
                stopped = stop_broker()
        except BrokerRequestOutcomeUnknown as exc:
            fail(
                "stop_outcome_unknown",
                str(exc),
                retryable=False,
                data=(
                    exc.data
                    if isinstance(exc.data, dict)
                    else {"outcomeUnknown": True}
                ),
            )
        except BrokerRuntimeReleaseFailed as exc:
            fail(
                "runtime_release_failed",
                str(exc),
                retryable=False,
                data=(
                    exc.data
                    if isinstance(exc.data, dict)
                    else {
                        "stopped": True,
                        "turnEnded": False,
                    }
                ),
            )
        except BrokerBusy as exc:
            fail(
                "broker_busy",
                str(exc),
                retryable=True,
            )
        except Exception as exc:
            fail(
                "stop_failed",
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
        request_timeout = _maintenance_request_timeout(30)
        try:
            with operation_lock(timeout=request_timeout + 15):
                status = broker_status()
                if not status.get("running"):
                    if not status.get("confirmedStopped"):
                        fail(
                            "reset_state_unknown",
                            (
                                "Cannot verify that the nexum-browser broker is "
                                "stopped; refusing to report reset completion"
                            ),
                            retryable=False,
                            data=status,
                        )
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
                response = send_existing_request(
                    "reset",
                    {},
                    timeout=request_timeout,
                )
        except BrokerRequestOutcomeUnknown as exc:
            fail(
                "reset_outcome_unknown",
                str(exc),
                retryable=False,
                data={"outcomeUnknown": True},
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
    request_timeout = _run_request_timeout(timeout_ms)

    try:
        with operation_lock(timeout=request_timeout + 15):
            broker = broker_status()
            if broker.get("unresponsive"):
                fail(
                    "broker_busy",
                    (
                        "nexum-browser broker is running but not responding; "
                        "an earlier operation may still be active"
                    ),
                    retryable=True,
                    data={"outcomeUnknown": True},
                )
            if ns.no_startup_tab and not (
                broker.get("running")
                and broker.get("runtimeActive")
                and broker.get("policyReady")
            ):
                fail(
                    "runtime_not_passive_ready",
                    (
                        "An existing Browser Runtime with completed controlled-tab "
                        "readiness is required by --no-startup-tab"
                    ),
                    retryable=False,
                    data={
                        "brokerRunning": bool(broker.get("running")),
                        "runtimeActive": bool(broker.get("runtimeActive")),
                        "policyReady": bool(broker.get("policyReady")),
                    },
                )
            request = (
                send_existing_request
                if ns.no_startup_tab
                else send_request
            )
            response = request(
                "run",
                {
                    "code": ns.code,
                    "title": ns.title,
                    "timeoutMs": timeout_ms,
                    "noStartupTab": bool(ns.no_startup_tab),
                },
                timeout=request_timeout,
            )
    except BrokerRequestOutcomeUnknown as exc:
        fail(
            "run_outcome_unknown",
            str(exc),
            retryable=False,
            data={"outcomeUnknown": True},
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
