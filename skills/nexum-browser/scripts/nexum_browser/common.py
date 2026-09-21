from __future__ import annotations

import argparse
import base64
import contextlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import uuid
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = SKILL_ROOT / ".runtime"
SCREENSHOT_DIR = RUNTIME_DIR / "screenshots"
LOG_PATH = RUNTIME_DIR / "browser.log"
STATE_PATH = RUNTIME_DIR / "session.json"
BROKER_STATE_PATH = RUNTIME_DIR / "broker.json"
OPERATION_LOCK_PATH = RUNTIME_DIR / "operation.lock"
IDLE_SECONDS = int(os.environ.get("NEXUM_BROWSER_IDLE_SECONDS", "3600"))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("NEXUM_BROWSER_REQUEST_TIMEOUT_SECONDS", "45"))
LOCK_STALE_SECONDS = int(os.environ.get("NEXUM_BROWSER_LOCK_STALE_SECONDS", "900"))
MARKER = "NEXUM_JSON:"
_MEMBER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_FORBIDDEN_MEMBERS = {"constructor", "prototype", "__proto__"}
PUBLIC_API_SURFACES = {
    "agent": "Agent",
    "browsers-api": "Browsers",
    "docs-api": "Documentation",
    "browser": "Browser",
    "tabs": "Tabs",
    "user": "BrowserUser",
    "tab": "Tab",
    "playwright": "PlaywrightAPI",
    "cua": "CUAAPI",
    "dom-cua": "DomCUAAPI",
    "ax": "AXAPI",
    "content": "ContentAPI",
    "clipboard": "TabClipboardAPI",
    "dev": "TabDevAPI",
}
PUBLIC_API_ROOT_INTERFACES = set(PUBLIC_API_SURFACES.values())


@contextlib.contextmanager
def operation_lock(timeout: float = REQUEST_TIMEOUT_SECONDS + 15):
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    deadline = time.monotonic() + timeout
    acquired = False
    while not acquired:
        try:
            fd = os.open(OPERATION_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            try:
                age = time.time() - OPERATION_LOCK_PATH.stat().st_mtime
            except FileNotFoundError:
                continue
            if age > LOCK_STALE_SECONDS:
                with contextlib.suppress(FileNotFoundError):
                    OPERATION_LOCK_PATH.unlink()
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("Another nexum-browser operation is still running")
            time.sleep(0.05)
            continue
        try:
            os.write(fd, token.encode("ascii"))
        finally:
            os.close(fd)
        acquired = True
    try:
        yield
    finally:
        try:
            if OPERATION_LOCK_PATH.read_text(encoding="ascii") == token:
                OPERATION_LOCK_PATH.unlink()
        except (FileNotFoundError, OSError, UnicodeDecodeError):
            pass


def emit(value: dict[str, Any]) -> None:
    # Keep the CLI wire format ASCII-only so Windows hosts using a legacy
    # console code page cannot fail while emitting otherwise valid JSON.
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":")))


def fail(code: str, message: str, *, retryable: bool = False, exit_code: int = 1) -> None:
    emit({"code": code, "message": message, "retryable": retryable})
    raise SystemExit(exit_code)


def find_codex() -> Path:
    override = os.environ.get("NEXUM_BROWSER_CODEX")
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        found_override = shutil.which(override)
        if found_override:
            return Path(found_override)
        raise RuntimeError(f"NEXUM_BROWSER_CODEX is not executable: {override}")
    found = shutil.which("codex")
    if found:
        return Path(found)
    raise RuntimeError("Codex CLI was not found in PATH")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).expanduser()


def find_browser_plugin_root() -> Path:
    override = os.environ.get("NEXUM_BROWSER_PLUGIN_ROOT")
    if override:
        p = Path(override).expanduser()
        if (p / "scripts/browser-client.mjs").is_file():
            return p
        raise RuntimeError(f"NEXUM_BROWSER_PLUGIN_ROOT is not a Browser plugin root: {p}")
    root = codex_home() / "plugins/cache/openai-bundled/browser"
    candidates = [p.parent.parent for p in root.glob("*/scripts/browser-client.mjs") if p.is_file()]
    if not candidates:
        raise RuntimeError(f"OpenAI Browser plugin was not found under {root}")
    return max(candidates, key=lambda p: (p / "scripts/browser-client.mjs").stat().st_mtime_ns)


def find_browser_client() -> Path:
    override = os.environ.get("NEXUM_BROWSER_CLIENT")
    if override:
        p = Path(override).expanduser()
        if p.is_file():
            return p
        raise RuntimeError(f"NEXUM_BROWSER_CLIENT does not exist: {p}")
    return find_browser_plugin_root() / "scripts/browser-client.mjs"


def load_api_manifest() -> dict[str, Any]:
    if sys.platform == "darwin":
        from .direct_cua import direct_api_manifest_path

        p = direct_api_manifest_path()
    else:
        p = find_browser_plugin_root() / "docs/api.json"
    if not p.is_file():
        raise RuntimeError(f"Browser API manifest was not found: {p}")
    value = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Browser API manifest is not an object")
    return value


