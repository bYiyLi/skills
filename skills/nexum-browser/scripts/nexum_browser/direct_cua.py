from __future__ import annotations

import base64
import contextlib
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import sys
import uuid
from typing import Any

from .common import (
    LOG_PATH,
    MARKER,
    PUBLIC_API_SURFACES,
    build_public_api_contract,
    codex_home,
)
from .mcp import PendingElicitation, StdioMcpClient


_BACKEND = "direct-cua"
_REQUIRED_TOOLS = {"js", "js_reset", "turn_ended"}
_DEFAULT_STARTUP_TIMEOUT = 120.0


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
    api_json: Path

    def summary(self) -> dict[str, Any]:
        return {
            "backend": _BACKEND,
            "source": str(self.config_path),
            "runtimeVersion": self.runtime_version,
            "command": self.command,
            "browserEnv": self.browser_env,
            "nodeRepl": str(self.node_repl),
            "apiJson": str(self.api_json),
            "enabledTools": sorted(self.enabled_tools),
        }


def is_direct_cua_platform() -> bool:
    return sys.platform == "darwin"


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
    if candidate.is_file() and os.access(candidate, os.X_OK):
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
    if not isinstance(raw_args, list) or not all(isinstance(item, str) for item in raw_args):
        raise RuntimeError(f"cua_repl args are invalid in {path}")
    command = _resolve_command(raw_command)
    args = tuple(raw_args)
    entry = next((Path(item).expanduser() for item in args if "cua-repl" in item), None)
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
    if not isinstance(env_vars, list) or not all(isinstance(item, str) for item in env_vars):
        raise RuntimeError(f"cua_repl env_vars is invalid in {path}")
    for name in env_vars:
        if name not in os.environ:
            raise RuntimeError(f"Required cua_repl environment variable is unavailable: {name}")
        env[name] = os.environ[name]

    node_repl_raw = env.get("CUA_REPL_NODE_REPL_PATH")
    if not node_repl_raw:
        raise RuntimeError("CUA_REPL_NODE_REPL_PATH is missing from the launch contract")
    node_repl = Path(node_repl_raw).expanduser()
    if not node_repl.is_file() or not os.access(node_repl, os.X_OK):
        raise RuntimeError(f"CUA_REPL_NODE_REPL_PATH is not executable: {node_repl}")

    surfaces = {
        item.strip()
        for item in str(env.get("CUA_REPL_ENABLED_SURFACES") or "").split(",")
        if item.strip()
    }
    if "browser" not in surfaces:
        raise RuntimeError("CUA_REPL_ENABLED_SURFACES does not enable browser")

    modules_raw = str(env.get("NODE_REPL_NODE_MODULE_DIRS") or "")
    node_modules = tuple(
        Path(item).expanduser() for item in modules_raw.split(os.pathsep) if item
    )
    if not node_modules or not all(item.is_dir() for item in node_modules):
        raise RuntimeError("NODE_REPL_NODE_MODULE_DIRS does not contain valid directories")

    browser_env = str(env.get("CUA_REPL_BROWSER_ENV") or "codex-app")
    api_json = next(
        (
            root / "@oai/browser-desktop/environment-docs" / browser_env / "api.json"
            for root in node_modules
            if (root / "@oai/browser-desktop/environment-docs" / browser_env / "api.json").is_file()
        ),
        None,
    )
    if api_json is None:
        raise RuntimeError(
            f"Browser Runtime api.json was not found for environment {browser_env}"
        )

    raw_tools = config.get("enabled_tools") or []
    if not isinstance(raw_tools, list) or not all(isinstance(item, str) for item in raw_tools):
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
        startup_timeout=float(config.get("startup_timeout_sec") or _DEFAULT_STARTUP_TIMEOUT),
        browser_env=browser_env,
        node_modules=node_modules,
        node_repl=node_repl,
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
        raise RuntimeError("No valid cua_repl launch contract was found. " + " | ".join(errors))
    root = codex_home() / "plugins/cache/openai-bundled/unified-computer-use"
    raise RuntimeError(f"OpenAI unified-computer-use .mcp.json was not found under {root}")


def direct_runtime_diagnostics() -> dict[str, Any]:
    try:
        contract = discover_launch_contract()
    except Exception as exc:
        return {"available": False, "backend": _BACKEND, "error": str(exc)}
    return {"available": True, **contract.summary()}


