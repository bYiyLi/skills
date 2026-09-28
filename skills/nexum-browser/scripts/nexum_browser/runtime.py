from __future__ import annotations

import contextlib
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import uuid
from typing import Any

from .common import LOG_PATH, codex_home, is_executable_file
from .mcp import PendingElicitation, StdioMcpClient


_REQUIRED_TOOLS = frozenset({"js", "js_reset", "turn_ended"})
_DEFAULT_STARTUP_TIMEOUT = 120.0
_BOOTSTRAP_RETRY_PREFIX = "NEXUM_BROWSER_BOOTSTRAP_RETRY:"
_BOOTSTRAP_RETRY_MARKER = "__NEXUM_BROWSER_BOOTSTRAP_RETRY_MARKER__"
_BOOTSTRAP_ATTEMPTS = 5
_BOOTSTRAP = 'await import("@oai/cua/tinyskyAlt");'
_BOOTSTRAP_WITH_READINESS = r'''await import("@oai/cua/tinyskyAlt");
{
  let __nexumProbeTab;
  try {
    let __nexumBrowsers = await agent.browsers.list();
    let __nexumInfo =
      __nexumBrowsers.find(__nexumItem => __nexumItem.type === "extension")
      || __nexumBrowsers[0];
    if (__nexumInfo != null) {
      let __nexumBrowser = await agent.browsers.get(__nexumInfo.id);
      __nexumProbeTab = await __nexumBrowser.tabs.new();
    }
  } catch (__nexumError) {
    let __nexumMessage = String(__nexumError?.message || __nexumError);
    if (__nexumMessage.includes(
      "Unable to load browser request-header policy"
    )) {
      throw new Error(
        __NEXUM_BROWSER_BOOTSTRAP_RETRY_MARKER__ + __nexumMessage
      );
    }
    throw __nexumError;
  } finally {
    if (__nexumProbeTab != null) {
      await __nexumProbeTab.close();
    }
  }
}'''


class CuaToolError(RuntimeError):
    def __init__(self, message: str, result: dict[str, Any]) -> None:
        super().__init__(message)
        self.result = result


@dataclass(frozen=True)
class CuaLaunchContract:
    config_path: Path
    runtime_version: str
    command: str
    args: tuple[str, ...]
    env: dict[str, str]
    enabled_tools: frozenset[str]
    startup_timeout: float
    browser_env: str
    node_modules: tuple[Path, ...]
    node_repl: Path
    node_path: Path
    api_json: Path

    def summary(self) -> dict[str, Any]:
        if self.env.get("NODE_REPL_JS_BANNER") == "":
            banner_mode = "empty-override"
        elif "NODE_REPL_JS_BANNER" in self.env:
            banner_mode = "launch-contract"
        else:
            banner_mode = "runtime-default"
        return {
            "backend": "direct-cua",
            "source": str(self.config_path),
            "runtimeVersion": self.runtime_version,
            "command": self.command,
            "browserEnv": self.browser_env,
            "nodePath": str(self.node_path),
            "nodeRepl": str(self.node_repl),
            "apiJson": str(self.api_json),
            "enabledTools": sorted(self.enabled_tools),
            "startupBannerMode": banner_mode,
        }


def _candidate_configs() -> list[Path]:
    override = os.environ.get("NEXUM_BROWSER_CUA_MCP")
    if override:
        return [Path(override).expanduser()]

    root = codex_home() / "plugins/cache/openai-bundled/unified-computer-use"
    return sorted(
        root.glob("*/.mcp.json"),
        key=lambda path: path.stat().st_mtime_ns if path.exists() else 0,
        reverse=True,
    )


def _resolve_command(value: str) -> str:
    candidate = Path(value).expanduser()
    if is_executable_file(candidate):
        return str(candidate)
    found = shutil.which(value)
    if found:
        return found
    raise RuntimeError(f"cua_repl command is not executable: {value}")


