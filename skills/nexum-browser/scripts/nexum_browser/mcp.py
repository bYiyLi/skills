from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import uuid
from typing import Any


_PROTOCOL_VERSION = "2025-06-18"
_INTERNAL_TOOL_ALLOWLIST = {"js", "js_reset", "turn_ended"}


class McpError(RuntimeError):
    pass


@dataclass
class _PendingRequest:
    event: threading.Event = field(default_factory=threading.Event)
    response: dict[str, Any] | None = None
    error: BaseException | None = None


@dataclass(frozen=True)
class PendingElicitation:
    elicitation_id: str
    request_id: int | str
    params: dict[str, Any]


class StdioMcpClient:
    """Small full-duplex MCP JSON-RPC client for a persistent cua_repl process."""

    def __init__(
        self,
        *,
        command: str,
        args: list[str],
        env: dict[str, str],
        configured_tools: set[str],
        log_path: Path,
        startup_timeout: float,
    ) -> None:
        self._write_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._next_request_id = 0
        self._pending: dict[int, _PendingRequest] = {}
        self._elicitations: dict[str, PendingElicitation] = {}
        self._closed = threading.Event()
        self._tools_dirty = False
        self._tool_names: set[str] = set()
        self._configured_tools = set(configured_tools)
        self._allowed_tools: set[str] = set()
        self._startup_timeout = startup_timeout
        self._log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log = open(log_path, "a", encoding="utf-8", buffering=1)
        self.process = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            bufsize=1,
            start_new_session=os.name != "nt",
        )
        if self.process.stdin is None or self.process.stdout is None or self.process.stderr is None:
            self.process.kill()
            raise RuntimeError("cua_repl stdio is unavailable")
        self._stdout_thread = threading.Thread(
            target=self._stdout_loop,
            name="nexum-browser-cua-stdout",
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._stderr_loop,
            name="nexum-browser-cua-stderr",
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

    @property
    def allowed_tools(self) -> set[str]:
        with self._state_lock:
            return set(self._allowed_tools)

    def initialize(self) -> dict[str, Any]:
        result = self.request(
            "initialize",
            {
                "protocolVersion": _PROTOCOL_VERSION,
                "capabilities": {"elicitation": {}},
                "clientInfo": {"name": "nexum-browser", "version": "0.4.0"},
            },
            timeout=self._startup_timeout,
        )
        negotiated = result.get("protocolVersion")
        if negotiated != _PROTOCOL_VERSION:
            raise McpError(
                "cua_repl negotiated unsupported MCP protocol version: "
                f"{negotiated!r}; expected {_PROTOCOL_VERSION}"
            )
        self.notify("notifications/initialized", {})
        self.refresh_tools(timeout=self._startup_timeout)
        return result

    def refresh_tools(self, *, timeout: float | None = None) -> set[str]:
        result = self.request("tools/list", {}, timeout=timeout or self._startup_timeout)
        tools = result.get("tools") or []
        names = {
            str(item.get("name"))
            for item in tools
            if isinstance(item, dict) and item.get("name")
        }
        allowed = names & self._configured_tools & _INTERNAL_TOOL_ALLOWLIST
        missing = _INTERNAL_TOOL_ALLOWLIST - allowed
        if missing:
            raise RuntimeError(
                "cua_repl is missing required enabled tools: " + ", ".join(sorted(missing))
            )
        with self._state_lock:
            self._tool_names = names
            self._allowed_tools = allowed
            self._tools_dirty = False
        return allowed

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        meta: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        with self._state_lock:
            dirty = self._tools_dirty
        if dirty:
            self.refresh_tools()
        if name not in self.allowed_tools:
            raise RuntimeError(f"cua_repl tool is not enabled for nexum-browser: {name}")
        params: dict[str, Any] = {"name": name, "arguments": arguments}
        if meta:
            params["_meta"] = meta
        return self.request("tools/call", params, timeout=timeout)

    def request(
        self,
        method: str,
        params: dict[str, Any],
        *,
        timeout: float | None,
    ) -> dict[str, Any]:
        with self._state_lock:
            if self._closed.is_set():
                raise McpError("cua_repl connection is closed")
            self._next_request_id += 1
            request_id = self._next_request_id
            pending = _PendingRequest()
            self._pending[request_id] = pending
        try:
            self._send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": method,
                    "params": params,
                }
            )
        except Exception:
            with self._state_lock:
                self._pending.pop(request_id, None)
            raise
        completed = pending.event.wait(timeout)
        if not completed:
            with self._state_lock:
                self._pending.pop(request_id, None)
            with self._write_lock:
                if not self._closed.is_set():
                    self._write_json(
                        {
                            "jsonrpc": "2.0",
                            "method": "notifications/cancelled",
                            "params": {
                                "requestId": request_id,
                                "reason": f"nexum-browser timed out waiting for {method}",
                            },
                        }
                    )
            raise TimeoutError(f"Timed out waiting for cua_repl method {method}")
        if pending.error is not None:
            raise McpError(str(pending.error))
        response = pending.response or {}
        if "error" in response:
            error = response.get("error")
            if isinstance(error, dict):
                message = str(error.get("message") or error)
            else:
                message = str(error)
            raise McpError(message)
        result = response.get("result")
        return result if isinstance(result, dict) else {}

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def pending_elicitation(self) -> PendingElicitation | None:
        with self._state_lock:
            return next(iter(self._elicitations.values()), None)

    def respond_elicitation(
        self,
        elicitation_id: str,
        *,
        action: str,
        content: dict[str, Any] | None = None,
    ) -> None:
        if action not in {"accept", "decline", "cancel"}:
            raise ValueError(f"Unsupported elicitation action: {action}")
        with self._state_lock:
            elicitation = self._elicitations.pop(elicitation_id, None)
            if elicitation is None:
                raise RuntimeError(f"Unknown or resolved elicitation: {elicitation_id}")
        result: dict[str, Any] = {"action": action}
        if content is not None:
            result["content"] = content
        self._send(
            {
                "jsonrpc": "2.0",
                "id": elicitation.request_id,
                "result": result,
            }
        )

    def close(self) -> None:
        self._closed.set()
        process = self.process
        if process.poll() is None:
            try:
                if os.name == "nt":
                    process.terminate()
                else:
                    os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=3)
            except Exception:
                try:
                    if os.name == "nt":
                        process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                except Exception:
                    pass
        self._fail_pending(McpError("cua_repl connection closed"))
        current = threading.current_thread()
        for thread in (self._stdout_thread, self._stderr_thread):
            if thread is not current and thread.is_alive():
                thread.join(timeout=0.5)
        try:
            if not self._log.closed:
                self._log.close()
        except Exception:
            pass

    def _send(self, message: dict[str, Any]) -> None:
        with self._write_lock:
            if self._closed.is_set():
                raise McpError("cua_repl connection is closed")
            self._write_json(message)

    def _write_json(self, message: dict[str, Any]) -> None:
        if self.process.stdin is None:
            raise McpError("cua_repl stdin is unavailable")
        try:
            self.process.stdin.write(
                json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise McpError("cua_repl stdin closed") from exc

    def _stdout_loop(self) -> None:
        assert self.process.stdout is not None
        try:
            for raw in self.process.stdout:
                line = raw.strip()
                if not line:
                    continue
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    self._log.write(f"[cua_repl stdout] {line}\n")
                    continue
                if not isinstance(message, dict):
                    continue
                self._dispatch(message)
        finally:
            self._closed.set()
            return_code = self.process.poll()
            self._fail_pending(
                McpError(
                    "cua_repl exited"
                    + (f" with code {return_code}" if return_code is not None else "")
                )
            )

    def _stderr_loop(self) -> None:
        assert self.process.stderr is not None
        for raw in self.process.stderr:
            self._log.write(raw)

    def _dispatch(self, message: dict[str, Any]) -> None:
        request_id = message.get("id")
        method = message.get("method")
        if request_id is not None and method is None:
            with self._state_lock:
                pending = self._pending.pop(int(request_id), None) if isinstance(request_id, int) else None
            if pending is not None:
                pending.response = message
                pending.event.set()
            return
        if request_id is not None and isinstance(method, str):
            self._handle_server_request(message)
            return
        if isinstance(method, str):
            if method == "notifications/tools/list_changed":
                with self._state_lock:
                    self._tools_dirty = True
            elif method == "notifications/cancelled":
                params = message.get("params") or {}
                cancelled = params.get("requestId")
                if isinstance(cancelled, int):
                    with self._state_lock:
                        pending = self._pending.pop(cancelled, None)
                    if pending is not None:
                        pending.error = McpError(
                            str(params.get("reason") or "cua_repl cancelled the request")
                        )
                        pending.event.set()

    def _handle_server_request(self, message: dict[str, Any]) -> None:
        method = str(message.get("method") or "")
        request_id = message.get("id")
        if not isinstance(request_id, (int, str)):
            return
        if method != "elicitation/create":
            self._send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unsupported server request: {method}"},
                }
            )
            return
        params = message.get("params")
        if not isinstance(params, dict):
            self._send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Invalid elicitation params"},
                }
            )
            return
        elicitation_id = "el_" + uuid.uuid4().hex
        pending = PendingElicitation(elicitation_id, request_id, params)
        with self._state_lock:
            self._elicitations[elicitation_id] = pending

    def _fail_pending(self, error: BaseException) -> None:
        with self._state_lock:
            pending = list(self._pending.values())
            self._pending.clear()
        for item in pending:
            item.error = error
            item.event.set()