def build_public_api_contract() -> dict[str, Any]:
    manifest = load_api_manifest()
    interfaces = manifest.get("interfaces") or {}
    types = manifest.get("types") or {}
    interface_names = set(interfaces)

    aliases: dict[str, list[str]] = {}
    for name, value in types.items():
        if not isinstance(value, dict):
            continue
        refs = [ref for ref in value.get("references") or [] if ref in interface_names]
        if refs:
            aliases[name] = list(dict.fromkeys(refs))

    contract: dict[str, dict[str, dict[str, Any]]] = {}
    return_names = interface_names | set(aliases)
    for interface_name, members in interfaces.items():
        if not isinstance(members, dict):
            continue
        member_contract: dict[str, dict[str, Any]] = {}
        for member_name, member in members.items():
            if not isinstance(member, dict):
                continue
            returns: list[str] = []
            callback_kinds: list[str] = []
            for declaration in member.get("declarations") or []:
                if not isinstance(declaration, dict):
                    continue
                text = str(declaration.get("text") or "").split("//", 1)[0].strip()
                signature = text.rsplit("):", 1)[0] if "):" in text else text
                if "=>" in signature:
                    if re.search(r"\(\s*\)\s*=>\s*Promise\b", signature):
                        callback_kinds.append("zero-arg-async")
                    else:
                        callback_kinds.append("unsupported")
                if "):" in text:
                    return_text = text.rsplit("):", 1)[1].rsplit(";", 1)[0]
                elif ":" in text:
                    return_text = text.split(":", 1)[1].rsplit(";", 1)[0]
                else:
                    return_text = ""
                for ref in declaration.get("references") or []:
                    if ref in return_names and re.search(rf"\b{re.escape(ref)}\b", return_text):
                        returns.append(ref)
            member_contract[member_name] = {
                "returns": list(dict.fromkeys(returns)),
                "callbackKinds": list(dict.fromkeys(callback_kinds)),
            }
        contract[interface_name] = member_contract

    return {"interfaces": contract, "aliases": aliases}


def public_api_coverage() -> dict[str, Any]:
    contract = build_public_api_contract()
    interfaces: dict[str, dict[str, dict[str, Any]]] = contract["interfaces"]
    aliases: dict[str, list[str]] = contract["aliases"]
    reachable = {name for name in PUBLIC_API_ROOT_INTERFACES if name in interfaces}

    changed = True
    while changed:
        changed = False
        for interface_name in tuple(reachable):
            for member in interfaces.get(interface_name, {}).values():
                for returned in member.get("returns") or []:
                    for candidate in [returned, *(aliases.get(returned) or [])]:
                        if candidate in interfaces and candidate not in reachable:
                            reachable.add(candidate)
                            changed = True

    installed = set(interfaces)
    missing = sorted(installed - reachable)
    callback_members: list[dict[str, Any]] = []
    unsupported_callbacks: list[str] = []
    for interface_name, members in interfaces.items():
        for member_name, member in members.items():
            kinds = list(member.get("callbackKinds") or [])
            if not kinds:
                continue
            qualified = f"{interface_name}.{member_name}"
            callback_members.append({"member": qualified, "kinds": kinds})
            if any(kind != "zero-arg-async" for kind in kinds):
                unsupported_callbacks.append(qualified)
    return {
        "complete": not missing and not unsupported_callbacks,
        "surfaceInterfaces": PUBLIC_API_SURFACES,
        "installedInterfaces": sorted(installed),
        "directRootInterfaces": sorted(
            name for name in PUBLIC_API_ROOT_INTERFACES if name in installed
        ),
        "reachableInterfaces": sorted(reachable),
        "unreachableInterfaces": missing,
        "callbackMembers": callback_members,
        "unsupportedCallbackMembers": sorted(unsupported_callbacks),
    }


def parse_json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("expected a JSON object")
    return parsed


def parse_json_array(value: str) -> list[Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise argparse.ArgumentTypeError("expected a JSON array")
    return parsed


def validate_member_path(value: str) -> str:
    if value.startswith("$"):
        if value not in {"$value", "$await", "$release", "$image"}:
            raise argparse.ArgumentTypeError(f"unsupported special method: {value}")
        return value
    parts = value.split(".")
    if not parts or any(not _MEMBER.match(part) or part in _FORBIDDEN_MEMBERS for part in parts):
        raise argparse.ArgumentTypeError("method must be a dot-separated public member path")
    return value


def save_images(content: list[dict[str, Any]], prefix: str = "image") -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    for item in content:
        if item.get("type") != "image" or not item.get("data"):
            continue
        raw = base64.b64decode(item["data"])
        mime = str(item.get("mimeType") or "image/jpeg")
        ext = {
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }.get(mime, ".jpg")
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOT_DIR / f"{prefix}-{uuid.uuid4().hex}{ext}"
        path.write_bytes(raw)
        images.append({"path": str(path), "mimeType": mime, "size": len(raw)})
    return images