def _read_contract(path: Path) -> CuaLaunchContract:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to read cua_repl launch contract: {path}") from exc

    servers = value.get("mcpServers") if isinstance(value, dict) else None
    config = servers.get("cua_repl") if isinstance(servers, dict) else None
    if not isinstance(config, dict) or config.get("enabled") is False:
        raise RuntimeError(f"cua_repl is not enabled in {path}")

    raw_command = config.get("command")
    raw_args = config.get("args")
    if not isinstance(raw_command, str) or not raw_command:
        raise RuntimeError(f"cua_repl command is missing in {path}")
    if not isinstance(raw_args, list) or not all(
        isinstance(item, str) for item in raw_args
    ):
        raise RuntimeError(f"cua_repl args are invalid in {path}")

    command = _resolve_command(raw_command)
    args = tuple(raw_args)
    entry = next(
        (Path(item).expanduser() for item in args if "cua-repl" in item.lower()),
        None,
    )
    if entry is None or not entry.is_file():
        raise RuntimeError(f"cua_repl entrypoint is missing in {path}")

    raw_env = config.get("env") or {}
    if not isinstance(raw_env, dict):
        raise RuntimeError(f"cua_repl env is invalid in {path}")
    env = os.environ.copy()
    for name, raw in raw_env.items():
        if raw is None:
            env.pop(str(name), None)
        else:
            env[str(name)] = str(raw)

    env_vars = config.get("env_vars") or []
    if not isinstance(env_vars, list) or not all(
        isinstance(item, str) for item in env_vars
    ):
        raise RuntimeError(f"cua_repl env_vars is invalid in {path}")
    for name in env_vars:
        if name not in os.environ:
            raise RuntimeError(
                f"Required cua_repl environment variable is unavailable: {name}"
            )
        env[name] = os.environ[name]

    # Keep OpenAI's generated launch contract intact except for this one
    # compatibility override. CUA is initialized inside the first authenticated
    # js tool call instead of during Node REPL startup.
    env["NODE_REPL_JS_BANNER"] = ""

    node_repl_raw = env.get("CUA_REPL_NODE_REPL_PATH")
    if not node_repl_raw:
        raise RuntimeError("CUA_REPL_NODE_REPL_PATH is missing from the launch contract")
    node_repl = Path(node_repl_raw).expanduser()
    if not is_executable_file(node_repl):
        raise RuntimeError(f"CUA_REPL_NODE_REPL_PATH is not executable: {node_repl}")

    node_path_raw = env.get("NODE_REPL_NODE_PATH") or command
    node_path = Path(node_path_raw).expanduser()
    if not is_executable_file(node_path):
        raise RuntimeError(f"NODE_REPL_NODE_PATH is not executable: {node_path}")

    surfaces = {
        item.strip()
        for item in str(env.get("CUA_REPL_ENABLED_SURFACES") or "").split(",")
        if item.strip()
    }
    if "browser" not in surfaces:
        raise RuntimeError("CUA_REPL_ENABLED_SURFACES does not enable browser")

    module_text = str(env.get("NODE_REPL_NODE_MODULE_DIRS") or "")
    node_modules = tuple(
        Path(item).expanduser()
        for item in module_text.split(os.pathsep)
        if item
    )
    if not node_modules or not all(item.is_dir() for item in node_modules):
        raise RuntimeError(
            "NODE_REPL_NODE_MODULE_DIRS does not contain valid directories"
        )

    browser_env = str(env.get("CUA_REPL_BROWSER_ENV") or "codex-app")
    api_json = next(
        (
            root
            / "@oai/browser-desktop/environment-docs"
            / browser_env
            / "api.json"
            for root in node_modules
            if (
                root
                / "@oai/browser-desktop/environment-docs"
                / browser_env
                / "api.json"
            ).is_file()
        ),
        None,
    )
    if api_json is None:
        raise RuntimeError(
            f"Browser Runtime api.json was not found for environment {browser_env}"
        )

    raw_tools = config.get("enabled_tools") or []
    if not isinstance(raw_tools, list) or not all(
        isinstance(item, str) for item in raw_tools
    ):
        raise RuntimeError(f"cua_repl enabled_tools is invalid in {path}")
    enabled_tools = frozenset(raw_tools)
    missing = _REQUIRED_TOOLS - enabled_tools
    if missing:
        raise RuntimeError(
            "cua_repl launch contract does not enable required tools: "
            + ", ".join(sorted(missing))
        )

    return CuaLaunchContract(
        config_path=path,
        runtime_version=path.parent.name,
        command=command,
        args=args,
        env=env,
        enabled_tools=enabled_tools,
        startup_timeout=float(
            config.get("startup_timeout_sec") or _DEFAULT_STARTUP_TIMEOUT
        ),
        browser_env=browser_env,
        node_modules=node_modules,
        node_repl=node_repl,
        node_path=node_path,
        api_json=api_json,
    )


def discover_launch_contract() -> CuaLaunchContract:
    errors: list[str] = []
    for path in _candidate_configs():
        try:
            return _read_contract(path)
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    if errors:
        raise RuntimeError(
            "No valid cua_repl launch contract was found. " + " | ".join(errors)
        )
    root = codex_home() / "plugins/cache/openai-bundled/unified-computer-use"
    raise RuntimeError(
        f"OpenAI unified-computer-use .mcp.json was not found under {root}"
    )


def runtime_diagnostics() -> dict[str, Any]:
    try:
        return {"available": True, **discover_launch_contract().summary()}
    except Exception as exc:
        return {
            "available": False,
            "backend": "direct-cua",
            "error": str(exc),
        }