def direct_api_manifest_path() -> Path:
    return discover_launch_contract().api_json


class DirectCuaRuntime:
    """Persistent direct cua_repl runtime with the legacy execute_js adapter contract."""

    backend = _BACKEND
    fallback_reason: str | None = None

    def __init__(self) -> None:
        if not is_direct_cua_platform():
            raise RuntimeError("direct cua_repl is currently enabled only on macOS")
        self.contract = discover_launch_contract()
        self.session_id = "nexum-browser-" + uuid.uuid4().hex
        self.turn_id = "browser-turn-" + uuid.uuid4().hex
        self.runtime_state = "fresh"
        self.handle_generation = 1
        self._bridge_installed = False
        self._released = False
        self.client = StdioMcpClient(
            command=self.contract.command,
            args=list(self.contract.args),
            env=self.contract.env,
            configured_tools=set(self.contract.enabled_tools),
            log_path=LOG_PATH,
            startup_timeout=self.contract.startup_timeout,
        )
        try:
            self.client.initialize()
        except Exception:
            self.client.close()
            raise

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

    def execute_js(
        self,
        code: str,
        *,
        title: str = "Browser action",
        timeout_ms: int = 30000,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        self._ensure_initialized()
        return self._execute_js_once(code, title=title, timeout_ms=timeout_ms)

    def _ensure_initialized(self) -> None:
        if self.runtime_state == "fresh":
            result = self.client.call_tool(
                "js",
                {
                    "code": "await cua.getState({emit:false})",
                    "timeout_ms": 30000,
                    "title": "Initialize browser runtime",
                },
                meta=self._meta(),
                timeout=None,
            )
            self._raise_tool_error(result)
            self.runtime_state = "initialized"
        if not self._bridge_installed:
            result = self.client.call_tool(
                "js",
                {
                    "code": self._bridge_code(),
                    "timeout_ms": int(self.contract.startup_timeout * 1000),
                    "title": "Initialize browser adapter",
                },
                meta=self._meta(),
                timeout=None,
            )
            self._raise_tool_error(result)
            self._bridge_installed = True

    def _execute_js_once(
        self,
        code: str,
        *,
        title: str,
        timeout_ms: int,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        result = self.client.call_tool(
            "js",
            {"code": code, "timeout_ms": timeout_ms, "title": title[:80]},
            meta=self._meta(),
            timeout=None,
        )
        content = result.get("content") or []
        self._raise_tool_error(result)
        return self._decode_structured_result(content), content

    @staticmethod
    def _raise_tool_error(result: dict[str, Any]) -> None:
        if not result.get("isError"):
            return
        texts = [
            str(item.get("text") or "")
            for item in result.get("content") or []
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        raise RuntimeError(
            "\n".join(text for text in texts if text).strip()
            or "Browser runtime returned an error"
        )

    @staticmethod
    def _decode_structured_result(content: list[dict[str, Any]]) -> dict[str, Any]:
        texts = [
            str(item.get("text") or "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
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
                return candidate
        message = "\n".join(text for text in texts if text).strip()
        raise RuntimeError(message or "Browser runtime did not return a structured result")

    def reset(self) -> None:
        result = self.client.call_tool("js_reset", {}, meta=self._meta(), timeout=30)
        self._raise_tool_error(result)
        self.runtime_state = "fresh"
        self._bridge_installed = False
        self.handle_generation += 1

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        with contextlib.suppress(Exception):
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

    def close(self) -> None:
        self.client.close()

    def _bridge_code(self) -> str:
        public_api = build_public_api_contract()
        surfaces = PUBLIC_API_SURFACES
        generation = self.handle_generation
        return f"""
globalThis.__nexumBrowserAgent = globalThis.agent;
if (globalThis.__nexumBrowserAgent == null) throw new Error('Browser Runtime Agent surface is unavailable');
globalThis.__nexumPublicApi = {json.dumps(public_api, separators=(',', ':'))};
globalThis.__nexumPublicSurfaces = {json.dumps(surfaces, separators=(',', ':'))};
globalThis.__nexumHandleGeneration = {generation};
globalThis.__nexumBrowserHandles = new Map();
globalThis.__nexumBrowserHandleMeta = new Map();
globalThis.__nexumBrowserHandleSeq = 0;

globalThis.__nexumStoreHandle = (value, interfaceHint = null, extra = {{}}) => {{
  const id = 'g' + globalThis.__nexumHandleGeneration + ':h_' + (++globalThis.__nexumBrowserHandleSeq);
  let resolvedInterface = interfaceHint || null;
  if (resolvedInterface === 'Dialog' && value && typeof value.type === 'string') {{
    resolvedInterface = {{alert:'AlertDialog',beforeunload:'BeforeUnloadDialog',confirm:'ConfirmDialog',prompt:'PromptDialog'}}[value.type] || resolvedInterface;
  }}
  globalThis.__nexumBrowserHandles.set(id, value);
  const meta = {{interface: resolvedInterface, ...extra}};
  globalThis.__nexumBrowserHandleMeta.set(id, meta);
  return {{handle:id, ...(resolvedInterface ? {{interface:resolvedInterface}} : {{}}), ...(meta.binary ? {{binary:true,byteLength:meta.byteLength}} : {{}})}};
}};

globalThis.__nexumInflate = (value) => {{
  if (Array.isArray(value)) return value.map(globalThis.__nexumInflate);
  if (value && typeof value === 'object') {{
    if (typeof value.$handle === 'string') {{
      if (!globalThis.__nexumBrowserHandles.has(value.$handle)) throw new Error('Unknown or stale browser handle: ' + value.$handle);
      return globalThis.__nexumBrowserHandles.get(value.$handle);
    }}
    if (value.$call != null) {{
      const descriptor = value.$call;
      if (descriptor == null || typeof descriptor !== 'object' || Array.isArray(descriptor)) throw new Error('$call must contain a public Browser API call descriptor');
      return async () => await globalThis.__nexumInvokeDescriptor(descriptor);
    }}
    return Object.fromEntries(Object.entries(value).map(([key,item]) => [key,globalThis.__nexumInflate(item)]));
  }}
  return value;
}};

globalThis.__nexumSerialize = (value, depth = 0, interfaceHint = null) => {{
  if (value === undefined || value === null) return value ?? null;
  if (['string','number','boolean'].includes(typeof value)) return value;
  if (typeof value === 'bigint') return value.toString();
  if (value instanceof Uint8Array) return globalThis.__nexumStoreHandle(value, null, {{binary:true,byteLength:value.byteLength}});
  if (depth >= 5) return {{truncated:true}};
  if (Array.isArray(value)) return value.map(item => globalThis.__nexumSerialize(item, depth + 1, interfaceHint));
  if (typeof value === 'function') return globalThis.__nexumStoreHandle(value, interfaceHint);
  if (typeof value === 'object') {{
    const proto = Object.getPrototypeOf(value);
    if (proto && proto !== Object.prototype && proto?.constructor?.name !== 'Object') return globalThis.__nexumStoreHandle(value, interfaceHint);
    const out = {{}};
    for (const [key,item] of Object.entries(value)) out[key] = globalThis.__nexumSerialize(item, depth + 1);
    return out;
  }}
  return String(value);
}};

globalThis.__nexumResolvePath = (receiver, path) => {{
  const parts = path.split('.');
  let owner = receiver;
  for (let index = 0; index < parts.length - 1; index++) owner = owner[parts[index]];
  return {{owner,member:owner[parts[parts.length - 1]]}};
}};

globalThis.__nexumPublicCall = (interfaceName, path, args) => {{
  if (!interfaceName) return {{returnInterface:null}};
  const parts = path.split('.');
  let currentInterface = interfaceName;
  let returnInterface = null;
  for (let index = 0; index < parts.length; index++) {{
    const members = globalThis.__nexumPublicApi.interfaces[currentInterface];
    const member = members != null && Object.prototype.hasOwnProperty.call(members, parts[index]) ? members[parts[index]] : null;
    if (!member) throw new Error('Browser API member is not public: ' + currentInterface + '.' + parts[index]);
    let candidates = member.returns || [];
    if (currentInterface === 'PlaywrightAPI' && parts[index] === 'waitForEvent') {{
      if (args?.[0] === 'download') candidates = ['PlaywrightDownload'];
      else if (args?.[0] === 'filechooser') candidates = ['PlaywrightFileChooser'];
    }}
    returnInterface = candidates[0] || null;
    if (index < parts.length - 1) {{
      const next = candidates.find(name => globalThis.__nexumPublicApi.interfaces[name]);
      if (!next) throw new Error('Browser API path cannot continue through ' + currentInterface + '.' + parts[index]);
      currentInterface = next;
    }}
  }}
  return {{returnInterface}};
}};

globalThis.__nexumCallRaw = async (receiver, interfaceName, path, args) => {{
  globalThis.__nexumPublicCall(interfaceName, path, args);
  const resolved = globalThis.__nexumResolvePath(receiver, path);
  const inflated = globalThis.__nexumInflate(args);
  return await (typeof resolved.member === 'function' ? resolved.member.apply(resolved.owner, inflated) : resolved.member);
}};

globalThis.__nexumCall = async (receiver, interfaceName, path, args, awaitResult = true) => {{
  const info = globalThis.__nexumPublicCall(interfaceName, path, args);
  const resolved = globalThis.__nexumResolvePath(receiver, path);
  const inflated = globalThis.__nexumInflate(args);
  let result = typeof resolved.member === 'function' ? resolved.member.apply(resolved.owner, inflated) : resolved.member;
  if (!awaitResult) {{
    const guarded = Promise.resolve(result).then(
      value => ({{__nexumPromise:true,ok:true,value}}),
      error => ({{__nexumPromise:true,ok:false,error:{{message:String(error?.message || error),name:String(error?.name || 'Error')}}}})
    );
    return globalThis.__nexumStoreHandle(guarded, null, {{promise:true,resolvedInterface:info.returnInterface}});
  }}
  result = await result;
  return globalThis.__nexumSerialize(result, 0, info.returnInterface);
}};

globalThis.__nexumCallHandle = async (handleId, path, args, awaitResult = true) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error('Unknown or stale browser handle: ' + handleId);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  if (!meta.interface) throw new Error('Browser handle ' + handleId + ' has no documented public interface');
  return await globalThis.__nexumCall(globalThis.__nexumBrowserHandles.get(handleId), meta.interface, path, args, awaitResult);
}};
globalThis.__nexumCallHandleRaw = async (handleId, path, args) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error('Unknown or stale browser handle: ' + handleId);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  if (!meta.interface) throw new Error('Browser handle ' + handleId + ' has no documented public interface');
  return await globalThis.__nexumCallRaw(globalThis.__nexumBrowserHandles.get(handleId), meta.interface, path, args);
}};

globalThis.__nexumResolveDescriptorTarget = async (descriptor) => {{
  const surface = descriptor.surface;
  if (surface === 'handle') {{
    const handleId = descriptor.handle;
    if (typeof handleId !== 'string' || !globalThis.__nexumBrowserHandles.has(handleId)) throw new Error('Unknown or stale browser handle: ' + String(handleId));
    const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
    if (!meta.interface) throw new Error('Browser handle ' + handleId + ' has no documented public interface');
    return {{receiver:globalThis.__nexumBrowserHandles.get(handleId),interfaceName:meta.interface}};
  }}
  if (surface === 'browser-capability' || surface === 'tab-capability') {{
    const capability = descriptor.capability;
    if (typeof capability !== 'string' || !capability) throw new Error('capability is required for callback surface ' + surface);
    let collection;
    if (surface === 'tab-capability') {{
      if (typeof descriptor.tab !== 'string' || !descriptor.tab) throw new Error('tab is required for callback surface tab-capability');
      collection = (await globalThis.__nexumBrowser.tabs.get(descriptor.tab)).capabilities;
    }} else collection = globalThis.__nexumBrowser.capabilities;
    const advertised = await collection.list();
    if (!advertised.some(item => item?.id === capability)) throw new Error('Browser capability ' + capability + ' is unavailable on the selected backend');
    const receiver = await collection.get(capability);
    try {{ await receiver.documentation(); }} catch {{}}
    return {{receiver,interfaceName:null,dynamicCapability:true}};
  }}
  const interfaceName = globalThis.__nexumPublicSurfaces[surface];
  if (!interfaceName) throw new Error('Unsupported callback Browser API surface: ' + String(surface));
  if (surface === 'agent') return {{receiver:globalThis.__nexumBrowserAgent,interfaceName}};
  if (surface === 'browsers-api') return {{receiver:globalThis.__nexumBrowserAgent.browsers,interfaceName}};
  if (surface === 'docs-api') return {{receiver:globalThis.__nexumBrowserAgent.documentation,interfaceName}};
  if (surface === 'browser') return {{receiver:globalThis.__nexumBrowser,interfaceName}};
  if (surface === 'tabs') return {{receiver:globalThis.__nexumBrowser.tabs,interfaceName}};
  if (surface === 'user') {{
    if (globalThis.__nexumBrowser.user == null) throw new Error('Browser API surface user is unavailable on the selected backend');
    return {{receiver:globalThis.__nexumBrowser.user,interfaceName}};
  }}
  if (typeof descriptor.tab !== 'string' || !descriptor.tab) throw new Error('tab is required for callback surface ' + surface);
  const tab = await globalThis.__nexumBrowser.tabs.get(descriptor.tab);
  const receiver = {{tab,playwright:tab.playwright,cua:tab.cua,'dom-cua':tab.dom_cua,ax:tab.ax,content:tab.content,clipboard:tab.clipboard,dev:tab.dev}}[surface];
  if (receiver == null) throw new Error('Browser API surface ' + surface + ' is unavailable on the selected backend');
  return {{receiver,interfaceName}};
}};

globalThis.__nexumInvokeDescriptor = async (descriptor) => {{
  if (typeof descriptor.method !== 'string' || !descriptor.method) throw new Error('$call descriptor requires a public method');
  if (descriptor.args != null && !Array.isArray(descriptor.args)) throw new Error('$call descriptor args must be an array');
  const target = await globalThis.__nexumResolveDescriptorTarget(descriptor);
  if (target.dynamicCapability) {{
    if (descriptor.method.includes('.')) throw new Error('Optional capability callbacks must use one documented member name at a time');
    if (!/^[A-Za-z_$][A-Za-z0-9_$]*$/.test(descriptor.method) || ['constructor','prototype','__proto__'].includes(descriptor.method)) throw new Error('Optional capability callback member is invalid: ' + descriptor.method);
    if (!(descriptor.method in target.receiver)) throw new Error('Browser capability member is unavailable: ' + descriptor.method);
  }}
  return await globalThis.__nexumCallRaw(target.receiver, target.interfaceName, descriptor.method, descriptor.args || []);
}};

globalThis.__nexumAwaitHandle = async (handleId) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error('Unknown or stale browser handle: ' + handleId);
  const meta = globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}};
  if (!meta.promise) throw new Error('Browser handle ' + handleId + ' is not an asynchronous result');
  const settled = await globalThis.__nexumBrowserHandles.get(handleId);
  if (settled?.__nexumPromise && !settled.ok) throw new Error(settled.error?.message || 'Browser promise rejected');
  return globalThis.__nexumSerialize(settled?.__nexumPromise ? settled.value : settled, 0, meta.resolvedInterface || null);
}};
globalThis.__nexumHandleInfo = (handleId) => {{
  if (!globalThis.__nexumBrowserHandles.has(handleId)) throw new Error('Unknown or stale browser handle: ' + handleId);
  return {{handle:handleId,...(globalThis.__nexumBrowserHandleMeta.get(handleId) || {{}})}};
}};

globalThis.__nexumReadDoc = async (name) => await globalThis.__nexumBrowserAgent.documentation.get(name);
globalThis.__nexumSelectBrowser = async (mode, value) => {{
  let browser;
  if (mode === 'default') browser = await cua.getBrowser();
  else if (mode === 'url') browser = await cua.getBrowser({{url:value}});
  else browser = await cua.getBrowser({{id:value}});
  globalThis.__nexumBrowser = browser;
  const infos = await cua.listBrowsers({{emit:false}});
  const info = infos.find(item => item.id === browser.browserId) || {{id:browser.browserId}};
  if (info.type === 'extension' && typeof browser.nameSession === 'function') {{
    try {{ await browser.nameSession('🔎 Nexum Browser'); }} catch {{}}
  }}
  return info;
}};
await globalThis.__nexumSelectBrowser('default', null);
"""
