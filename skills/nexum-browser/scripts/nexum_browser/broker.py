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
from .runtime import CuaRuntime, CuaToolError


_STATE_VERSION = 1
_BROKER_PROTOCOL = 3
_MAX_MESSAGE_BYTES = 64 * 1024 * 1024
_WINDOWS_TASK_ENV_PATH = RUNTIME_DIR / "broker-task-env.json"


class ActiveOperation:
    def __init__(self, code: str, title: str, timeout_ms: int) -> None:
        self.id = "op_" + uuid.uuid4().hex
        self.code = code
        self.title = title
        self.timeout_ms = timeout_ms
        self.state = "running"
        self.terminal_decision: str | None = None
        self.result: dict[str, Any] | None = None
        self.error: BaseException | None = None
        self.done = threading.Event()
        self.thread: threading.Thread | None = None


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
        }

    def _operation_status(self) -> dict[str, Any] | None:
        with self._operation_lock:
            return self._operation_status_unlocked()

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
            try:
                self._shutdown_runtime()
            except Exception as exc:
                self.stop_requested = True
                return {
                    "code": "runtime_release_failed",
                    "message": str(exc),
                    "retryable": True,
                }
            self.stop_requested = True
            return {"code": "ok", "data": {"stopped": True}}

        self.last_activity = time.monotonic()

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
        except Exception as exc:
            return {
                "code": "reset_failed",
                "message": str(exc),
                "retryable": True,
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

        try:
            runtime = self.ensure_runtime()
        except Exception as exc:
            return {
                "code": "runtime_unavailable",
                "message": str(exc),
                "retryable": True,
            }

        operation = ActiveOperation(code, title, timeout_ms)
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

                if operation.terminal_decision is not None:
                    if operation.terminal_decision == "decline":
                        return {
                            "code": "operation_declined",
                            "message": "Browser Runtime confirmation was declined",
                            "retryable": False,
                        }
                    return {
                        "code": "operation_cancelled",
                        "message": "Browser Runtime operation was cancelled",
                        "retryable": False,
                    }

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

    def _resume_operation(self, args: dict[str, Any]) -> dict[str, Any]:
        operation_id = str(args.get("operation") or "")
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

        try:
            runtime.respond_elicitation(
                elicitation.elicitation_id,
                action=decision,
                content=content,
            )
        except Exception as exc:
            return {
                "code": "runtime_unavailable",
                "message": str(exc),
                "retryable": True,
            }

        if decision == "accept":
            operation.state = "running"
        else:
            operation.terminal_decision = "decline"
            operation.state = "cancelled"
        return self._wait_for_operation(operation)

    def _cancel_operation(self, args: dict[str, Any]) -> dict[str, Any]:
        operation_id = str(args.get("operation") or "")
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

        try:
            runtime.respond_elicitation(
                elicitation.elicitation_id,
                action="cancel",
            )
        except Exception as exc:
            return {
                "code": "runtime_unavailable",
                "message": str(exc),
                "retryable": True,
            }

        operation.terminal_decision = "cancel"
        operation.state = "cancelled"
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

    with socket.create_connection(
        ("127.0.0.1", int(state["port"])),
        timeout=timeout,
    ) as conn:
        conn.sendall(payload)
        conn.shutdown(socket.SHUT_WR)
        raw = _recv_line(conn, timeout)

    if not raw:
        raise RuntimeError("nexum-browser broker returned an empty response")
    try:
        response = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "nexum-browser broker returned invalid JSON"
        ) from exc
    if not isinstance(response, dict):
        raise RuntimeError(
            "nexum-browser broker returned a non-object response"
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


def broker_status() -> dict[str, Any]:
    state = _load_state()
    if not state:
        return {"running": False}

    response = _ping_response(state)
    if response is None:
        return {
            "running": False,
            "staleState": True,
            "pid": state.get("pid"),
        }

    data = response.get("data")
    if not isinstance(data, dict) or not _compatible_ping(response):
        return {
            "running": False,
            "incompatibleProtocol": True,
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
    if state:
        ping = _ping_response(state)
        if _compatible_ping(ping):
            return state
        if ping is not None:
            _request(state, "__stop__", {}, timeout=2)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if _ping_response(state, timeout=0.2) is None:
                    break
                time.sleep(0.05)
            else:
                raise RuntimeError(
                    "An incompatible nexum-browser broker is still running; "
                    "refusing to start a second broker"
                )
        _clear_state_if_token(str(state.get("token") or ""))

    if os.name == "nt":
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
            _remove_windows_task()
        return False

    if _ping_response(state) is None:
        _clear_state_if_token(str(state.get("token") or ""))
        if os.name == "nt":
            _remove_windows_task()
        return False

    response = _request(state, "__stop__", {}, timeout=5)
    response_error = (
        str(response.get("message") or response)
        if response.get("code") != "ok"
        else None
    )
    if response.get("code") == "broker_busy":
        raise RuntimeError(response_error or "nexum-browser broker is busy")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if _ping_response(state, timeout=0.2) is None:
            _clear_state_if_token(str(state.get("token") or ""))
            if os.name == "nt":
                _remove_windows_task()
            if response_error is not None:
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