class CuaRuntime:
    """One persistent direct cua_repl MCP connection and Node REPL context."""

    backend = "direct-cua"

    def __init__(self, contract: CuaLaunchContract | None = None) -> None:
        self.contract = contract or discover_launch_contract()
        self.session_id = "nexum-browser-" + uuid.uuid4().hex
        self.turn_id = "browser-turn-" + uuid.uuid4().hex
        self.bootstrapped = False
        self.policy_ready = False
        self._released = False
        self.client, self.initialize_info = self._open_client()

    def _open_client(self) -> tuple[StdioMcpClient, dict[str, Any]]:
        client = StdioMcpClient(
            command=self.contract.command,
            args=list(self.contract.args),
            env=self.contract.env,
            configured_tools=set(self.contract.enabled_tools),
            log_path=LOG_PATH,
            startup_timeout=self.contract.startup_timeout,
        )
        try:
            initialize_info = client.initialize()
        except Exception:
            client.close()
            raise
        return client, initialize_info

    def _restart_after_bootstrap_failure(self) -> None:
        self.client.close()
        self.client, self.initialize_info = self._open_client()
        self.bootstrapped = False
        self.policy_ready = False

    @property
    def allowed_tools(self) -> set[str]:
        return self.client.allowed_tools

    def _meta(self) -> dict[str, str]:
        return {
            "x-codex-turn-metadata": json.dumps(
                {
                    "session_id": self.session_id,
                    "turn_id": self.turn_id,
                    "model": "nexum-browser",
                    "thread_source": "direct",
                },
                separators=(",", ":"),
            )
        }

    def pending_elicitation(self) -> PendingElicitation | None:
        return self.client.pending_elicitation()

    def respond_elicitation(
        self,
        elicitation_id: str,
        *,
        action: str,
        content: dict[str, Any] | None = None,
    ) -> None:
        self.client.respond_elicitation(
            elicitation_id,
            action=action,
            content=content,
        )

    def run(
        self,
        code: str,
        *,
        title: str = "Browser JavaScript",
        timeout_ms: int = 30000,
        rpc_timeout: float | None = None,
    ) -> dict[str, Any]:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("browser run requires non-empty JavaScript")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be greater than zero")

        bootstrap = not self.bootstrapped
        needs_readiness = bootstrap and not self.policy_ready
        attempts = _BOOTSTRAP_ATTEMPTS if needs_readiness else 1
        retry_marker = (
            _BOOTSTRAP_RETRY_PREFIX + uuid.uuid4().hex + ":"
            if needs_readiness
            else ""
        )
        if needs_readiness:
            bootstrap_code = _BOOTSTRAP_WITH_READINESS.replace(
                _BOOTSTRAP_RETRY_MARKER,
                json.dumps(retry_marker),
            )
        elif bootstrap:
            bootstrap_code = _BOOTSTRAP
        else:
            bootstrap_code = ""
        for attempt in range(attempts):
            actual_code = f"{bootstrap_code}\n{code}" if bootstrap else code
            result = self.client.call_tool(
                "js",
                {
                    "code": actual_code,
                    "timeout_ms": int(timeout_ms),
                    "title": title[:80],
                },
                meta=self._meta(),
                timeout=rpc_timeout,
            )
            try:
                self._raise_tool_error(result)
            except CuaToolError as exc:
                if (
                    needs_readiness
                    and str(exc).startswith(retry_marker)
                    and attempt + 1 < attempts
                ):
                    self._restart_after_bootstrap_failure()
                    continue
                if needs_readiness and str(exc).startswith(retry_marker):
                    message = str(exc)[len(retry_marker):]
                    raise CuaToolError(message, exc.result) from None
                raise
            self.bootstrapped = True
            if needs_readiness:
                self.policy_ready = True
            return result
        raise RuntimeError("Browser Runtime bootstrap retry loop exhausted")

    def reset(self) -> dict[str, Any]:
        result = self.client.call_tool(
            "js_reset",
            {},
            meta=self._meta(),
            timeout=30,
        )
        self._raise_tool_error(result)
        self.bootstrapped = False
        return result

    def release(self) -> dict[str, Any] | None:
        if self._released:
            return None
        result = self.client.call_tool(
            "turn_ended",
            {
                "hook_event_name": "Stop",
                "session_id": self.session_id,
                "turn_id": self.turn_id,
            },
            timeout=15,
        )
        self._raise_tool_error(result)
        self._released = True
        return result

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def _raise_tool_error(result: dict[str, Any]) -> None:
        if not result.get("isError"):
            return
        texts = [
            str(item.get("text") or "")
            for item in result.get("content") or []
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        messages = [text.strip() for text in texts if text.strip()]
        if messages:
            # First-use documentation can accompany an actual js error in the
            # same MCP result. Prefer the smallest text item so a concise
            # runtime error does not expand into pages of Browser docs.
            message = min(messages, key=len)
            if len(message) > 4000:
                message = message[:4000] + "\n...[truncated]"
        else:
            message = "Browser Runtime returned an error"
        raise CuaToolError(message, result)

    def shutdown(self) -> None:
        with contextlib.suppress(Exception):
            self.release()
        self.close()
