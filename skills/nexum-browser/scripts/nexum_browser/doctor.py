from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from .common import (
    SKILL_ROOT,
    find_browser_plugin_root,
    find_codex,
    is_executable_file,
    run_json_script,
)
from .runtime import CuaLaunchContract, CuaRuntime, discover_launch_contract


def _entry(
    checks: list[dict[str, Any]],
    name: str,
    status: str,
    message: str,
    **details: Any,
) -> None:
    value: dict[str, Any] = {
        "name": name,
        "status": status,
        "message": message,
    }
    if details:
        value["details"] = details
    checks.append(value)


def _codex_path(contract: CuaLaunchContract) -> Path:
    try:
        return find_codex()
    except Exception:
        candidate = Path(contract.env.get("CODEX_CLI_PATH") or "").expanduser()
        if candidate and is_executable_file(candidate):
            return candidate
        raise


def _bounded(value: str, limit: int = 6000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"


def _run_process(args: list[str], timeout: float = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
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


def _windows_acl_details(runtime_path: Path, sandbox_output: str) -> dict[str, Any]:
    absolute = runtime_path.absolute()
    try:
        resolved = runtime_path.resolve(strict=False)
    except OSError:
        resolved = absolute

    groups_text = ""
    acl_text = ""
    resolved_acl_text = ""
    try:
        groups = _run_process(["whoami", "/groups", "/fo", "csv"], timeout=10)
        groups_text = (groups.stdout or groups.stderr).strip()
    except Exception as exc:
        groups_text = f"unavailable: {exc}"

    for target, field in ((runtime_path, "runtime"), (resolved, "resolved")):
        try:
            result = _run_process(["icacls", str(target)], timeout=10)
            value = (result.stdout or result.stderr).strip()
        except Exception as exc:
            value = f"unavailable: {exc}"
        if field == "runtime":
            acl_text = value
        else:
            resolved_acl_text = value

    sandbox_lines = [
        line
        for line in groups_text.splitlines()
        if "codexsandbox" in line.lower()
    ]
    sids = re.findall(r"S-\d-(?:\d+-)+\d+", "\n".join(sandbox_lines))
    acl_fold = (acl_text + "\n" + resolved_acl_text).lower()
    group_present = (
        "codexsandboxusers" in acl_fold
        or any(sid.lower() in acl_fold for sid in sids)
    )
    access_denied = any(
        token in sandbox_output.lower()
        for token in (
            "access is denied",
            "access denied",
            "createprocessasuserw failed: 5",
            "winerror 5",
        )
    )
    if access_denied and sandbox_lines and not group_present:
        mismatch = "suspected"
    elif access_denied:
        mismatch = "undetermined"
    else:
        mismatch = "not-detected"

    return {
        "runtimePath": str(absolute),
        "junctionTarget": str(resolved),
        "sandboxGroup": sandbox_lines,
        "sandboxGroupSids": sids,
        "runtimeAcl": _bounded(acl_text),
        "junctionTargetAcl": _bounded(resolved_acl_text),
        "aclMismatch": mismatch,
    }


def _browser_checks(
    checks: list[dict[str, Any]],
    contract: CuaLaunchContract,
) -> None:
    try:
        root = find_browser_plugin_root(contract.runtime_version)
    except Exception as exc:
        _entry(checks, "Browser plugin", "fail", str(exc))
        return

    _entry(
        checks,
        "Browser plugin",
        "pass",
        f"OpenAI Browser plugin found: {root}",
    )
    scripts = root / "scripts"

    def run(name: str, *args: str) -> tuple[dict[str, Any], str]:
        script = scripts / name
        if not script.is_file():
            return {}, f"diagnostic script is missing: {script}"
        try:
            rc, value, message = run_json_script(
                contract.node_path,
                script,
                *args,
            )
        except Exception as exc:
            return {}, str(exc)
        if rc != 0 and not value:
            return {}, message or f"{name} exited with {rc}"
        return value, message

    installed, installed_msg = run("installed-browsers.js", "--json")
    browsers = installed.get("installed_browsers") or []
    chrome = next(
        (
            item
            for item in browsers
            if isinstance(item, dict)
            and "chrome" in str(item.get("name") or "").lower()
        ),
        None,
    )
    if chrome:
        _entry(
            checks,
            "Chrome installed",
            "pass",
            str(chrome.get("name") or "Google Chrome"),
            browser=chrome,
        )
    else:
        _entry(
            checks,
            "Chrome installed",
            "fail",
            installed_msg or "Google Chrome was not found",
        )

    running, running_msg = run(
        "chrome-is-running.js",
        "--browser",
        "chrome",
        "--json",
    )
    if running.get("running") is True:
        _entry(checks, "Chrome running", "pass", "Google Chrome is running")
    else:
        _entry(
            checks,
            "Chrome running",
            "fail",
            running_msg or "Google Chrome is not running",
        )

    extension, extension_msg = run(
        "check-extension-installed.js",
        "--browser",
        "chrome",
        "--json",
    )
    if extension.get("installed") is True and extension.get("enabled") is True:
        _entry(
            checks,
            "Browser extension",
            "pass",
            "ChatGPT/Codex Chrome extension is installed and enabled",
            profile=extension.get("selectedProfileDirectory"),
        )
    else:
        _entry(
            checks,
            "Browser extension",
            "fail",
            extension_msg
            or "ChatGPT/Codex Chrome extension is missing or disabled",
            diagnostic=extension,
        )

    native, native_msg = run(
        "check-native-host-manifest.js",
        "--browser",
        "chrome",
        "--json",
    )
    if native.get("correct") is True:
        _entry(
            checks,
            "Native messaging host",
            "pass",
            "Chrome native messaging host is registered correctly",
            manifestPath=native.get("manifestPath"),
        )
    else:
        _entry(
            checks,
            "Native messaging host",
            "fail",
            str(native.get("problem") or native_msg or "Native host check failed"),
            diagnostic=native,
        )


def run_doctor() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    contract: CuaLaunchContract | None = None

    try:
        contract = discover_launch_contract()
        _entry(
            checks,
            "unified-computer-use",
            "pass",
            f"Launch contract found: {contract.config_path}",
            runtimeVersion=contract.runtime_version,
        )
        _entry(
            checks,
            "Runtime launch contract",
            "pass",
            "command, args, env, env_vars and enabled_tools are valid",
            **contract.summary(),
        )
    except Exception as exc:
        _entry(checks, "unified-computer-use", "fail", str(exc))
        return {
            "healthy": False,
            "platform": sys.platform,
            "checks": checks,
        }

    try:
        codex = _codex_path(contract)
        _entry(checks, "Codex installation", "pass", str(codex))
    except Exception as exc:
        codex = None
        _entry(checks, "Codex installation", "fail", str(exc))

    for name, path in (
        ("cua_repl node runtime", Path(contract.command)),
        ("node runtime", contract.node_path),
        ("node_repl", contract.node_repl),
        ("Browser API manifest", contract.api_json),
    ):
        if path.is_file():
            _entry(checks, name, "pass", str(path))
        else:
            _entry(checks, name, "fail", f"Missing: {path}")

    if contract.env.get("NODE_REPL_JS_BANNER") == "":
        _entry(
            checks,
            "Node startup banner",
            "pass",
            "NODE_REPL_JS_BANNER is overridden to an empty string",
        )
    else:
        _entry(
            checks,
            "Node startup banner",
            "fail",
            "NODE_REPL_JS_BANNER must be empty",
        )

    if os.name == "nt":
        if codex is None:
            _entry(
                checks,
                "Codex sandbox node.exe",
                "fail",
                "Codex CLI is unavailable, so the Windows sandbox execute check cannot run",
            )
        else:
            try:
                result = _run_process(
                    [str(codex), "sandbox", str(contract.node_path), "--version"],
                    timeout=30,
                )
                output = "\n".join(
                    item
                    for item in ((result.stdout or "").strip(), (result.stderr or "").strip())
                    if item
                )
                if result.returncode == 0:
                    _entry(
                        checks,
                        "Codex sandbox node.exe",
                        "pass",
                        "Codex Windows sandbox can execute Browser Runtime node.exe",
                        output=_bounded(output),
                    )
                else:
                    details = _windows_acl_details(contract.node_path, output)
                    _entry(
                        checks,
                        "Codex sandbox node.exe",
                        "fail",
                        "Codex sandbox cannot execute Browser Runtime node.exe",
                        exitCode=result.returncode,
                        output=_bounded(output),
                        **details,
                    )
            except Exception as exc:
                details = _windows_acl_details(contract.node_path, str(exc))
                _entry(
                    checks,
                    "Codex sandbox node.exe",
                    "fail",
                    f"Codex sandbox node.exe probe failed: {exc}",
                    **details,
                )

    _browser_checks(checks, contract)

    runtime: CuaRuntime | None = None
    try:
        runtime = CuaRuntime(contract)
    except Exception as exc:
        details: dict[str, Any] = {}
        if os.name == "nt":
            details.update(_windows_acl_details(contract.node_path, str(exc)))
        _entry(
            checks,
            "MCP initialize",
            "fail",
            str(exc),
            **details,
        )
    else:
        _entry(
            checks,
            "MCP initialize",
            "pass",
            "cua_repl MCP initialize completed",
            protocolVersion=runtime.initialize_info.get("protocolVersion"),
        )
        _entry(
            checks,
            "tools/list",
            "pass",
            "Required Browser Runtime tools are enabled",
            tools=sorted(runtime.allowed_tools),
        )

        def browser_probe(name: str, title: str) -> None:
            try:
                runtime.run(
                    """
let __doctorBrowser = await cua.getBrowser({id: "chrome"});
let __doctorTab;
try {
  __doctorTab = await cua.createBrowserTab(__doctorBrowser.browserId);
  nodeRepl.write("nexum-browser doctor tab ok");
} finally {
  if (__doctorTab) await __doctorTab.close();
}
""".strip(),
                    title=title,
                    timeout_ms=60000,
                    rpc_timeout=max(60.0, contract.startup_timeout),
                )
            except Exception as exc:
                details: dict[str, Any] = {}
                if os.name == "nt":
                    details.update(
                        _windows_acl_details(contract.node_path, str(exc))
                    )
                _entry(checks, name, "fail", str(exc), **details)
            else:
                _entry(
                    checks,
                    name,
                    "pass",
                    "Created and closed a temporary controlled Chrome tab",
                )

        browser_probe(
            "js + Browser backend",
            "nexum-browser doctor controlled tab",
        )

        try:
            runtime.reset()
        except Exception as exc:
            _entry(checks, "js_reset", "fail", str(exc))
        else:
            _entry(
                checks,
                "js_reset",
                "pass",
                "Node REPL context reset completed",
            )
            browser_probe(
                "post-reset bootstrap",
                "nexum-browser doctor post-reset controlled tab",
            )

        try:
            runtime.release()
        except Exception as exc:
            _entry(checks, "turn_ended", "fail", str(exc))
        else:
            _entry(
                checks,
                "turn_ended",
                "pass",
                "Browser Runtime turn ended cleanly",
            )
        finally:
            runtime.close()

    healthy = not any(item["status"] == "fail" for item in checks)
    return {
        "healthy": healthy,
        "platform": sys.platform,
        "runtime": contract.summary(),
        "checks": checks,
    }
