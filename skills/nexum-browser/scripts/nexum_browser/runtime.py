from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import subprocess
import time
import uuid
from typing import Any

from .common import (
    LOG_PATH,
    MARKER,
    PUBLIC_API_SURFACES,
    RUNTIME_DIR,
    SKILL_ROOT,
    STATE_PATH,
    build_public_api_contract,
    codex_home,
    find_browser_client,
    find_codex,
)
from .transport import ProxyWebSocket, SocketWebSocket


_ALLOWED_APP_SERVER_METHODS = {
    "initialize",
    "thread/start",
    "mcpServerStatus/list",
    "mcpServer/tool/call",
}
_STATE_VERSION = 1
_BACKEND_MANAGED = "managed-daemon"
_BACKEND_LOCAL = "local-websocket"
_WINDOWS_ELEVATION_ERROR = "start the windows daemon from a non-elevated terminal"
_WINDOWS_UNTRUSTED_BROWSER_CLIENT = (
    "privileged native pipe bridge is not available; browser-client is not trusted"
)
_BROWSER_BOOTSTRAP_TIMEOUT_MS = 90_000


def _bounded_message(value: str, limit: int = 800) -> str:
    value = " ".join(value.strip().split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _run_codex(codex: Path, args: list[str], *, timeout: float = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(codex), *args],
        cwd=str(SKILL_ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _parse_json_line(value: str) -> dict[str, Any]:
    for line in reversed(value.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _parse_json_output(value: str) -> dict[str, Any]:
    stripped = value.strip()
    if stripped:
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(parsed, dict):
                return parsed
    return _parse_json_line(value)


def _codex_version(codex: Path) -> str:
    result = _run_codex(codex, ["--version"], timeout=15)
    if result.returncode != 0:
        raise RuntimeError(_bounded_message(result.stderr or result.stdout) or "Unable to read Codex CLI version")
    return result.stdout.strip()


def _standalone_codex(fallback: Path) -> Path:
    if os.environ.get("NEXUM_BROWSER_CODEX"):
        return fallback
    home = codex_home()
    name = "codex.exe" if os.name == "nt" else "codex"
    for candidate in (
        home / "packages" / "standalone" / "current" / name,
        home / "packages" / "standalone" / "current" / "bin" / name,
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return fallback


def daemon_version(codex: Path) -> tuple[dict[str, Any], str | None]:
    result = _run_codex(_standalone_codex(codex), ["app-server", "daemon", "version"], timeout=20)
    if result.returncode == 0:
        data = _parse_json_output(result.stdout)
        return data or {"status": "running"}, None
    return {}, _bounded_message(result.stderr or result.stdout) or "Codex app-server daemon is not running"


def _managed_codex(fallback: Path, daemon: dict[str, Any]) -> Path:
    candidates: list[Path] = []
    value = daemon.get("managedCodexPath")
    if value:
        candidates.append(Path(str(value)).expanduser())
    home = codex_home()
    candidates.extend(
        [
            home / "packages" / "standalone" / "current" / "bin" / ("codex.exe" if os.name == "nt" else "codex"),
            home / "packages" / "standalone" / "current" / ("codex.exe" if os.name == "nt" else "codex"),
        ]
    )
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return fallback


def ensure_daemon(codex: Path) -> dict[str, Any]:
    result = _run_codex(
        _standalone_codex(codex),
        ["app-server", "daemon", "start"],
        timeout=60,
    )
    if result.returncode != 0:
        message = _bounded_message(result.stderr or result.stdout)
        raise RuntimeError(message or "Unable to start the Codex app-server daemon")
    return _parse_json_output(result.stdout)


def bootstrap_daemon(codex: Path) -> dict[str, Any]:
    result = _run_codex(
        _standalone_codex(codex),
        ["app-server", "daemon", "bootstrap"],
        timeout=120,
    )
    if result.returncode != 0:
        message = _bounded_message(result.stderr or result.stdout)
        raise RuntimeError(message or "Unable to bootstrap the Codex app-server daemon")
    return _parse_json_output(result.stdout)


def _is_windows_elevation_error(message: str) -> bool:
    return os.name == "nt" and _WINDOWS_ELEVATION_ERROR in message.lower()


def prepare_runtime(codex: Path) -> dict[str, Any]:
    daemon, daemon_error = daemon_version(codex)
    if not daemon_error:
        return {
            "backend": _BACKEND_MANAGED,
            "daemon": daemon,
            "bootstrap": {"status": "already-running"},
        }
    try:
        bootstrap = bootstrap_daemon(codex)
    except RuntimeError as exc:
        if not _is_windows_elevation_error(str(exc)):
            raise
        return {
            "backend": _BACKEND_LOCAL,
            "fallbackReason": (
                "Codex refuses a shared managed daemon from an elevated Windows "
                "caller; nexum-browser will use a broker-owned authenticated "
                "loopback app-server instead."
            ),
        }
    return {
        "backend": _BACKEND_MANAGED,
        "bootstrap": bootstrap,
    }


def _pick_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _terminate_process_pid(pid: int) -> None:
    if pid <= 0:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
        return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.kill(pid, 15)


def _start_local_app_server(
    codex: Path,
    *,
    log_file: Any,
) -> tuple[SocketWebSocket, subprocess.Popen[Any]]:
    token = secrets.token_urlsafe(48)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    port = _pick_loopback_port()
    args = [
        str(_standalone_codex(codex)),
        "app-server",
        "--listen",
        f"ws://127.0.0.1:{port}",
        "--ws-auth",
        "capability-token",
        "--ws-token-sha256",
        digest,
    ]
    kwargs: dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": log_file,
        "stderr": log_file,
        "cwd": str(SKILL_ROOT),
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    process = subprocess.Popen(args, **kwargs)
    deadline = time.monotonic() + 15
    last_error: Exception | None = None
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    "Private Codex app-server exited during startup with code "
                    f"{process.returncode}; see {LOG_PATH}"
                )
            try:
                connection = SocketWebSocket(
                    "127.0.0.1",
                    port,
                    token,
                    timeout=0.75,
                )
                return connection, process
            except Exception as exc:
                last_error = exc
                time.sleep(0.1)
    except Exception:
        _terminate_process_pid(process.pid)
        raise
    _terminate_process_pid(process.pid)
    if last_error is not None:
        raise RuntimeError(
            f"Private Codex app-server did not become ready: {last_error}"
        )
    raise RuntimeError(
        f"Private Codex app-server did not become ready; see {LOG_PATH}"
    )


def _run_browser_diagnostic(script_name: str, *args: str) -> dict[str, Any]:
    node = shutil.which("node")
    if not node:
        return {}
    try:
        script = find_browser_client().parent / script_name
    except Exception:
        return {}
    if not script.is_file():
        return {}
    try:
        result = subprocess.run(
            [node, str(script), *args],
            cwd=str(script.parent.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    return _parse_json_output(result.stdout)


def diagnose_browser_runtime_error(error: Exception | str) -> str:
    message = str(error)
    if os.name != "nt":
        return message
    lower = message.lower()
    if _WINDOWS_ELEVATION_ERROR in lower:
        return (
            message
            + " The shared managed daemon is unavailable at this Windows "
            "integrity level. nexum-browser normally falls back to its "
            "broker-owned authenticated loopback app-server for this case."
        )
    if _WINDOWS_UNTRUSTED_BROWSER_CLIENT in lower:
        return (
            message
            + " The cached bundled Browser plugin is stale or overwritten. "
            "Reload or reinstall the bundled Browser plugin from the Codex/ChatGPT "
            "desktop plugin UI, then retry. nexum-browser will not repair the "
            "native Browser integration itself."
        )
    if "no browser is available" not in lower:
        return message

    native_host = _run_browser_diagnostic(
        "check-native-host-manifest.js", "--browser", "chrome", "--json"
    )
    problem = native_host.get("problem")
    if native_host.get("correct") is False and isinstance(problem, str) and problem.strip():
        return (
            message
            + " Browser plugin diagnostic: "
            + _bounded_message(problem)
            + ". Reload or reinstall the bundled Browser plugin from the Codex/ChatGPT "
            "desktop plugin UI, then retry. Do not create or repair the native-host "
            "registration manually."
        )

    extension = _run_browser_diagnostic(
        "check-extension-installed.js", "--browser", "chrome", "--json"
    )
    if extension:
        if extension.get("installed") is False:
            return (
                message
                + " Browser plugin diagnostic: the ChatGPT browser extension is not "
                "installed for the selected Chrome profile."
            )
        if extension.get("enabled") is False:
            return (
                message
                + " Browser plugin diagnostic: the ChatGPT browser extension is installed "
                "but disabled for the selected Chrome profile."
            )

    running = _run_browser_diagnostic(
        "chrome-is-running.js", "--browser", "chrome", "--json"
    )
    if running.get("running") is False:
        return message + " Browser plugin diagnostic: Google Chrome is not running."

    return (
        message
        + " Browser discovery failed even though the local app-server is available. "
        "Reload the bundled Browser plugin in the Codex/ChatGPT desktop app and retry."
    )


def _load_state() -> dict[str, Any]:
    try:
        value = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(value, dict) or value.get("version") != _STATE_VERSION:
        return {}
    return value


def _save_state(value: dict[str, Any]) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_name(f"{STATE_PATH.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        with contextlib.suppress(OSError):
            os.chmod(tmp, 0o600)
        os.replace(tmp, STATE_PATH)
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def deactivate_state() -> None:
    state = _load_state()
    if not state:
        return
    state["active"] = False
    state["browserTurnId"] = ""
    state["localProcessId"] = None
    state["lastActivity"] = time.time()
    _save_state(state)


def release_persisted_state() -> bool:
    state = _load_state()
    session_id = str(state.get("threadId") or "")
    turn_id = str(state.get("browserTurnId") or "")
    if not state.get("active") or not session_id or not turn_id:
        deactivate_state()
        return False

    backend = str(state.get("backend") or _BACKEND_MANAGED)
    if backend == _BACKEND_LOCAL:
        try:
            local_pid = int(state.get("localProcessId") or 0)
        except (TypeError, ValueError):
            local_pid = 0
        if local_pid:
            _terminate_process_pid(local_pid)
        deactivate_state()
        return True

    server = AppServer(create_thread=False, allow_local_fallback=False)
    try:
        server._signal_specific_browser_turn_ended(
            session_id=session_id,
            turn_id=turn_id,
        )
        deactivate_state()
        return True
    finally:
        server.close()


def session_status() -> dict[str, Any]:
    state = _load_state()
    return {
        "present": bool(state.get("threadId")),
        "active": bool(state.get("active")),
        "threadId": state.get("threadId"),
        "backend": state.get("backend"),
        "lastActivity": state.get("lastActivity"),
    }


def runtime_diagnostics() -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": False,
        "platform": {"system": platform.system().lower(), "machine": platform.machine()},
        "python": platform.python_version(),
        "session": session_status(),
    }
    try:
        codex = find_codex()
        result["codex"] = {"path": str(codex), "version": _codex_version(codex)}
    except Exception as exc:
        result["codex"] = {"available": False, "error": _bounded_message(str(exc))}
        return result

    daemon, daemon_error = daemon_version(codex)
    if daemon_error:
        result["daemon"] = {"status": "unavailable", "error": daemon_error}
    else:
        result["daemon"] = daemon

    try:
        browser_client = find_browser_client()
        result["browserPlugin"] = {"available": True, "client": str(browser_client)}
    except Exception as exc:
        result["browserPlugin"] = {"available": False, "error": _bounded_message(str(exc))}
        return result

    result["available"] = bool(daemon.get("status") == "running")
    return result


class AppServer:
    """Browser Runtime client over one persistent Codex app-server proxy connection."""

    def __init__(
        self,
        *,
        create_thread: bool = True,
        allow_local_fallback: bool = True,
    ) -> None:
        launcher = find_codex()
        self.browser_client = find_browser_client()
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
        self.proxy: ProxyWebSocket | SocketWebSocket | None = None
        self.backend = ""
        self.local_process: subprocess.Popen[Any] | None = None
        self.seq = 0
        self.thread_id = ""
        self.browser_turn_id = ""
        self._active = False
        self._released = False
        stale = _load_state()
        stale_session_id = str(stale.get("threadId") or "")
        stale_turn_id = str(stale.get("browserTurnId") or "")
        stale_backend = str(stale.get("backend") or _BACKEND_MANAGED)
        try:
            stale_local_pid = int(stale.get("localProcessId") or 0)
        except (TypeError, ValueError):
            stale_local_pid = 0
        if create_thread and stale_backend == _BACKEND_LOCAL and stale_local_pid:
            _terminate_process_pid(stale_local_pid)
            deactivate_state()
        try:
            try:
                daemon = ensure_daemon(launcher)
            except RuntimeError as exc:
                if (
                    not allow_local_fallback
                    or not _is_windows_elevation_error(str(exc))
                ):
                    raise
                self.backend = _BACKEND_LOCAL
                self.proxy, self.local_process = _start_local_app_server(
                    launcher,
                    log_file=self.log_file,
                )
            else:
                self.backend = _BACKEND_MANAGED
                proxy_codex = _managed_codex(launcher, daemon)
                self.proxy = ProxyWebSocket(proxy_codex, stderr=self.log_file)
            self._initialize_connection()
            if create_thread:
                self._create_thread()
            if (
                create_thread
                and stale_backend == _BACKEND_MANAGED
                and self.backend == _BACKEND_MANAGED
                and stale.get("active")
                and stale_session_id
                and stale_turn_id
            ):
                try:
                    self._signal_specific_browser_turn_ended(
                        session_id=stale_session_id,
                        turn_id=stale_turn_id,
                    )
                except Exception:
                    pass
        except Exception:
            self.close()
            raise

    def _initialize_connection(self) -> None:
        self._request(
            "initialize",
            {
                "clientInfo": {"name": "nexum-browser", "version": "0.3.0"},
                "capabilities": {"experimentalApi": True},
            },
        )
        assert self.proxy is not None
        self.proxy.send_json({"jsonrpc": "2.0", "method": "initialized", "params": {}})

    def _create_thread(self) -> None:
        result = self._request(
            "thread/start",
            {"cwd": str(SKILL_ROOT), "ephemeral": True, "threadSource": "nexum-browser"},
        )
        self.thread_id = str((result.get("thread") or {}).get("id") or "")
        if not self.thread_id:
            raise RuntimeError("Codex app-server did not return a thread id")
        self.browser_turn_id = "nexum-browser-" + uuid.uuid4().hex
        self._active = True
        self._wait_for_node_repl(timeout=20)
        self._persist_state(active=True)

    def _persist_state(self, *, active: bool) -> None:
        if not self.thread_id:
            return
        _save_state(
            {
                "version": _STATE_VERSION,
                "threadId": self.thread_id,
                "browserTurnId": self.browser_turn_id if active else "",
                "browserClient": str(self.browser_client),
                "backend": self.backend,
                "localProcessId": (
                    self.local_process.pid
                    if self.local_process is not None and active
                    else None
                ),
                "active": active,
                "lastActivity": time.time(),
            }
        )

    def _wait_for_node_repl(self, *, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self._request(
                "mcpServerStatus/list",
                {"threadId": self.thread_id, "detail": "toolsAndAuthOnly"},
                timeout=min(10, max(1, deadline - time.monotonic())),
            )
            if any(
                server.get("name") == "node_repl" and server.get("runtimeStatus") == "connected"
                for server in status.get("data") or []
            ):
                return
            time.sleep(0.15)
        raise RuntimeError("Codex node_repl MCP server did not become ready")

    def close(self) -> None:
        if self._active and not self._released and self.thread_id:
            self._persist_state(active=True)
        if self.proxy is not None:
            self.proxy.close()
            self.proxy = None
        if self.local_process is not None:
            if self.local_process.poll() is None:
                _terminate_process_pid(self.local_process.pid)
            with contextlib.suppress(Exception):
                self.local_process.wait(timeout=2)
            self.local_process = None
        if not self.log_file.closed:
            self.log_file.close()

    def release(self) -> None:
        if not self._active:
            deactivate_state()
            self._released = True
            return
        self._release_active(best_effort=False)

    def _release_active(self, *, best_effort: bool) -> None:
        errors: list[Exception] = []
        try:
            self._signal_browser_turn_ended()
        except Exception as exc:
            if not self._is_stale_thread_error(str(exc)):
                errors.append(exc)
        try:
            self._reset_browser_globals()
        except Exception as exc:
            if not self._is_stale_thread_error(str(exc)):
                errors.append(exc)
        self._active = False
        self._released = True
        self.browser_turn_id = ""
        self._persist_state(active=False)
        if errors and not best_effort:
            raise RuntimeError(str(errors[0]))

    def _signal_browser_turn_ended(self) -> None:
        if not self.thread_id or not self.browser_turn_id:
            return
        self._signal_specific_browser_turn_ended(
            session_id=self.thread_id,
            turn_id=self.browser_turn_id,
        )

    def _signal_specific_browser_turn_ended(self, *, session_id: str, turn_id: str) -> None:
        if not session_id or not turn_id:
            return
        self._call_node_tool_for_session(
            session_id,
            turn_id,
            "turn_ended",
            {
                "hook_event_name": "Stop",
                "session_id": session_id,
                "turn_id": turn_id,
            },
            timeout=15,
        )

    def _reset_browser_globals(self) -> None:
        self._call_node_tool("js_reset", {}, timeout=15)

    def _call_node_tool(
        self,
        tool: str,
        arguments: dict[str, Any],
        *,
        timeout: float,
    ) -> dict[str, Any]:
        return self._call_node_tool_for_session(
            self.thread_id,
            self.browser_turn_id,
            tool,
            arguments,
            timeout=timeout,
        )

    def _call_node_tool_for_session(
        self,
        session_id: str,
        turn_id: str,
        tool: str,
        arguments: dict[str, Any],
        *,
        timeout: float,
    ) -> dict[str, Any]:
        result = self._request(
            "mcpServer/tool/call",
            {
                "threadId": session_id,
                "server": "node_repl",
                "tool": tool,
                "_meta": self._meta_for(session_id, turn_id),
                "arguments": arguments,
            },
            timeout=timeout,
        )
        if result.get("isError"):
            texts = [
                str(item.get("text", ""))
                for item in result.get("content") or []
                if item.get("type") == "text"
            ]
            raise RuntimeError("\n".join(text for text in texts if text).strip() or f"{tool} failed")
        return result

    def _request(self, method: str, params: dict[str, Any], timeout: float = 30) -> dict[str, Any]:
        if method not in _ALLOWED_APP_SERVER_METHODS:
            raise RuntimeError(f"Codex app-server method is not allowed in nexum-browser: {method}")
        if self.proxy is None:
            raise RuntimeError("Codex app-server proxy is not connected")
        self.seq += 1
        request_id = self.seq
        self.proxy.send_json(
            {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        )
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            payload = self.proxy.recv_json(max(0.1, deadline - time.monotonic()))
            if payload.get("id") != request_id:
                continue
            if "error" in payload:
                error = payload["error"]
                if isinstance(error, dict):
                    raise RuntimeError(str(error.get("message") or error))
                raise RuntimeError(str(error))
            result = payload.get("result")
            return result if isinstance(result, dict) else {}
        raise TimeoutError(f"Timed out waiting for app-server method {method}")

    def _meta(self) -> dict[str, str]:
        return self._meta_for(self.thread_id, self.browser_turn_id)

    @staticmethod
    def _meta_for(session_id: str, turn_id: str) -> dict[str, str]:
        return {
            "x-codex-turn-metadata": json.dumps(
                {
                    "session_id": session_id,
                    "turn_id": turn_id,
                    "model": "nexum-browser",
                    "thread_source": "direct",
                },
                separators=(",", ":"),
            )
        }

    def execute_js(
        self,
        code: str,
        *,
        title: str = "Browser action",
        timeout_ms: int = 30000,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        guard = "if (typeof globalThis.__nexumBrowserAgent === 'undefined' || typeof globalThis.__nexumBrowser === 'undefined') throw new Error('NEXUM_BROWSER_RUNTIME_NOT_INITIALIZED');"
        guarded_code = guard + code
        try:
            result = self._execute_js_once(guarded_code, title=title, timeout_ms=timeout_ms)
        except RuntimeError as exc:
            message = str(exc)
            if self._is_stale_thread_error(message):
                stale_session_id = self.thread_id
                stale_turn_id = self.browser_turn_id
                self.thread_id = ""
                self.browser_turn_id = ""
                self._active = False
                self._released = False
                self._create_thread()
                if stale_session_id and stale_turn_id:
                    try:
                        self._signal_specific_browser_turn_ended(
                            session_id=stale_session_id,
                            turn_id=stale_turn_id,
                        )
                    except Exception:
                        pass
                self._bootstrap_browser()
                result = self._execute_js_once(guarded_code, title=title, timeout_ms=timeout_ms)
            elif "NEXUM_BROWSER_RUNTIME_NOT_INITIALIZED" not in message:
                raise
            else:
                self._bootstrap_browser()
                result = self._execute_js_once(guarded_code, title=title, timeout_ms=timeout_ms)
        self._persist_state(active=True)
        return result

    @staticmethod
    def _is_stale_thread_error(message: str) -> bool:
        lowered = message.lower()
        return "thread not found" in lowered or "unknown thread" in lowered

    def _execute_js_once(
        self,
        code: str,
        *,
        title: str = "Browser action",
        timeout_ms: int = 30000,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        result = self._request(
            "mcpServer/tool/call",
            {
                "threadId": self.thread_id,
                "server": "node_repl",
                "tool": "js",
                "_meta": self._meta(),
                "arguments": {"code": code, "timeout_ms": timeout_ms, "title": title[:80]},
            },
            timeout=max(35, timeout_ms / 1000 + 5),
        )
        content = result.get("content") or []
        texts = [str(item.get("text", "")) for item in content if item.get("type") == "text"]
        if result.get("isError"):
            raise RuntimeError("\n".join(x for x in texts if x).strip() or "Browser runtime returned an error")
        decoded: dict[str, Any] | None = None
        for text in texts:
            index = text.find(MARKER)
            if index < 0:
                continue
            tail = text[index + len(MARKER):]
            token = "".join(ch for ch in tail if ch.isalnum() or ch in "+/=_-")
            if not token:
                continue
            token += "=" * (-len(token) % 4)
            try:
                candidate = json.loads(base64.b64decode(token).decode("utf-8"))
            except Exception:
                continue
            if isinstance(candidate, dict):
                decoded = candidate
                break
        if decoded is None:
            message = "\n".join(x for x in texts if x).strip()
            raise RuntimeError(message or "Browser runtime did not return a structured result")
        return decoded, content

    def _bootstrap_browser(self) -> None:
        uri = self.browser_client.resolve().as_uri()
        public_api = build_public_api_contract()
        public_surfaces = PUBLIC_API_SURFACES
        code = f"""
const {{setupBrowserRuntime}} = await import({json.dumps(uri)});
const __nexumSetupGlobals = {{}};
const __nexumSetupResult = await setupBrowserRuntime({{
  globals: __nexumSetupGlobals,
  elicitationDisplayName: 'Nexum Browser',
}});
globalThis.__nexumBrowserAgent = __nexumSetupResult ?? __nexumSetupGlobals.agent;
if (globalThis.__nexumBrowserAgent == null) throw new Error('Browser Runtime setup did not return an agent');
globalThis.__nexumPublicApi = {json.dumps(public_api, separators=(',', ':'))};
globalThis.__nexumPublicSurfaces = {json.dumps(public_surfaces, separators=(',', ':'))};
globalThis.__nexumBrowserHandles = new Map();
globalThis.__nexumBrowserHandleMeta = new Map();
globalThis.__nexumBrowserHandleSeq = 0;

globalThis.__nexumResolveInterfaceHint = (hint, value) => {{
  if (hint === 'Dialog' && value && typeof value.type === 'string') {{
    if (value.type === 'alert') return 'AlertDialog';
    if (value.type === 'beforeunload') return 'BeforeUnloadDialog';
    if (value.type === 'confirm') return 'ConfirmDialog';
    if (value.type === 'prompt') return 'PromptDialog';
  }}
  return hint || null;
}};

globalThis.__nexumStoreHandle = (value, interfaceHint = null, extra = {{}}) => {{
  const id = `h_${{++globalThis.__nexumBrowserHandleSeq}}`;
  globalThis.__nexumBrowserHandles.set(id, value);
  const resolvedInterface = globalThis.__nexumResolveInterfaceHint(interfaceHint, value);
  const meta = {{interface: resolvedInterface, ...extra}};
  globalThis.__nexumBrowserHandleMeta.set(id, meta);
  return {{handle: id, ...(resolvedInterface ? {{interface: resolvedInterface}} : {{}}), ...(meta.binary ? {{binary: true, byteLength: meta.byteLength}} : {{}})}};
}};

globalThis.__nexumInflate = (value) => {{
  if (Array.isArray(value)) return value.map(globalThis.__nexumInflate);
  if (value && typeof value === 'object') {{
    if (typeof value.$handle === 'string') {{
      if (!globalThis.__nexumBrowserHandles.has(value.$handle)) throw new Error(`Unknown browser handle: ${{value.$handle}}`);
      return globalThis.__nexumBrowserHandles.get(value.$handle);
    }}
    if (value.$call != null) {{
      const descriptor = value.$call;
      if (descriptor == null || typeof descriptor !== 'object' || Array.isArray(descriptor)) {{
        throw new Error('$call must contain a public Browser API call descriptor');
      }}
      return async () => await globalThis.__nexumInvokeDescriptor(descriptor);
    }}
    return Object.fromEntries(Object.entries(value).map(([k,v]) => [k, globalThis.__nexumInflate(v)]));
  }}
  return value;
}};

globalThis.__nexumSerialize = (value, depth = 0, interfaceHint = null) => {{
  if (value === undefined || value === null) return value ?? null;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return value;
  if (typeof value === 'bigint') return value.toString();
  if (value instanceof Uint8Array) return globalThis.__nexumStoreHandle(value, null, {{binary: true, byteLength: value.byteLength}});
  if (depth >= 5) return {{truncated: true}};
  if (Array.isArray(value)) return value.map(v => globalThis.__nexumSerialize(v, depth + 1, interfaceHint));
  if (typeof value === 'function') return globalThis.__nexumStoreHandle(value, interfaceHint);
  if (typeof value === 'object') {{
    const proto = Object.getPrototypeOf(value);
    const ctorName = proto?.constructor?.name;
    if (proto && proto !== Object.prototype && ctorName !== 'Object') {{
      return globalThis.__nexumStoreHandle(value, interfaceHint);
    }}
    const out = {{}};
    for (const [key, item] of Object.entries(value)) out[key] = globalThis.__nexumSerialize(item, depth + 1);
    return out;
  }}
  return String(value);
}};

globalThis.__nexumResolvePath = (receiver, path) => {{
  const parts = path.split('.');
  let owner = receiver;
  for (let i = 0; i < parts.length - 1; i++) owner = owner[parts[i]];
  return {{owner, member: owner[parts[parts.length - 1]]}};
}};

globalThis.__nexumPublicCall = (interfaceName, path, args) => {{
  if (!interfaceName) return {{returnInterface: null}};
  const parts = path.split('.');
  let currentInterface = interfaceName;
  let returnInterface = null;
  for (let i = 0; i < parts.length; i++) {{
    const members = globalThis.__nexumPublicApi.interfaces[currentInterface];
    const member = members != null && Object.prototype.hasOwnProperty.call(members, parts[i])
      ? members[parts[i]]
      : null;
    if (!member) throw new Error(`Browser API member is not public: ${{currentInterface}}.${{parts[i]}}`);
    let candidates = member.returns || [];
    if (currentInterface === 'PlaywrightAPI' && parts[i] === 'waitForEvent') {{
      if (args?.[0] === 'download') candidates = ['PlaywrightDownload'];
      else if (args?.[0] === 'filechooser') candidates = ['PlaywrightFileChooser'];
    }}
    returnInterface = candidates[0] || null;
    if (i < parts.length - 1) {{
      const next = candidates.find(name => globalThis.__nexumPublicApi.interfaces[name]);
      if (!next) throw new Error(`Browser API path cannot continue through ${{currentInterface}}.${{parts[i]}}`);
      currentInterface = next;
    }}
  }}
  return {{returnInterface}};
}};

globalThis.__nexumCall = async (receiver, interfaceName, path, args, awaitResult = true) => {{
  const {{returnInterface}} = globalThis.__nexumPublicCall(interfaceName, path, args);
  const {{owner, member}} = globalThis.__nexumResolvePath(receiver, path);
  const inflated = globalThis.__nexumInflate(args);
  let result = typeof member === 'function' ? member.apply(owner, inflated) : member;
  if (!awaitResult) {{
    const guarded = Promise.resolve(result).then(
      value => ({{__nexumPromise: true, ok: true, value}}),
      error => ({{__nexumPromise: true, ok: false, error: {{message: String(error?.message || error), name: String(error?.name || 'Error')}}}}),
    );
    return globalThis.__nexumStoreHandle(guarded, null, {{promise: true, resolvedInterface: returnInterface}});
  }}
  result = await result;
  return globalThis.__nexumSerialize(result, 0, returnInterface);
}};

globalThis.__nexumCallRaw = async (receiver, interfaceName, path, args) => {{
  globalThis.__nexumPublicCall(interfaceName, path, args);
  const {{owner, member}} = globalThis.__nexumResolvePath(receiver, path);
  const inflated = globalThis.__nexumInflate(args);
  return await (typeof member === 'function' ? member.apply(owner, inflated) : member);
}};

globalThis.__nexumCallHandle = async (handleId, path, args, awaitResult = true) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error(`Unknown browser handle: ${{handleId}}`);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  if (!meta.interface) throw new Error(`Browser handle ${{handleId}} has no documented public interface`);
  return await globalThis.__nexumCall(globalThis.__nexumBrowserHandles.get(handleId), meta.interface, path, args, awaitResult);
}};

globalThis.__nexumCallHandleRaw = async (handleId, path, args) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error(`Unknown browser handle: ${{handleId}}`);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  if (!meta.interface) throw new Error(`Browser handle ${{handleId}} has no documented public interface`);
  return await globalThis.__nexumCallRaw(globalThis.__nexumBrowserHandles.get(handleId), meta.interface, path, args);
}};

globalThis.__nexumResolveDescriptorTarget = async (descriptor) => {{
  const surface = descriptor.surface;
  if (surface === 'handle') {{
    const handleId = descriptor.handle;
    if (typeof handleId !== 'string' || !globalThis.__nexumBrowserHandles.has(handleId)) {{
      throw new Error(`Unknown browser handle: ${{String(handleId)}}`);
    }}
    const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
    if (!meta.interface) throw new Error(`Browser handle ${{handleId}} has no documented public interface`);
    return {{receiver: globalThis.__nexumBrowserHandles.get(handleId), interfaceName: meta.interface}};
  }}

  const interfaceName = globalThis.__nexumPublicSurfaces[surface];
  if (!interfaceName) throw new Error(`Unsupported callback Browser API surface: ${{String(surface)}}`);
  if (surface === 'agent') return {{receiver: globalThis.__nexumBrowserAgent, interfaceName}};
  if (surface === 'browsers-api') return {{receiver: globalThis.__nexumBrowserAgent.browsers, interfaceName}};
  if (surface === 'docs-api') return {{receiver: globalThis.__nexumBrowserAgent.documentation, interfaceName}};
  if (surface === 'browser') return {{receiver: globalThis.__nexumBrowser, interfaceName}};
  if (surface === 'tabs') return {{receiver: globalThis.__nexumBrowser.tabs, interfaceName}};
  if (surface === 'user') return {{receiver: globalThis.__nexumBrowser.user, interfaceName}};

  const tabId = descriptor.tab;
  if (typeof tabId !== 'string' || !tabId) throw new Error(`tab is required for callback surface ${{surface}}`);
  const tab = await globalThis.__nexumBrowser.tabs.get(tabId);
  const receiver = {{
    tab,
    playwright: tab.playwright,
    cua: tab.cua,
    'dom-cua': tab.dom_cua,
    ax: tab.ax,
    content: tab.content,
    clipboard: tab.clipboard,
    dev: tab.dev,
  }}[surface];
  if (receiver == null) throw new Error(`Browser API surface ${{surface}} is unavailable on the selected backend`);
  return {{receiver, interfaceName}};
}};

globalThis.__nexumInvokeDescriptor = async (descriptor) => {{
  if (typeof descriptor.method !== 'string' || !descriptor.method) {{
    throw new Error('$call descriptor requires a public method');
  }}
  if (descriptor.args != null && !Array.isArray(descriptor.args)) {{
    throw new Error('$call descriptor args must be an array');
  }}
  const {{receiver, interfaceName}} = await globalThis.__nexumResolveDescriptorTarget(descriptor);
  return await globalThis.__nexumCallRaw(
    receiver,
    interfaceName,
    descriptor.method,
    descriptor.args || [],
  );
}};

globalThis.__nexumAwaitHandle = async (handleId) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error(`Unknown browser handle: ${{handleId}}`);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  if (!meta.promise) throw new Error(`Browser handle ${{handleId}} is not an asynchronous result`);
  const settled = await globalThis.__nexumBrowserHandles.get(handleId);
  if (settled?.__nexumPromise && !settled.ok) throw new Error(settled.error?.message || 'Browser promise rejected');
  const value = settled?.__nexumPromise ? settled.value : settled;
  return globalThis.__nexumSerialize(value, 0, meta.resolvedInterface || null);
}};

globalThis.__nexumHandleInfo = (handleId) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error(`Unknown browser handle: ${{handleId}}`);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  return {{handle: handleId, ...meta}};
}};

globalThis.__nexumReadDoc = async (name) => await globalThis.__nexumBrowserAgent.documentation.get(name);
for (const name of ['browser-safety', 'confirmations', 'browser-control-interruption', 'api-use-behavior']) {{
  try {{ await globalThis.__nexumReadDoc(name); }} catch {{}}
}}

globalThis.__nexumSelectBrowser = async (mode, value) => {{
  let browser;
  if (mode === 'default') browser = await globalThis.__nexumBrowserAgent.browsers.getDefault();
  else if (mode === 'url') browser = await globalThis.__nexumBrowserAgent.browsers.getForUrl(value);
  else browser = await globalThis.__nexumBrowserAgent.browsers.get(value);
  globalThis.__nexumBrowser = browser;
  try {{ await browser.documentation(); }} catch {{}}
  const infos = await globalThis.__nexumBrowserAgent.browsers.list();
  const info = infos.find(x => x.id === browser.browserId) || {{id: browser.browserId}};
  if (info.type === 'extension') {{
    try {{ await browser.nameSession('🔎 Nexum Browser'); }} catch {{}}
  }}
  return info;
}};

const __selected = await globalThis.__nexumSelectBrowser('default', null);
const __value = {{browserId: globalThis.__nexumBrowser.browserId, selected: __selected}};
nodeRepl.write({json.dumps(MARKER)} + Buffer.from(JSON.stringify(__value)).toString('base64'));
"""
        self._execute_js_once(
            code,
            title="Initialize browser runtime",
            timeout_ms=_BROWSER_BOOTSTRAP_TIMEOUT_MS,
        )
