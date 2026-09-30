from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from typing import Any

from .common import (
    BROKER_STATE_PATH,
    IDLE_SECONDS,
    LOG_PATH,
    PROXY_ENV_NAMES,
    REQUEST_TIMEOUT_SECONDS,
    RUNTIME_DIR,
    SKILL_ROOT,
)
from .mcp import McpRequestOutcomeUnknown
from .runtime import (
    _BOOTSTRAP_ATTEMPTS,
    _DEFAULT_STARTUP_TIMEOUT,
    CuaRuntime,
    CuaToolError,
    discover_launch_contract,
)


_STATE_VERSION = 1
_BROKER_PROTOCOL = 3
_MAX_MESSAGE_BYTES = 64 * 1024 * 1024
_RUN_COMPLETION_GRACE_SECONDS = 15.0
_WINDOWS_TASK_ENV_PATH = RUNTIME_DIR / "broker-task-env.json"


class BrokerRequestOutcomeUnknown(RuntimeError):
    """The broker may have received a request whose outcome is not known."""

    def __init__(
        self,
        message: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.data = data


class BrokerRequestTimeout(BrokerRequestOutcomeUnknown, TimeoutError):
    pass


class BrokerRuntimeReleaseFailed(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.data = data


class BrokerBusy(RuntimeError):
    pass


class ActiveOperation:
    def __init__(
        self,
        code: str,
        title: str,
        timeout_ms: int,
        completion_budget: float,
    ) -> None:
        self.id = "op_" + uuid.uuid4().hex
        self.code = code
        self.title = title
        self.timeout_ms = timeout_ms
        self.completion_budget = completion_budget
        self.state = "running"
        self.terminal_decision: str | None = None
        self.elicitation_id: str | None = None
        self.result: dict[str, Any] | None = None
        self.error: BaseException | None = None
        self.done = threading.Event()
        self.thread: threading.Thread | None = None
        self.deadline: float | None = None
        self.arm_deadline()

    def arm_deadline(self) -> None:
        self.deadline = time.monotonic() + self.completion_budget


class Broker:
    """Own one persistent cua_repl connection and one persistent JS context."""

    def __init__(self) -> None:
        self.runtime: CuaRuntime | None = None
        self.active_operation: ActiveOperation | None = None
        self._operation_lock = threading.Lock()
        self.stop_requested = False
        self.last_activity = time.monotonic()

    def ensure_runtime(self) -> CuaRuntime:
        if self.runtime is None:
            self.runtime = CuaRuntime()
        return self.runtime

    @staticmethod
    def _completion_budget(runtime: CuaRuntime, timeout_ms: int) -> float:
        execution = timeout_ms / 1000
        contract = getattr(runtime, "contract", None)
        startup_timeout = float(
            getattr(contract, "startup_timeout", 0.0) or 0.0
        )
        if runtime.policy_ready:
            return (
                startup_timeout
                + execution
                + _RUN_COMPLETION_GRACE_SECONDS
            )
        restart_budget = (
            2 * startup_timeout * max(0, _BOOTSTRAP_ATTEMPTS - 1)
        )
        return (
            startup_timeout
            + execution * (_BOOTSTRAP_ATTEMPTS + 1)
            + restart_budget
            + _RUN_COMPLETION_GRACE_SECONDS
        )

    def has_active_operation(self) -> bool:
        with self._operation_lock:
            return self.active_operation is not None

    def _operation_status_unlocked(self) -> dict[str, Any] | None:
        operation = self.active_operation
        if operation is None:
            return None
        return {
            "id": operation.id,
            "command": "run",
            "state": operation.state,
            "timeoutMs": operation.timeout_ms,
        }

    def _operation_status(self) -> dict[str, Any] | None:
        with self._operation_lock:
            return self._operation_status_unlocked()

    def _reconcile_withdrawn_confirmation(
        self,
    ) -> dict[str, Any] | None:
        with self._operation_lock:
            operation = self.active_operation
            if (
                operation is None
                or operation.state != "awaiting_confirmation"
            ):
                return None

        runtime = self.runtime
        pending = (
            runtime.pending_elicitation()
            if runtime is not None
            else None
        )
        if pending is not None:
            if operation.elicitation_id == pending.elicitation_id:
                return None
            operation.elicitation_id = pending.elicitation_id
            return {
                "code": "confirmation_required",
                "message": str(
                    pending.params.get("message")
                    or "Browser Runtime requires confirmation"
                ),
                "retryable": True,
                "data": {
                    "operationId": operation.id,
                    "elicitationId": pending.elicitation_id,
                    "request": pending.params,
                    "replacement": True,
                },
            }

        operation.state = "outcome_unknown"
        if runtime is not None:
            with contextlib.suppress(Exception):
                runtime.close()
            if self.runtime is runtime:
                self.runtime = None
        operation.done.wait(2)
        with self._operation_lock:
            if self.active_operation is operation:
                self.active_operation = None
        return {
            "code": "run_outcome_unknown",
            "message": (
                "Browser Runtime confirmation was withdrawn before a "
                "continuation completed; inspect browser state before retrying"
            ),
            "retryable": False,
            "data": {
                "operationId": operation.id,
                "outcomeUnknown": True,
                "confirmationWithdrawn": True,
                "runtimeDiscarded": runtime is not None,
            },
        }

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        command = str(request.get("command") or "")
        args = request.get("args") or {}
        if not isinstance(args, dict):
            return {
                "code": "invalid_request",
                "message": "Broker args must be an object",
                "retryable": False,
            }

        if command == "__ping__":
            return {
                "code": "ok",
                "data": {
                    "running": True,
                    "brokerProtocol": _BROKER_PROTOCOL,
                    "runtimeActive": self.runtime is not None,
                    "runtimeBackend": (
                        self.runtime.backend if self.runtime is not None else None
                    ),
                    "bootstrapped": (
                        self.runtime.bootstrapped
                        if self.runtime is not None
                        else False
                    ),
                    "policyReady": (
                        self.runtime.policy_ready
                        if self.runtime is not None
                        else False
                    ),
                    "activeOperation": self._operation_status(),
                },
            }

        if command == "__stop__":
            with self._operation_lock:
                active = self.active_operation
                if (
                    active is not None
                    and active.state != "awaiting_confirmation"
                ):
                    return {
                        "code": "broker_busy",
                        "message": "A browser run operation is still active",
                        "retryable": True,
                        "data": {
                            "activeOperation": self._operation_status_unlocked()
                        },
                    }
            paused_operation = (
                active
                if active is not None
                and active.state == "awaiting_confirmation"
                else None
            )
            try:
                self._shutdown_runtime()
            except McpRequestOutcomeUnknown as exc:
                self.stop_requested = True
                data = {"outcomeUnknown": True}
                if paused_operation is not None:
                    data.update(
                        {
                            "activeRunOutcomeUnknown": True,
                            "operationId": paused_operation.id,
                        }
                    )
                return {
                    "code": "stop_outcome_unknown",
                    "message": str(exc),
                    "retryable": False,
                    "data": data,
                }
            except Exception as exc:
                self.stop_requested = True
                data = {
                    "stopped": True,
                    "turnEnded": False,
                }
                if paused_operation is not None:
                    data.update(
                        {
                            "activeRunOutcomeUnknown": True,
                            "operationId": paused_operation.id,
                            "outcomeUnknown": True,
                        }
                    )
                return {
                    "code": "runtime_release_failed",
                    "message": str(exc),
                    "retryable": False,
                    "data": data,
                }
            self.stop_requested = True
            if paused_operation is not None:
                return {
                    "code": "stop_outcome_unknown",
                    "message": (
                        "Browser Runtime stopped and turn_ended completed, "
                        "but the previously paused run outcome is unknown"
                    ),
                    "retryable": False,
                    "data": {
                        "stopped": True,
                        "turnEnded": True,
                        "activeRunOutcomeUnknown": True,
                        "operationId": paused_operation.id,
                        "outcomeUnknown": True,
                    },
                }
            return {"code": "ok", "data": {"stopped": True}}

        self.last_activity = time.monotonic()

        withdrawn = self._reconcile_withdrawn_confirmation()
        if withdrawn is not None:
            return withdrawn

        if command == "_resume":
            return self._resume_operation(args)
        if command == "_cancel":
            return self._cancel_operation(args)
        if command == "reset":
            return self._reset()
        if command == "run":
            return self._start_run(args)

        return {
            "code": "invalid_request",
            "message": f"Unsupported broker command: {command}",
            "retryable": False,
        }

    def _reset(self) -> dict[str, Any]:
        with self._operation_lock:
            if self.active_operation is not None:
                return {
                    "code": "broker_busy",
                    "message": "A browser run operation is still active",
                    "retryable": True,
                    "data": {
                        "activeOperation": self._operation_status_unlocked()
                    },
                }

        if self.runtime is None:
            return {
                "code": "ok",
                "data": {"reset": False, "alreadyReset": True},
            }

        try:
            result = self.runtime.reset()
        except McpRequestOutcomeUnknown as exc:
            runtime = self.runtime
            with contextlib.suppress(Exception):
                runtime.close()
            if self.runtime is runtime:
                self.runtime = None
            return {
                "code": "reset_outcome_unknown",
                "message": str(exc),
                "retryable": False,
                "data": {
                    "outcomeUnknown": True,
                    "runtimeDiscarded": True,
                },
            }
        except Exception as exc:
            runtime = self.runtime
            with contextlib.suppress(Exception):
                runtime.close()
            if self.runtime is runtime:
                self.runtime = None
            return {
                "code": "reset_state_unknown",
                "message": str(exc),
                "retryable": False,
                "data": {
                    "stateUnknown": True,
                    "runtimeDiscarded": True,
                },
            }
        return {
            "code": "ok",
            "data": {
                "reset": True,
                "alreadyReset": False,
                "result": result,
            },
        }

    def _start_run(self, args: dict[str, Any]) -> dict[str, Any]:
        code = args.get("code")
        title = str(args.get("title") or "Browser JavaScript")
        try:
            timeout_ms = int(args.get("timeoutMs") or 30000)
        except (TypeError, ValueError):
            return {
                "code": "invalid_request",
                "message": "timeoutMs must be an integer",
                "retryable": False,
            }

        if not isinstance(code, str) or not code.strip():
            return {
                "code": "invalid_request",
                "message": "browser run requires non-empty JavaScript",
                "retryable": False,
            }
        if timeout_ms <= 0:
            return {
                "code": "invalid_request",
                "message": "timeoutMs must be greater than zero",
                "retryable": False,
            }

        no_startup_tab = bool(args.get("noStartupTab"))

        with self._operation_lock:
            if self.active_operation is not None:
                return {
                    "code": "broker_busy",
                    "message": "Another browser run operation is still active",
                    "retryable": True,
                    "data": {
                        "activeOperation": self._operation_status_unlocked()
                    },
                }

        runtime = self.runtime
        if no_startup_tab:
            if runtime is None or not runtime.policy_ready:
                return {
                    "code": "runtime_not_passive_ready",
                    "message": (
                        "An existing Browser Runtime with completed "
                        "controlled-tab readiness is required"
                    ),
                    "retryable": False,
                }
        else:
            try:
                runtime = self.ensure_runtime()
            except Exception as exc:
                return {
                    "code": "runtime_unavailable",
                    "message": str(exc),
                    "retryable": True,
                }
        assert runtime is not None

        operation = ActiveOperation(
            code,
            title,
            timeout_ms,
            self._completion_budget(runtime, timeout_ms),
        )
        with self._operation_lock:
            if self.active_operation is not None:
                return {
                    "code": "broker_busy",
                    "message": "Another browser run operation is still active",
                    "retryable": True,
                    "data": {
                        "activeOperation": self._operation_status_unlocked()
                    },
                }
            self.active_operation = operation

        def run() -> None:
            try:
                operation.result = runtime.run(
                    operation.code,
                    title=operation.title,
                    timeout_ms=operation.timeout_ms,
                )
            except BaseException as exc:
                operation.error = exc
            finally:
                operation.done.set()

        operation.thread = threading.Thread(
            target=run,
            name=f"nexum-browser-operation-{operation.id}",
            daemon=True,
        )
        operation.thread.start()
        return self._wait_for_operation(operation)

    def _wait_for_operation(
        self,
        operation: ActiveOperation,
    ) -> dict[str, Any]:
        while True:
            if operation.done.wait(0.05):
                with self._operation_lock:
                    if self.active_operation is operation:
                        self.active_operation = None

                if operation.error is not None:
                    if isinstance(
                        operation.error,
                        McpRequestOutcomeUnknown,
                    ):
                        runtime = self.runtime
                        if runtime is not None:
                            with contextlib.suppress(Exception):
                                runtime.close()
                            if self.runtime is runtime:
                                self.runtime = None
                        return {
                            "code": "run_outcome_unknown",
                            "message": str(operation.error),
                            "retryable": False,
                            "data": {
                                "operationId": operation.id,
                                "outcomeUnknown": True,
                                "runtimeDiscarded": runtime is not None,
                            },
                        }

                if (
                    operation.terminal_decision is not None
                    and operation.result is not None
                    and operation.error is None
                ):
                    return {
                        "code": "run_outcome_unknown",
                        "message": (
                            "Browser Runtime returned a successful result after "
                            "the confirmation was declined or cancelled"
                        ),
                        "retryable": False,
                        "data": {
                            "operationId": operation.id,
                            "confirmationDecision": operation.terminal_decision,
                            "outcomeUnknown": True,
                            "result": operation.result,
                        },
                    }

                if operation.terminal_decision is not None:
                    response = {
                        "code": (
                            "operation_declined"
                            if operation.terminal_decision == "decline"
                            else "operation_cancelled"
                        ),
                        "message": (
                            "Browser Runtime confirmation was declined"
                            if operation.terminal_decision == "decline"
                            else "Browser Runtime operation was cancelled"
                        ),
                        "retryable": False,
                    }
                    if isinstance(operation.error, CuaToolError):
                        response["data"] = operation.error.result
                    elif operation.result is not None:
                        response["data"] = operation.result
                    return response

                if operation.error is not None:
                    response = {
                        "code": "run_failed",
                        "message": str(operation.error),
                        "retryable": False,
                    }
                    if isinstance(operation.error, CuaToolError):
                        response["data"] = operation.error.result
                    return response

                return {
                    "code": "ok",
                    "data": operation.result or {},
                }

            runtime = self.runtime
            if runtime is None:
                continue
            elicitation = runtime.pending_elicitation()
            if elicitation is not None:
                operation.state = "awaiting_confirmation"
                operation.elicitation_id = elicitation.elicitation_id
                operation.deadline = None
                return {
                    "code": "confirmation_required",
                    "message": str(
                        elicitation.params.get("message")
                        or "Browser Runtime requires confirmation"
                    ),
                    "retryable": True,
                    "data": {
                        "operationId": operation.id,
                        "elicitationId": elicitation.elicitation_id,
                        "request": elicitation.params,
                    },
                }

            if (
                operation.deadline is not None
                and time.monotonic() >= operation.deadline
                and not operation.done.is_set()
            ):
                operation.state = "outcome_unknown"
                with contextlib.suppress(Exception):
                    runtime.close()
                if self.runtime is runtime:
                    self.runtime = None
                operation.done.wait(2)
                with self._operation_lock:
                    if self.active_operation is operation:
                        self.active_operation = None
                return {
                    "code": "run_outcome_unknown",
                    "message": (
                        "Browser Runtime did not report completion before the "
                        "broker deadline; inspect current browser state before "
                        "retrying"
                    ),
                    "retryable": False,
                    "data": {
                        "operationId": operation.id,
                        "outcomeUnknown": True,
                        "runtimeDiscarded": True,
                    },
                }

    def _resume_operation(self, args: dict[str, Any]) -> dict[str, Any]:
        operation_id = str(args.get("operation") or "")
        elicitation_id = str(args.get("elicitation") or "")
        decision = str(args.get("decision") or "")
        content = args.get("content")

        if decision not in {"accept", "decline"}:
            return {
                "code": "invalid_request",
                "message": "decision must be accept or decline",
                "retryable": False,
            }
        if content is not None and not isinstance(content, dict):
            return {
                "code": "invalid_request",
                "message": "Elicitation content must be a JSON object",
                "retryable": False,
            }

        with self._operation_lock:
            operation = self.active_operation
            if operation is None or operation.id != operation_id:
                return {
                    "code": "operation_lost",
                    "message": f"Active operation was not found: {operation_id}",
                    "retryable": False,
                }
            if operation.state != "awaiting_confirmation":
                return {
                    "code": "invalid_operation_state",
                    "message": (
                        "Operation is not awaiting confirmation: "
                        f"{operation.state}"
                    ),
                    "retryable": False,
                }

        runtime = self.runtime
        if runtime is None:
            return {
                "code": "operation_lost",
                "message": "Browser Runtime is no longer available",
                "retryable": False,
            }
        elicitation = runtime.pending_elicitation()
        if elicitation is None:
            return {
                "code": "operation_lost",
                "message": "Pending Browser Runtime confirmation was lost",
                "retryable": False,
            }
        if elicitation.elicitation_id != elicitation_id:
            return {
                "code": "elicitation_mismatch",
                "message": (
                    "The supplied elicitation no longer matches the pending "
                    "Browser Runtime confirmation"
                ),
                "retryable": False,
            }

        try:
            runtime.respond_elicitation(
                elicitation_id,
                action=decision,
                content=content,
            )
        except McpRequestOutcomeUnknown as exc:
            operation.state = "outcome_unknown"
            with contextlib.suppress(Exception):
                runtime.close()
            if self.runtime is runtime:
                self.runtime = None
            operation.done.wait(2)
            with self._operation_lock:
                if self.active_operation is operation:
                    self.active_operation = None
            return {
                "code": "run_outcome_unknown",
                "message": str(exc),
                "retryable": False,
                "data": {
                    "operationId": operation.id,
                    "outcomeUnknown": True,
                    "runtimeDiscarded": True,
                },
            }
        except Exception as exc:
            return {
                "code": "runtime_unavailable",
                "message": str(exc),
                "retryable": True,
            }

        if decision == "accept":
            operation.state = "running"
            operation.elicitation_id = None
        else:
            operation.terminal_decision = "decline"
            operation.elicitation_id = None
            operation.state = "cancelled"
        operation.completion_budget = self._completion_budget(
            runtime,
            operation.timeout_ms,
        )
        operation.arm_deadline()
        return self._wait_for_operation(operation)

    def _cancel_operation(self, args: dict[str, Any]) -> dict[str, Any]:
        operation_id = str(args.get("operation") or "")
        elicitation_id = str(args.get("elicitation") or "")
        with self._operation_lock:
            operation = self.active_operation
            if operation is None or operation.id != operation_id:
                return {
                    "code": "operation_lost",
                    "message": f"Active operation was not found: {operation_id}",
                    "retryable": False,
                }
            if operation.state != "awaiting_confirmation":
                return {
                    "code": "operation_not_cancellable",
                    "message": (
                        "Only an operation awaiting Browser Runtime "
                        "confirmation can be cancelled"
                    ),
                    "retryable": False,
                }

        runtime = self.runtime
        if runtime is None:
            return {
                "code": "operation_lost",
                "message": "Browser Runtime is no longer available",
                "retryable": False,
            }
        elicitation = runtime.pending_elicitation()
        if elicitation is None:
            return {
                "code": "operation_lost",
                "message": "Pending Browser Runtime confirmation was lost",
                "retryable": False,
            }
        if elicitation.elicitation_id != elicitation_id:
            return {
                "code": "elicitation_mismatch",
                "message": (
                    "The supplied elicitation no longer matches the pending "
                    "Browser Runtime confirmation"
                ),
                "retryable": False,
            }

        try:
            runtime.respond_elicitation(
                elicitation_id,
                action="cancel",
            )
        except McpRequestOutcomeUnknown as exc:
            operation.state = "outcome_unknown"
            with contextlib.suppress(Exception):
                runtime.close()
            if self.runtime is runtime:
                self.runtime = None
            operation.done.wait(2)
            with self._operation_lock:
                if self.active_operation is operation:
                    self.active_operation = None
            return {
                "code": "run_outcome_unknown",
                "message": str(exc),
                "retryable": False,
                "data": {
                    "operationId": operation.id,
                    "outcomeUnknown": True,
                    "runtimeDiscarded": True,
                },
            }
        except Exception as exc:
            return {
                "code": "runtime_unavailable",
                "message": str(exc),
                "retryable": True,
            }

        operation.terminal_decision = "cancel"
        operation.elicitation_id = None
        operation.state = "cancelled"
        operation.completion_budget = self._completion_budget(
            runtime,
            operation.timeout_ms,
        )
        operation.arm_deadline()
        return self._wait_for_operation(operation)

    def _cancel_pending_elicitation(self) -> None:
        runtime = self.runtime
        if runtime is None:
            return
        elicitation = runtime.pending_elicitation()
        if elicitation is None:
            return

        with self._operation_lock:
            operation = self.active_operation
            if (
                operation is not None
                and operation.state == "awaiting_confirmation"
            ):
                operation.terminal_decision = "cancel"
                operation.elicitation_id = None
                operation.state = "cancelled"

        with contextlib.suppress(Exception):
            runtime.respond_elicitation(
                elicitation.elicitation_id,
                action="cancel",
            )

    def _shutdown_runtime(self) -> None:
        runtime = self.runtime
        if runtime is None:
            return

        with self._operation_lock:
            active = self.active_operation
        self._cancel_pending_elicitation()
        if active is not None and active.state == "cancelled":
            active.done.wait(2)

        release_error: BaseException | None = None
        try:
            runtime.release()
        except BaseException as exc:
            release_error = exc
        finally:
            runtime.close()
            self.runtime = None
            with self._operation_lock:
                if self.active_operation is active:
                    self.active_operation = None

        if release_error is not None:
            raise release_error

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._shutdown_runtime()


def _recv_line(conn: socket.socket, timeout: float) -> bytes:
    conn.settimeout(timeout)
    data = bytearray()
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > _MAX_MESSAGE_BYTES:
            raise RuntimeError(
                "nexum-browser broker message exceeded the supported size"
            )
        if b"\n" in chunk:
            break
    return bytes(data).split(b"\n", 1)[0]


def _load_state() -> dict[str, Any]:
    try:
        value = json.loads(BROKER_STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(value, dict) or value.get("version") != _STATE_VERSION:
        return {}
    try:
        port = int(value.get("port") or 0)
        pid = int(value.get("pid") or 0)
    except (TypeError, ValueError):
        return {}
    token = value.get("token")
    if not (
        1 <= port <= 65535
        and pid > 0
        and isinstance(token, str)
        and len(token) >= 32
    ):
        return {}
    value["port"] = port
    value["pid"] = pid
    return value


def _secure_windows_state_file(path: Path) -> None:
    if os.name != "nt":
        return

    username = os.environ.get("USERNAME")
    if not username:
        raise RuntimeError(
            "USERNAME is unavailable; cannot secure nexum-browser broker state"
        )
    domain = os.environ.get("USERDOMAIN")
    principal = f"{domain}\\{username}" if domain else username
    result = subprocess.run(
        [
            "icacls",
            str(path),
            "/inheritance:r",
            "/grant:r",
            f"{principal}:F",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise RuntimeError(
            message
            or "Unable to restrict nexum-browser broker state permissions"
        )


def _save_state(value: dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BROKER_STATE_PATH.with_name(
        f"{BROKER_STATE_PATH.name}.{uuid.uuid4().hex}.tmp"
    )
    try:
        tmp.write_text(
            json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        with contextlib.suppress(OSError):
            os.chmod(tmp, 0o600)
        _secure_windows_state_file(tmp)
        os.replace(tmp, BROKER_STATE_PATH)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def _clear_state_if_token(token: str) -> None:
    state = _load_state()
    if state.get("token") != token:
        return
    with contextlib.suppress(FileNotFoundError):
        BROKER_STATE_PATH.unlink()


def _windows_task_name() -> str:
    user = (
        f"{os.environ.get('USERDOMAIN', '')}\\"
        f"{os.environ.get('USERNAME', '')}"
    )
    digest = hashlib.sha256(
        f"{user}|{SKILL_ROOT}".encode("utf-8", errors="replace")
    ).hexdigest()[:16]
    return f"NexumBrowserBroker-{digest}"


def _powershell_executable() -> str:
    system_root = os.environ.get("SystemRoot") or r"C:\Windows"
    candidate = (
        Path(system_root)
        / "System32/WindowsPowerShell/v1.0/powershell.exe"
    )
    if candidate.is_file():
        return str(candidate)
    return "powershell.exe"


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_windows_task_script(
    script: str,
    *,
    timeout: float = 30,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _powershell_executable(),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _windows_task_running() -> bool | None:
    if os.name != "nt":
        return False
    task_name = _windows_task_name()
    script = (
        "$ErrorActionPreference='Stop';"
        f"$name={_ps_quote(task_name)};"
        "$task=Get-ScheduledTask -TaskName $name "
        "-ErrorAction SilentlyContinue;"
        "if(!$task){Write-Output 'missing';exit 0};"
        "if($task.State -eq 'Running'){Write-Output 'running';exit 0};"
        "Write-Output 'stopped'"
    )
    try:
        result = _run_windows_task_script(script, timeout=10)
    except Exception:
        return None
    if result.returncode != 0:
        return None
    task_state = (result.stdout or "").strip().lower()
    if task_state == "running":
        return True
    if task_state in {"missing", "stopped"}:
        return False
    return None


def _maintenance_request_timeout(tool_timeout: float) -> float:
    try:
        startup_timeout = float(
            discover_launch_contract().startup_timeout
        )
    except Exception:
        startup_timeout = _DEFAULT_STARTUP_TIMEOUT
    return (
        startup_timeout
        + float(tool_timeout)
        + _RUN_COMPLETION_GRACE_SECONDS
    )


def _remove_windows_task() -> None:
    if os.name != "nt":
        return

    task_name = _windows_task_name()
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        "$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
        f"$name={_ps_quote(task_name)};"
        "$task=Get-ScheduledTask -TaskName $name "
        "-ErrorAction SilentlyContinue;"
        "if($task){"
        "if($task.State -eq 'Running'){"
        "Stop-ScheduledTask -TaskName $name "
        "-ErrorAction SilentlyContinue};"
        "Unregister-ScheduledTask -TaskName $name "
        "-Confirm:$false -ErrorAction SilentlyContinue"
        "}"
    )
    with contextlib.suppress(Exception):
        _run_windows_task_script(script, timeout=20)
    with contextlib.suppress(FileNotFoundError):
        _WINDOWS_TASK_ENV_PATH.unlink()


def _write_windows_task_environment() -> None:
    env: dict[str, str | None] = {}
    for name in (
        "CODEX_HOME",
        "NEXUM_BROWSER_CUA_MCP",
        "NEXUM_BROWSER_IDLE_SECONDS",
        "NEXUM_BROWSER_REQUEST_TIMEOUT_SECONDS",
        "NEXUM_BROWSER_LOCK_STALE_SECONDS",
    ):
        value = os.environ.get(name)
        if value:
            env[name] = value
    for name in PROXY_ENV_NAMES:
        env[name] = os.environ.get(name)

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _WINDOWS_TASK_ENV_PATH.with_name(
        f"{_WINDOWS_TASK_ENV_PATH.name}.{uuid.uuid4().hex}.tmp"
    )
    try:
        tmp.write_text(
            json.dumps(env, ensure_ascii=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        _secure_windows_state_file(tmp)
        os.replace(tmp, _WINDOWS_TASK_ENV_PATH)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def _spawn_windows_task() -> None:
    task_name = _windows_task_name()
    launcher = Path(__file__).resolve().parents[1] / "browser_task.py"

    _remove_windows_task()
    _write_windows_task_environment()

    argument = subprocess.list2cmdline([str(launcher)])
    script = (
        "$ErrorActionPreference='Stop';"
        "$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
        f"$name={_ps_quote(task_name)};"
        f"$exe={_ps_quote(sys.executable)};"
        f"$arg={_ps_quote(argument)};"
        f"$cwd={_ps_quote(str(SKILL_ROOT))};"
        "$user=[System.Security.Principal.WindowsIdentity]"
        "::GetCurrent().Name;"
        "$action=New-ScheduledTaskAction -Execute $exe "
        "-Argument $arg -WorkingDirectory $cwd;"
        "$principal=New-ScheduledTaskPrincipal -UserId $user "
        "-LogonType Interactive -RunLevel Limited;"
        "$settings=New-ScheduledTaskSettingsSet "
        "-ExecutionTimeLimit (New-TimeSpan -Seconds 0) "
        "-MultipleInstances IgnoreNew;"
        "Register-ScheduledTask -TaskName $name -Action $action "
        "-Principal $principal -Settings $settings -Force | Out-Null;"
        "Start-ScheduledTask -TaskName $name"
    )
    result = _run_windows_task_script(script, timeout=30)
    if result.returncode != 0:
        with contextlib.suppress(FileNotFoundError):
            _WINDOWS_TASK_ENV_PATH.unlink()
        message = (result.stderr or result.stdout).strip()
        raise RuntimeError(
            message
            or "Unable to start nexum-browser broker through Windows Task Scheduler"
        )


def _request(
    state: dict[str, Any],
    command: str,
    args: dict[str, Any],
    *,
    timeout: float,
) -> dict[str, Any]:
    payload = json.dumps(
        {
            "token": state["token"],
            "command": command,
            "args": args,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"

    may_have_dispatched = False
    try:
        with socket.create_connection(
            ("127.0.0.1", int(state["port"])),
            timeout=timeout,
        ) as conn:
            may_have_dispatched = True
            conn.sendall(payload)
            conn.shutdown(socket.SHUT_WR)
            raw = _recv_line(conn, timeout)
    except TimeoutError as exc:
        if may_have_dispatched:
            raise BrokerRequestTimeout(
                "Timed out waiting for nexum-browser after request dispatch; "
                "the operation outcome may be unknown"
            ) from exc
        raise
    except OSError as exc:
        if may_have_dispatched:
            raise BrokerRequestOutcomeUnknown(
                "Lost nexum-browser transport after request dispatch; "
                "the operation outcome may be unknown"
            ) from exc
        raise
    except Exception as exc:
        if may_have_dispatched:
            raise BrokerRequestOutcomeUnknown(
                "Unable to read nexum-browser response after request dispatch; "
                "the operation outcome may be unknown"
            ) from exc
        raise

    if not raw:
        raise BrokerRequestOutcomeUnknown(
            "nexum-browser returned no response after request dispatch; "
            "the operation outcome may be unknown"
        )
    try:
        response = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BrokerRequestOutcomeUnknown(
            "nexum-browser returned invalid data after request dispatch; "
            "the operation outcome may be unknown"
        ) from exc
    if not isinstance(response, dict):
        raise BrokerRequestOutcomeUnknown(
            "nexum-browser returned an invalid response after request dispatch; "
            "the operation outcome may be unknown"
        )
    code = response.get("code")
    if not isinstance(code, str) or not code:
        raise BrokerRequestOutcomeUnknown(
            "nexum-browser returned a response without a valid code; "
            "the operation outcome may be unknown"
        )
    if code in {"ok", "confirmation_required"} and not isinstance(
        response.get("data"),
        dict,
    ):
        raise BrokerRequestOutcomeUnknown(
            "nexum-browser returned an incomplete success response; "
            "the operation outcome may be unknown"
        )
    data = response.get("data")
    if code == "confirmation_required":
        if not (
            isinstance(data.get("operationId"), str)
            and data.get("operationId")
            and isinstance(data.get("elicitationId"), str)
            and data.get("elicitationId")
        ):
            raise BrokerRequestOutcomeUnknown(
                "nexum-browser returned an incomplete confirmation response; "
                "the operation outcome may be unknown"
            )
    elif code == "ok":
        if command in {"run", "_resume"} and not (
            isinstance(data.get("content"), list)
            and (
                "isError" not in data
                or isinstance(data.get("isError"), bool)
            )
        ):
            raise BrokerRequestOutcomeUnknown(
                "nexum-browser returned an incomplete run result; "
                "the operation outcome may be unknown"
            )
        if command == "__ping__" and not isinstance(
            data.get("brokerProtocol"),
            int,
        ):
            raise BrokerRequestOutcomeUnknown(
                "nexum-browser returned an incomplete ping response"
            )
        if command == "reset" and not isinstance(data.get("reset"), bool):
            raise BrokerRequestOutcomeUnknown(
                "nexum-browser returned an incomplete reset response; "
                "the operation outcome may be unknown"
            )
        if command == "__stop__" and data.get("stopped") is not True:
            raise BrokerRequestOutcomeUnknown(
                "nexum-browser returned an incomplete stop response; "
                "the operation outcome may be unknown"
            )
    return response


def _ping_response(
    state: dict[str, Any],
    *,
    timeout: float = 0.75,
) -> dict[str, Any] | None:
    if not state:
        return None
    try:
        response = _request(state, "__ping__", {}, timeout=timeout)
    except Exception:
        return None
    return response if response.get("code") == "ok" else None


def _compatible_ping(response: dict[str, Any] | None) -> bool:
    if response is None:
        return False
    data = response.get("data")
    return (
        isinstance(data, dict)
        and data.get("brokerProtocol") == _BROKER_PROTOCOL
    )


def _state_process_alive(state: dict[str, Any]) -> bool | None:
    try:
        pid = int(state.get("pid") or 0)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False

    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                if int(kernel32.GetLastError()) == 87:
                    return False
                return None
            try:
                exit_code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(
                    handle,
                    ctypes.byref(exit_code),
                ):
                    return None
                return exit_code.value == 259
            finally:
                kernel32.CloseHandle(handle)
        except Exception:
            return None

    pids = _unix_broker_pids()
    if pids is None:
        return None
    return pid in pids


def _unix_broker_pids(
    entry: str | None = None,
) -> list[int] | None:
    if os.name == "nt":
        return []
    entry = entry or str(
        Path(__file__).resolve().parents[1] / "browser"
    )
    try:
        result = subprocess.run(
            ["ps", "-ww", "-axo", "pid=,command="],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None

    pids: list[int] = []
    for line in (result.stdout or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pid_text, _, command = stripped.partition(" ")
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if command.rstrip().endswith(f"{entry} _broker"):
            pids.append(pid)
    return pids


def broker_status() -> dict[str, Any]:
    state = _load_state()
    if not state:
        if os.name == "nt":
            task_running = _windows_task_running()
            if task_running is not False:
                return {
                    "running": False,
                    "stateUncertain": True,
                    "taskRunning": task_running is True,
                }
        else:
            pids = _unix_broker_pids()
            if pids is None:
                return {"running": False, "stateUncertain": True}
            if pids:
                return {
                    "running": True,
                    "unresponsive": True,
                    "stateUncertain": True,
                    "pids": pids,
                }
        return {"running": False, "confirmedStopped": True}

    response = _ping_response(state)
    if response is None:
        if os.name == "nt" and _windows_task_running() is False:
            return {
                "running": False,
                "staleState": True,
                "confirmedStopped": True,
                "pid": state.get("pid"),
            }
        alive = _state_process_alive(state)
        if alive is not False:
            status = {
                "running": True,
                "unresponsive": True,
                "pid": state.get("pid"),
            }
            if alive is None:
                status["livenessUnknown"] = True
            return status
        status = {
            "running": False,
            "staleState": True,
            "pid": state.get("pid"),
        }
        if os.name == "nt":
            task_running = _windows_task_running()
            if task_running is not False:
                status["stateUncertain"] = True
                status["taskRunning"] = task_running is True
                return status
        status["confirmedStopped"] = True
        return status

    data = response.get("data")
    if not isinstance(data, dict) or not _compatible_ping(response):
        return {
            "running": False,
            "incompatibleProtocol": True,
            "stateUncertain": True,
            "pid": state.get("pid"),
        }

    return {
        "running": True,
        "pid": state["pid"],
        "port": state["port"],
        "startedAt": state.get("startedAt"),
        "brokerProtocol": data.get("brokerProtocol"),
        "runtimeActive": bool(data.get("runtimeActive")),
        "runtimeBackend": data.get("runtimeBackend"),
        "bootstrapped": bool(data.get("bootstrapped")),
        "policyReady": bool(data.get("policyReady")),
        "activeOperation": data.get("activeOperation"),
    }


def _spawn() -> subprocess.Popen[Any] | None:
    entry = Path(__file__).resolve().parents[1] / "browser"
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        _spawn_windows_task()
        return None

    log = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
    kwargs: dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": log,
        "stderr": log,
        "cwd": str(SKILL_ROOT),
        "close_fds": True,
        "start_new_session": True,
    }
    try:
        return subprocess.Popen(
            [sys.executable, str(entry), "_broker"],
            **kwargs,
        )
    finally:
        log.close()


def ensure_broker() -> dict[str, Any]:
    state = _load_state()
    if not state and os.name != "nt":
        pids = _unix_broker_pids()
        if pids is None:
            raise RuntimeError(
                "Cannot determine whether a nexum-browser broker is already "
                "running; refusing to start a second broker"
            )
        if pids:
            raise RuntimeError(
                "A nexum-browser broker appears to be running without state; "
                "refusing to start a second broker"
            )
    if state:
        ping = _ping_response(state)
        if _compatible_ping(ping):
            return state
        if ping is not None:
            raise RuntimeError(
                "An incompatible nexum-browser broker is responding; "
                "refusing automatic replacement. Stop it explicitly after "
                "resolving any active operation."
            )
        elif not (
            os.name == "nt" and _windows_task_running() is False
        ) and _state_process_alive(state) is not False:
            raise RuntimeError(
                "The nexum-browser broker is running but not responding; "
                "refusing to replace it while an operation may still be active"
            )
        _clear_state_if_token(str(state.get("token") or ""))

    if os.name == "nt":
        task_running = _windows_task_running()
        if task_running is not False:
            raise RuntimeError(
                "Windows nexum-browser broker task may still be running "
                "but broker state is unavailable; refusing to replace it"
            )
        _remove_windows_task()

    process = _spawn()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(
                "nexum-browser broker exited during startup with code "
                f"{process.returncode}; see {LOG_PATH}"
            )
        state = _load_state()
        if state and _compatible_ping(_ping_response(state)):
            return state
        time.sleep(0.05)

    if process is not None:
        with contextlib.suppress(Exception):
            process.terminate()
    if os.name == "nt":
        _remove_windows_task()
    raise RuntimeError(
        f"nexum-browser broker did not become ready; see {LOG_PATH}"
    )


def send_request(
    command: str,
    args: dict[str, Any],
    *,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    return _request(
        ensure_broker(),
        command,
        args,
        timeout=timeout,
    )


def send_existing_request(
    command: str,
    args: dict[str, Any],
    *,
    timeout: float = REQUEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    state = _load_state()
    if not state or not _compatible_ping(_ping_response(state)):
        raise RuntimeError("nexum-browser broker is not running")
    return _request(state, command, args, timeout=timeout)


def stop_broker() -> bool:
    state = _load_state()
    if not state:
        if os.name == "nt":
            task_running = _windows_task_running()
            if task_running is not False:
                raise RuntimeError(
                    "Windows nexum-browser broker task may still be running "
                    "but broker state is unavailable; refusing to force-stop it"
                )
            _remove_windows_task()
        else:
            pids = _unix_broker_pids()
            if pids is None:
                raise RuntimeError(
                    "Cannot determine whether a nexum-browser broker is still "
                    "running because broker state is unavailable"
                )
            if pids:
                raise RuntimeError(
                    "A nexum-browser broker appears to be running without state; "
                    "refusing to report it stopped"
                )
        return False

    if _ping_response(state) is None:
        if os.name == "nt" and _windows_task_running() is False:
            _clear_state_if_token(str(state.get("token") or ""))
            _remove_windows_task()
            return False
        if _state_process_alive(state) is not False:
            raise RuntimeError(
                "The nexum-browser broker is running but not responding; "
                "refusing to force-stop it while an operation outcome may be unknown"
            )
        _clear_state_if_token(str(state.get("token") or ""))
        if os.name == "nt":
            task_running = _windows_task_running()
            if task_running is not False:
                raise RuntimeError(
                    "Windows nexum-browser broker task may still be running; "
                    "refusing to force-stop it while outcome is unknown"
                )
            _remove_windows_task()
        return False

    response = _request(
        state,
        "__stop__",
        {},
        timeout=_maintenance_request_timeout(15),
    )
    response_error = (
        str(response.get("message") or response)
        if response.get("code") != "ok"
        else None
    )
    if response.get("code") == "broker_busy":
        raise BrokerBusy(
            response_error or "nexum-browser broker is busy"
        )
    response_unknown = response.get("code") == "stop_outcome_unknown"
    response_release_failed = (
        response.get("code") == "runtime_release_failed"
    )
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if _ping_response(state, timeout=0.2) is None:
            _clear_state_if_token(str(state.get("token") or ""))
            if os.name == "nt":
                _remove_windows_task()
            if response_error is not None:
                if response_unknown:
                    raise BrokerRequestOutcomeUnknown(
                        response_error,
                        data=(
                            response.get("data")
                            if isinstance(response.get("data"), dict)
                            else None
                        ),
                    )
                if response_release_failed:
                    raise BrokerRuntimeReleaseFailed(
                        response_error,
                        data=(
                            response.get("data")
                            if isinstance(response.get("data"), dict)
                            else None
                        ),
                    )
                raise RuntimeError(response_error)
            return True
        time.sleep(0.05)

    if os.name == "nt":
        _remove_windows_task()
    raise RuntimeError(
        "nexum-browser broker did not finish shutdown cleanup"
    )


def daemon_main() -> int:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    broker = Broker()
    token = secrets.token_urlsafe(48)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(8)
    sock.settimeout(1.0)

    state = {
        "version": _STATE_VERSION,
        "pid": os.getpid(),
        "port": int(sock.getsockname()[1]),
        "token": token,
        "startedAt": time.time(),
    }
    _save_state(state)

    def request_stop(_signum: int, _frame: Any) -> None:
        broker.stop_requested = True

    for signum in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(ValueError, OSError):
            signal.signal(signum, request_stop)

    try:
        while not broker.stop_requested:
            if (
                not broker.has_active_operation()
                and time.monotonic() - broker.last_activity > IDLE_SECONDS
            ):
                break

            try:
                conn, _ = sock.accept()
            except socket.timeout:
                continue

            with conn:
                try:
                    raw = _recv_line(conn, REQUEST_TIMEOUT_SECONDS)
                    request = (
                        json.loads(raw.decode("utf-8"))
                        if raw
                        else {}
                    )
                    if not isinstance(request, dict):
                        raise RuntimeError(
                            "broker request must be a JSON object"
                        )
                    if not secrets.compare_digest(
                        str(request.get("token") or ""),
                        token,
                    ):
                        response = {
                            "code": "broker_unauthorized",
                            "message": "Invalid nexum-browser broker token",
                            "retryable": False,
                        }
                    else:
                        response = broker.handle(request)
                except Exception as exc:
                    response = {
                        "code": "broker_error",
                        "message": str(exc),
                        "retryable": False,
                    }

                with contextlib.suppress(
                    BrokenPipeError,
                    ConnectionResetError,
                ):
                    conn.sendall(
                        json.dumps(
                            response,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ).encode("utf-8")
                        + b"\n"
                    )
        return 0
    finally:
        broker.close()
        sock.close()
        _clear_state_if_token(token)
