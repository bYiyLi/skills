from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import types
import unittest
import uuid
from unittest.mock import Mock, patch


sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "skills/nexum-browser"
sys.path.insert(0, str(ROOT / "scripts"))

import browser_task

from nexum_browser.broker import (
    ActiveOperation,
    Broker,
    BrokerBusy,
    BrokerRequestOutcomeUnknown,
    BrokerRequestTimeout,
    BrokerRuntimeReleaseFailed,
    _compatible_ping,
    _request,
    _state_process_alive,
    _unix_broker_pids,
    _write_windows_task_environment,
    broker_status,
    ensure_broker,
    stop_broker,
)
from nexum_browser.cli import (
    _WINDOWS_ARGV_ROOT_ENV,
    _WINDOWS_ARGV_SENTINEL,
    _continuation_request_timeout,
    _prepare_argv,
    _run_request_timeout,
    build_internal_parser,
    build_parser,
    main as cli_main,
)
from nexum_browser.common import codex_home, emit, operation_lock
from nexum_browser.doctor import (
    _failure_category,
    _read_windows_registry_default_value,
    _redact_sensitive_text,
    _runtime_browser_checks,
    _runtime_failure_details,
    _windows_acl_details,
)
from nexum_browser.mcp import (
    McpError,
    McpRequestOutcomeUnknown,
    PendingElicitation,
    StdioMcpClient,
)
from nexum_browser.runtime import (
    _BOOTSTRAP_RETRY_PREFIX,
    _BOOTSTRAP_WITH_READINESS,
    _POLICY_READY_NO,
    _POLICY_READY_YES,
    CuaRuntime,
    CuaToolError,
    _apply_windows_proxy_fallback,
    _read_contract,
    _wininet_proxy_override_to_no_proxy,
)


class LaunchContractTests(unittest.TestCase):
    def test_operation_lock_uses_live_os_ownership_not_file_age(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            lock_path = runtime_dir / "operation.lock"
            with (
                patch(
                    "nexum_browser.common.RUNTIME_DIR",
                    runtime_dir,
                ),
                patch(
                    "nexum_browser.common.OPERATION_LOCK_PATH",
                    lock_path,
                ),
            ):
                with operation_lock(timeout=0.1):
                    os.utime(lock_path, (0, 0))
                    with self.assertRaises(TimeoutError):
                        with operation_lock(timeout=0.05):
                            pass

    def test_cli_json_output_is_ascii_safe_for_windows_code_pages(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            emit({"session": "🔎 Browser", "title": "中文"})
        raw = output.getvalue()
        self.assertTrue(raw.isascii())
        self.assertEqual(
            json.loads(raw),
            {"session": "🔎 Browser", "title": "中文"},
        )

    def test_codex_home_honors_environment_override(self) -> None:
        with patch.dict(
            os.environ,
            {"CODEX_HOME": str(ROOT / ".test-codex-home")},
            clear=False,
        ):
            self.assertEqual(
                codex_home(),
                ROOT / ".test-codex-home",
            )

    def test_launch_contract_uses_generated_values_and_overrides_banner(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            node = root / "node"
            node_repl = root / "node_repl"
            entry = (
                root
                / "node_modules/@oai/cua-repl/bin/cua-repl.mjs"
            )
            api = (
                root
                / "node_modules/@oai/browser-desktop/"
                "environment-docs/codex-app/api.json"
            )
            for executable in (node, node_repl):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\n", encoding="utf-8")
                executable.chmod(0o755)
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("", encoding="utf-8")
            api.parent.mkdir(parents=True, exist_ok=True)
            api.write_text(
                '{"interfaces":{},"types":{}}',
                encoding="utf-8",
            )
            config = root / "26.1/.mcp.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "cua_repl": {
                                "command": str(node),
                                "args": [str(entry)],
                                "enabled": True,
                                "enabled_tools": [
                                    "js",
                                    "js_reset",
                                    "turn_ended",
                                ],
                                "startup_timeout_sec": 17,
                                "env_vars": [
                                    "FORWARDED_OPTIONAL",
                                    "MISSING_OPTIONAL",
                                ],
                                "env": {
                                    "CUA_REPL_NODE_REPL_PATH": str(
                                        node_repl
                                    ),
                                    "CUA_REPL_ENABLED_SURFACES": (
                                        "browser,computer"
                                    ),
                                    "NODE_REPL_NODE_MODULE_DIRS": str(
                                        root / "node_modules"
                                    ),
                                    "NODE_REPL_NODE_PATH": str(node),
                                    "NODE_REPL_JS_BANNER": (
                                        "await import('old-banner')"
                                    ),
                                    "PRESERVE_ME": "yes",
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"FORWARDED_OPTIONAL": "forward-me"},
                clear=False,
            ):
                os.environ.pop("MISSING_OPTIONAL", None)
                contract = _read_contract(config)

        self.assertEqual(contract.command, str(node))
        self.assertEqual(contract.runtime_version, "26.1")
        self.assertEqual(contract.startup_timeout, 17)
        self.assertEqual(contract.api_json, api)
        self.assertEqual(contract.node_repl, node_repl)
        self.assertEqual(contract.node_path, node)
        self.assertEqual(
            contract.enabled_tools,
            frozenset({"js", "js_reset", "turn_ended"}),
        )
        self.assertEqual(contract.env["PRESERVE_ME"], "yes")
        self.assertEqual(
            contract.env["FORWARDED_OPTIONAL"],
            "forward-me",
        )
        self.assertNotIn("MISSING_OPTIONAL", contract.env)
        self.assertEqual(contract.env["NODE_REPL_JS_BANNER"], "")

    def test_windows_proxy_fallback_preserves_explicit_values(self) -> None:
        env = {
            "HTTPS_PROXY": "",
            "ALL_PROXY": "socks5://explicit.invalid:1080",
            "NO_PROXY": "",
        }
        status = _apply_windows_proxy_fallback(
            env,
            explicit_names={"HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"},
            system_proxies={
                "http": "http://system.invalid:8080",
                "https": "http://system.invalid:8080",
                "no_proxy": "localhost,127.0.0.1,::1",
            },
        )

        self.assertNotIn("HTTP_PROXY", env)
        self.assertEqual(env["HTTPS_PROXY"], "")
        self.assertEqual(
            env["ALL_PROXY"],
            "socks5://explicit.invalid:1080",
        )
        self.assertEqual(status["http"], "all-proxy")
        self.assertEqual(status["https"], "explicit-empty")
        self.assertEqual(status["noProxy"], "explicit-empty")
        self.assertEqual(status["wininetProxy"], "configured")
        self.assertEqual(status["wininetBypass"], "configured")

    def test_windows_proxy_fallback_injects_missing_specific_proxy(
        self,
    ) -> None:
        env = {"HTTP_PROXY": "http://explicit.invalid:3128"}
        status = _apply_windows_proxy_fallback(
            env,
            explicit_names={"HTTP_PROXY"},
            system_proxies={
                "http": "http://system.invalid:8080",
                "https": "http://system.invalid:8080",
                "no_proxy": "localhost,127.0.0.1,::1",
            },
        )

        self.assertEqual(
            env["HTTP_PROXY"],
            "http://explicit.invalid:3128",
        )
        self.assertEqual(
            env["HTTPS_PROXY"],
            "http://system.invalid:8080",
        )
        self.assertEqual(status["http"], "explicit")
        self.assertEqual(status["https"], "wininet")
        self.assertEqual(
            env["NO_PROXY"],
            "localhost,127.0.0.1,::1",
        )
        self.assertEqual(status["noProxy"], "wininet-bypass")

    def test_wininet_proxy_override_maps_to_no_proxy(self) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                "localhost;*.corp.example;api.internal;10.0.0.5;*"
            ),
            (
                "localhost,*.corp.example,api.internal,10.0.0.5,*",
                False,
            ),
        )

    def test_wininet_proxy_override_marks_unrepresentable_patterns_partial(
        self,
    ) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                (
                    "<local>;127.*;10.*;localhost;"
                    "*.corp.example;api.internal"
                )
            ),
            ("127.0.0.1,localhost,*.corp.example,api.internal", True),
        )

    def test_loopback_subtraction_honors_rule_order(self) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                (
                    "localhost;loopback;127.0.0.1;127.0.0.2;"
                    "169.254.1.2;<-loopback>"
                )
            ),
            ("127.0.0.2,169.254.1.2", False),
        )
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                "<-loopback>;localhost;loopback;127.0.0.1"
            ),
            ("localhost,loopback,127.0.0.1", False),
        )

    def test_loopback_subtraction_keeps_explicit_127_alias(self) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                "127.0.0.2;<-loopback>"
            ),
            ("127.0.0.2", False),
        )

    def test_local_rule_is_not_mapped_to_localhost(self) -> None:
        for value in ("<local>;<-loopback>", "<-loopback>;<local>"):
            with self.subTest(value=value):
                self.assertEqual(
                    _wininet_proxy_override_to_no_proxy(value),
                    ("", True),
                )

    def test_loopback_subtraction_does_not_leave_broad_bypass(self) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy("*;<-loopback>"),
            ("", True),
        )
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy("<-loopback>;*"),
            ("*", False),
        )

    def test_wininet_proxy_override_rejects_non_equivalent_no_proxy_rules(
        self,
    ) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                (
                    ".corp.example;api.internal:8443;"
                    "192.168.1.0-192.168.1.255;10.0.0.0/8;::1"
                )
            ),
            ("", True),
        )

    def test_explicit_forward_proxy_still_uses_wininet_bypass(
        self,
    ) -> None:
        for explicit_name, value in (
            ("HTTP_PROXY", "http://explicit.invalid:3128"),
            ("HTTPS_PROXY", "http://explicit.invalid:3128"),
            ("ALL_PROXY", "socks5://explicit.invalid:1080"),
        ):
            with self.subTest(explicit_name=explicit_name):
                env = {explicit_name: value}
                status = _apply_windows_proxy_fallback(
                    env,
                    explicit_names={explicit_name},
                    system_proxies={
                        "http": "http://system.invalid:8080",
                        "https": "http://system.invalid:8080",
                        "no_proxy": "127.0.0.1",
                    },
                )
                self.assertEqual(env["NO_PROXY"], "127.0.0.1")
                self.assertEqual(status["noProxy"], "wininet-bypass")

    def test_explicit_empty_proxy_keeps_wininet_bypass_for_fallback(
        self,
    ) -> None:
        env = {"HTTP_PROXY": ""}
        status = _apply_windows_proxy_fallback(
            env,
            explicit_names={"HTTP_PROXY"},
            system_proxies={
                "http": "http://system.invalid:8080",
                "https": "http://system.invalid:8080",
                "no_proxy": "127.0.0.1",
            },
        )

        self.assertEqual(env["HTTP_PROXY"], "")
        self.assertEqual(
            env["HTTPS_PROXY"],
            "http://system.invalid:8080",
        )
        self.assertEqual(env["NO_PROXY"], "127.0.0.1")
        self.assertEqual(status["http"], "explicit-empty")
        self.assertEqual(status["https"], "wininet")
        self.assertEqual(status["noProxy"], "wininet-bypass")

    def test_wininet_proxy_override_rejects_no_proxy_separators(
        self,
    ) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                "api.internal,external.com;api.internal external.com"
            ),
            ("", True),
        )

    def test_wininet_proxy_override_rejects_mixed_wildcard_syntax(
        self,
    ) -> None:
        self.assertEqual(
            _wininet_proxy_override_to_no_proxy(
                "*.corp?.example;[ab].corp.example"
            ),
            ("", True),
        )

    def test_partial_wininet_bypass_status_is_explicit(self) -> None:
        env: dict[str, str] = {}
        status = _apply_windows_proxy_fallback(
            env,
            explicit_names=set(),
            system_proxies={
                "http": "http://system.invalid:8080",
                "https": "http://system.invalid:8080",
                "no_proxy": "localhost,127.0.0.1",
                "no_proxy_partial": "1",
            },
        )

        self.assertEqual(
            env["NO_PROXY"],
            "localhost,127.0.0.1",
        )
        self.assertEqual(
            status["noProxy"],
            "wininet-bypass-partial",
        )
        self.assertEqual(status["wininetBypass"], "partial")

    def test_missing_required_tools_rejects_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            node = root / "node"
            node_repl = root / "node_repl"
            entry = (
                root
                / "node_modules/@oai/cua-repl/bin/cua-repl.mjs"
            )
            api = (
                root
                / "node_modules/@oai/browser-desktop/"
                "environment-docs/codex-app/api.json"
            )
            for executable in (node, node_repl):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\n", encoding="utf-8")
                executable.chmod(0o755)
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("", encoding="utf-8")
            api.parent.mkdir(parents=True, exist_ok=True)
            api.write_text("{}", encoding="utf-8")
            config = root / "1/.mcp.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "cua_repl": {
                                "command": str(node),
                                "args": [str(entry)],
                                "enabled": True,
                                "enabled_tools": ["js"],
                                "env": {
                                    "CUA_REPL_NODE_REPL_PATH": str(
                                        node_repl
                                    ),
                                    "NODE_REPL_NODE_PATH": str(node),
                                    "NODE_REPL_NODE_MODULE_DIRS": str(
                                        root / "node_modules"
                                    ),
                                    "CUA_REPL_ENABLED_SURFACES": "browser",
                                },
                            }
                        }
                    }
                )
            )
            with self.assertRaisesRegex(
                RuntimeError,
                "required tools",
            ):
                _read_contract(config)


class RuntimeTests(unittest.TestCase):
    class FakeClient:
        def __init__(self) -> None:
            self.calls = []
            self.allowed_tools = {"js", "js_reset", "turn_ended"}

        def call_tool(
            self,
            name,
            arguments,
            *,
            meta=None,
            timeout=None,
        ):
            self.calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "meta": meta,
                    "timeout": timeout,
                }
            )
            code = str(arguments.get("code") or "")
            if (
                name == "js"
                and "agent.browsers.list()" in code
                and _POLICY_READY_YES in code
                and "nodeRepl.write(" in code
            ):
                return {
                    "content": [
                        {"type": "text", "text": _POLICY_READY_YES}
                    ],
                    "isError": False,
                }
            return {
                "content": [{"type": "text", "text": "ok"}],
                "isError": False,
            }

        def pending_elicitation(self):
            return None

        def respond_elicitation(
            self,
            elicitation_id,
            *,
            action,
            content=None,
        ):
            raise AssertionError("not expected")

        def close(self):
            pass

    def make_runtime(self) -> tuple[CuaRuntime, FakeClient]:
        runtime = object.__new__(CuaRuntime)
        client = self.FakeClient()
        runtime.client = client
        runtime.session_id = "session-1"
        runtime.turn_id = "turn-1"
        runtime.bootstrapped = False
        runtime.policy_ready = False
        runtime._released = False
        return runtime, client

    @staticmethod
    def _is_readiness_call(call: dict) -> bool:
        code = str(call["arguments"].get("code") or "")
        return (
            "agent.browsers.list()" in code
            and _POLICY_READY_YES in code
            and _POLICY_READY_NO in code
        )

    def test_first_run_probes_readiness_before_user_js(self) -> None:
        runtime, client = self.make_runtime()

        result = runtime.run("let probe = 41; probe")

        self.assertEqual(result["content"][0]["text"], "ok")
        self.assertEqual(len(client.calls), 2)
        readiness, user = client.calls
        self.assertEqual(readiness["name"], "js")
        self.assertTrue(self._is_readiness_call(readiness))
        self.assertTrue(
            readiness["arguments"]["code"].startswith(
                'await import("@oai/cua/tinyskyAlt");\n'
            )
        )
        self.assertIn("agent.browsers.list()", _BOOTSTRAP_WITH_READINESS)
        self.assertIn(
            "for (let __nexumInfo of __nexumOrdered)",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "__nexumErrors.push(__nexumError)",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "__nexumProbeTab = await __nexumBrowser.tabs.new()",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "await __nexumProbeTab.close()",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "nodeRepl.write(",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            _POLICY_READY_YES,
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            _POLICY_READY_NO,
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "Unable to close temporary browser readiness tab",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "catch (__nexumCleanupError)",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertNotIn("catch {}", _BOOTSTRAP_WITH_READINESS)
        self.assertIn(
            "Unable to load browser request-header policy",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertNotIn(
            "__NEXUM_BROWSER_BOOTSTRAP_RETRY_MARKER__",
            readiness["arguments"]["code"],
        )
        self.assertIn(
            _BOOTSTRAP_RETRY_PREFIX,
            readiness["arguments"]["code"],
        )
        self.assertNotIn("setTimeout(", _BOOTSTRAP_WITH_READINESS)
        self.assertNotIn(
            "let probe = 41; probe",
            readiness["arguments"]["code"],
        )
        self.assertEqual(
            user["arguments"]["code"],
            "let probe = 41; probe",
        )
        self.assertTrue(runtime.bootstrapped)
        self.assertTrue(runtime.policy_ready)

    def test_bootstrap_policy_failure_restarts_before_retrying_user_js(
        self,
    ) -> None:
        runtime, first = self.make_runtime()
        second = self.FakeClient()
        calls = 0

        def failing_call_tool(
            name,
            arguments,
            *,
            meta=None,
            timeout=None,
        ):
            nonlocal calls
            calls += 1
            first.calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "meta": meta,
                    "timeout": timeout,
                }
            )
            suffix = arguments["code"].split(
                _BOOTSTRAP_RETRY_PREFIX,
                1,
            )[1].split('"', 1)[0]
            marker = _BOOTSTRAP_RETRY_PREFIX + suffix
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Browser documentation",
                    },
                    {
                        "type": "text",
                        "text": "Error: "
                        + marker
                        + "Unable to load browser request-header policy.",
                    },
                ],
                "isError": True,
            }

        first.call_tool = failing_call_tool

        def restart() -> None:
            first.close()
            runtime.client = second
            runtime.initialize_info = {}
            runtime.bootstrapped = False
            runtime.policy_ready = False

        runtime._restart_after_bootstrap_failure = restart

        result = runtime.run("nodeRepl.write('user-js-ran')")

        self.assertEqual(calls, 1)
        self.assertEqual(result["content"][0]["text"], "ok")
        self.assertEqual(len(second.calls), 2)
        first_code = first.calls[0]["arguments"]["code"]
        second_readiness = second.calls[0]["arguments"]["code"]
        self.assertEqual(first_code, second_readiness)
        self.assertNotIn("nodeRepl.write('user-js-ran')", first_code)
        self.assertNotIn(
            "nodeRepl.write('user-js-ran')",
            second_readiness,
        )
        self.assertEqual(
            second.calls[1]["arguments"]["code"],
            "nodeRepl.write('user-js-ran')",
        )
        self.assertTrue(runtime.bootstrapped)
        self.assertTrue(runtime.policy_ready)

    def test_user_error_cannot_spoof_bootstrap_retry_marker(self) -> None:
        runtime, client = self.make_runtime()
        calls = 0

        def user_error(name, arguments, *, meta=None, timeout=None):
            nonlocal calls
            calls += 1
            code = str(arguments.get("code") or "")
            if "agent.browsers.list()" in code:
                client.calls.append(
                    {
                        "name": name,
                        "arguments": arguments,
                        "meta": meta,
                        "timeout": timeout,
                    }
                )
                return {
                    "content": [
                        {"type": "text", "text": _POLICY_READY_YES}
                    ],
                    "isError": False,
                }
            client.calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "meta": meta,
                    "timeout": timeout,
                }
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            _BOOTSTRAP_RETRY_PREFIX
                            + "Unable to load browser request-header policy."
                        ),
                    }
                ],
                "isError": True,
            }

        client.call_tool = user_error

        with self.assertRaises(CuaToolError):
            runtime.run(
                "throw new Error("
                "'NEXUM_BROWSER_BOOTSTRAP_RETRY:"
                "Unable to load browser request-header policy.'"
                ")"
            )

        self.assertEqual(calls, 2)
        self.assertTrue(runtime.bootstrapped)
        self.assertTrue(runtime.policy_ready)

    def test_later_runs_reuse_same_context_without_rebootstrap(self) -> None:
        runtime, client = self.make_runtime()
        runtime.run("let probe = 41")
        runtime.run("probe + 1")

        self.assertEqual(len(client.calls), 3)
        self.assertTrue(self._is_readiness_call(client.calls[0]))
        self.assertEqual(
            client.calls[1]["arguments"]["code"],
            "let probe = 41",
        )
        self.assertEqual(
            client.calls[2]["arguments"]["code"],
            "probe + 1",
        )

    def test_readiness_remains_false_without_a_controlled_tab_probe(
        self,
    ) -> None:
        runtime, client = self.make_runtime()
        original = client.call_tool

        def no_browser_probe(name, arguments, *, meta=None, timeout=None):
            code = str(arguments.get("code") or "")
            if "agent.browsers.list()" in code:
                client.calls.append(
                    {
                        "name": name,
                        "arguments": arguments,
                        "meta": meta,
                        "timeout": timeout,
                    }
                )
                return {
                    "content": [
                        {"type": "text", "text": _POLICY_READY_NO}
                    ],
                    "isError": False,
                }
            return original(
                name,
                arguments,
                meta=meta,
                timeout=timeout,
            )

        client.call_tool = no_browser_probe

        runtime.run("await cua.getState()")
        self.assertTrue(runtime.bootstrapped)
        self.assertFalse(runtime.policy_ready)
        self.assertEqual(len(client.calls), 2)

        runtime.run("await cua.getState()")
        self.assertTrue(self._is_readiness_call(client.calls[2]))
        self.assertEqual(
            client.calls[3]["arguments"]["code"],
            "await cua.getState()",
        )
        self.assertFalse(runtime.policy_ready)

    def test_caller_cannot_forge_passive_readiness(self) -> None:
        runtime, client = self.make_runtime()
        original = client.call_tool

        def no_browser_probe(name, arguments, *, meta=None, timeout=None):
            code = str(arguments.get("code") or "")
            if "agent.browsers.list()" in code:
                client.calls.append(
                    {
                        "name": name,
                        "arguments": arguments,
                        "meta": meta,
                        "timeout": timeout,
                    }
                )
                return {
                    "content": [
                        {"type": "text", "text": _POLICY_READY_NO}
                    ],
                    "isError": False,
                }
            return original(
                name,
                arguments,
                meta=meta,
                timeout=timeout,
            )

        client.call_tool = no_browser_probe

        runtime.run(
            "globalThis.__nexumBrowserPolicyReady = true; 'forged'"
        )

        self.assertFalse(runtime.policy_ready)
        self.assertEqual(
            client.calls[1]["arguments"]["code"],
            "globalThis.__nexumBrowserPolicyReady = true; 'forged'",
        )

    def test_conflicting_readiness_markers_are_rejected(self) -> None:
        runtime, client = self.make_runtime()

        def conflicting(name, arguments, *, meta=None, timeout=None):
            client.calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "meta": meta,
                    "timeout": timeout,
                }
            )
            return {
                "content": [
                    {"type": "text", "text": _POLICY_READY_YES},
                    {"type": "text", "text": _POLICY_READY_NO},
                ],
                "isError": False,
            }

        client.call_tool = conflicting

        with self.assertRaisesRegex(
            RuntimeError,
            "conflicting readiness markers",
        ):
            runtime.run("await cua.getState()")

        self.assertFalse(runtime.policy_ready)
        self.assertEqual(len(client.calls), 1)

    def test_readiness_survives_user_error_after_successful_probe(
        self,
    ) -> None:
        runtime, client = self.make_runtime()

        def failing_user_code(name, arguments, *, meta=None, timeout=None):
            client.calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "meta": meta,
                    "timeout": timeout,
                }
            )
            code = str(arguments.get("code") or "")
            if "agent.browsers.list()" in code:
                return {
                    "content": [
                        {"type": "text", "text": _POLICY_READY_YES}
                    ],
                    "isError": False,
                }
            return {
                "content": [
                    {"type": "text", "text": "ReferenceError: user"}
                ],
                "isError": True,
            }

        client.call_tool = failing_user_code

        with self.assertRaisesRegex(CuaToolError, "ReferenceError"):
            runtime.run("missingUserValue")

        self.assertTrue(runtime.policy_ready)
        self.assertTrue(runtime.bootstrapped)
        self.assertEqual(len(client.calls), 2)

    def test_reset_rechecks_readiness_before_next_user_run(self) -> None:
        runtime, client = self.make_runtime()
        runtime.run("let probe = 41")
        result = runtime.reset()
        self.assertFalse(runtime.bootstrapped)
        self.assertFalse(runtime.policy_ready)
        self.assertEqual(client.calls[-1]["name"], "js_reset")
        self.assertEqual(result["content"][0]["text"], "ok")

        runtime.run("typeof probe")
        self.assertTrue(self._is_readiness_call(client.calls[-2]))
        self.assertEqual(
            client.calls[-1]["arguments"]["code"],
            "typeof probe",
        )

    def test_run_preserves_raw_mcp_content(self) -> None:
        runtime, client = self.make_runtime()
        expected = {
            "content": [
                {"type": "text", "text": "state"},
                {
                    "type": "image",
                    "mimeType": "image/jpeg",
                    "data": "abc",
                },
                {
                    "type": "audio",
                    "mimeType": "audio/wav",
                    "data": "def",
                },
            ],
            "isError": False,
        }
        original = client.call_tool

        def raw_result(name, arguments, *, meta=None, timeout=None):
            if "agent.browsers.list()" in str(
                arguments.get("code") or ""
            ):
                return original(
                    name,
                    arguments,
                    meta=meta,
                    timeout=timeout,
                )
            return expected

        client.call_tool = raw_result

        self.assertIs(runtime.run("1 + 1"), expected)

    def test_tool_error_becomes_run_failure(self) -> None:
        runtime, client = self.make_runtime()
        original = client.call_tool

        def tool_error(name, arguments, *, meta=None, timeout=None):
            if "agent.browsers.list()" in str(
                arguments.get("code") or ""
            ):
                return original(
                    name,
                    arguments,
                    meta=meta,
                    timeout=timeout,
                )
            return {
                "content": [
                    {"type": "text", "text": "ReferenceError: missing"}
                ],
                "isError": True,
            }

        client.call_tool = tool_error

        with self.assertRaisesRegex(CuaToolError, "ReferenceError") as raised:
            runtime.run("missing")

        self.assertTrue(raised.exception.result["isError"])
        self.assertEqual(
            raised.exception.result["content"][0]["text"],
            "ReferenceError: missing",
        )
        self.assertTrue(runtime.bootstrapped)
        self.assertTrue(runtime.policy_ready)

    def test_release_sends_turn_ended_once(self) -> None:
        runtime, client = self.make_runtime()

        runtime.release()
        runtime.release()

        calls = [
            item for item in client.calls if item["name"] == "turn_ended"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0]["arguments"],
            {
                "hook_event_name": "Stop",
                "session_id": "session-1",
                "turn_id": "turn-1",
            },
        )

    def test_release_can_retry_after_turn_ended_failure(self) -> None:
        runtime, client = self.make_runtime()
        calls = 0

        def flaky_call_tool(name, arguments, *, meta=None, timeout=None):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("temporary turn_ended failure")
            return {"content": [], "isError": False}

        client.call_tool = flaky_call_tool

        with self.assertRaisesRegex(RuntimeError, "temporary"):
            runtime.release()
        self.assertFalse(runtime._released)

        runtime.release()
        self.assertTrue(runtime._released)
        self.assertEqual(calls, 2)


class BrokerTests(unittest.TestCase):
    class FakeRuntime:
        backend = "direct-cua"

        def __init__(self) -> None:
            self.bootstrapped = False
            self.policy_ready = True
            self.run_calls = []
            self.reset_calls = 0
            self.release_calls = 0
            self.close_calls = 0

        def run(self, code, *, title, timeout_ms):
            self.run_calls.append((code, title, timeout_ms))
            self.bootstrapped = True
            return {
                "content": [
                    {"type": "text", "text": "ok"},
                    {
                        "type": "image",
                        "mimeType": "image/jpeg",
                        "data": "raw-image",
                    },
                ],
                "isError": False,
            }

        def reset(self):
            self.reset_calls += 1
            self.bootstrapped = False
            return {"content": [], "isError": False}

        def pending_elicitation(self):
            return None

        def release(self):
            self.release_calls += 1

        def close(self):
            self.close_calls += 1

    def test_broker_reuses_one_runtime_and_passes_raw_content(self) -> None:
        runtime = self.FakeRuntime()
        broker = Broker()
        broker.runtime = runtime

        first = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "let x = 1",
                    "title": "first",
                    "timeoutMs": 1000,
                },
            }
        )
        second = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "x + 1",
                    "title": "second",
                    "timeoutMs": 1000,
                },
            }
        )

        self.assertEqual(first["code"], "ok")
        self.assertEqual(
            first["data"]["content"][1]["type"],
            "image",
        )
        self.assertEqual(second["code"], "ok")
        self.assertEqual(
            runtime.run_calls,
            [
                ("let x = 1", "first", 1000),
                ("x + 1", "second", 1000),
            ],
        )

    def test_broker_preserves_raw_mcp_error_content(self) -> None:
        class ErrorRuntime(self.FakeRuntime):
            def run(self, code, *, title, timeout_ms):
                raise CuaToolError(
                    "Browser failed",
                    {
                        "content": [
                            {"type": "text", "text": "Browser failed"},
                            {
                                "type": "image",
                                "mimeType": "image/jpeg",
                                "data": "raw-image",
                            },
                        ],
                        "isError": True,
                    },
                )

        broker = Broker()
        broker.runtime = ErrorRuntime()
        result = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await failingBrowserCall()",
                    "title": "failure",
                    "timeoutMs": 1000,
                },
            }
        )

        self.assertEqual(result["code"], "run_failed")
        self.assertTrue(result["data"]["isError"])
        self.assertEqual(result["data"]["content"][1]["type"], "image")

    def test_reset_does_not_start_a_runtime(self) -> None:
        broker = Broker()
        result = broker.handle({"command": "reset", "args": {}})
        self.assertEqual(
            result,
            {
                "code": "ok",
                "data": {
                    "reset": False,
                    "alreadyReset": True,
                },
            },
        )
        self.assertIsNone(broker.runtime)

    def test_windows_task_environment_preserves_explicit_proxy_values(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broker-task-env.json"
            with (
                patch(
                    "nexum_browser.broker._WINDOWS_TASK_ENV_PATH",
                    path,
                ),
                patch(
                    "nexum_browser.broker._secure_windows_state_file",
                    return_value=None,
                ),
                patch.dict(
                    os.environ,
                    {
                        "HTTP_PROXY": (
                            "http://user:secret@proxy.invalid:8080"
                        ),
                        "HTTPS_PROXY": "",
                        "NO_PROXY": "localhost",
                    },
                    clear=True,
                ),
            ):
                _write_windows_task_environment()
            saved = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(
            saved["HTTP_PROXY"],
            "http://user:secret@proxy.invalid:8080",
        )
        self.assertEqual(saved["HTTPS_PROXY"], "")
        self.assertEqual(saved["NO_PROXY"], "localhost")
        self.assertIsNone(saved["ALL_PROXY"])

    def test_windows_task_loader_clears_unset_proxy_from_task_env(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broker-task-env.json"
            path.write_text(
                json.dumps(
                    {
                        "HTTP_PROXY": "http://proxy.invalid:8080",
                        "HTTPS_PROXY": None,
                        "ALL_PROXY": None,
                        "NO_PROXY": "localhost",
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(browser_task, "ENV_PATH", path),
                patch.dict(
                    os.environ,
                    {
                        "HTTPS_PROXY": "http://stale.invalid:9999",
                        "ALL_PROXY": "socks5://stale.invalid:1080",
                    },
                    clear=False,
                ),
            ):
                browser_task._load_environment()
                self.assertEqual(
                    os.environ["HTTP_PROXY"],
                    "http://proxy.invalid:8080",
                )
                self.assertNotIn("HTTPS_PROXY", os.environ)
                self.assertNotIn("ALL_PROXY", os.environ)
                self.assertEqual(os.environ["NO_PROXY"], "localhost")

    def test_reset_keeps_broker_runtime_alive(self) -> None:
        runtime = self.FakeRuntime()
        broker = Broker()
        broker.runtime = runtime

        result = broker.handle({"command": "reset", "args": {}})

        self.assertEqual(result["code"], "ok")
        self.assertTrue(result["data"]["reset"])
        self.assertEqual(runtime.reset_calls, 1)
        self.assertIs(broker.runtime, runtime)

    def test_reset_failure_discards_runtime_as_unknown_state(
        self,
    ) -> None:
        class ResetFailureRuntime(self.FakeRuntime):
            def reset(self):
                self.reset_calls += 1
                raise RuntimeError("js_reset failed")

        runtime = ResetFailureRuntime()
        broker = Broker()
        broker.runtime = runtime

        result = broker.handle({"command": "reset", "args": {}})

        self.assertEqual(result["code"], "reset_state_unknown")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["stateUnknown"])
        self.assertTrue(result["data"]["runtimeDiscarded"])
        self.assertEqual(runtime.close_calls, 1)
        self.assertIsNone(broker.runtime)

    def test_ping_uses_new_direct_runtime_protocol(self) -> None:
        runtime = self.FakeRuntime()
        broker = Broker()
        broker.runtime = runtime

        response = broker.handle({"command": "__ping__", "args": {}})

        self.assertEqual(response["data"]["brokerProtocol"], 3)
        self.assertEqual(
            response["data"]["runtimeBackend"],
            "direct-cua",
        )
        self.assertTrue(response["data"]["policyReady"])
        self.assertTrue(
            _compatible_ping(
                {
                    "code": "ok",
                    "data": {"brokerProtocol": 3},
                }
            )
        )
        self.assertFalse(
            _compatible_ping(
                {
                    "code": "ok",
                    "data": {"brokerProtocol": 2},
                }
            )
        )

    def test_live_unresponsive_broker_is_not_replaced_or_force_stopped(
        self,
    ) -> None:
        state = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        with (
            patch(
                "nexum_browser.broker._load_state",
                return_value=state,
            ),
            patch(
                "nexum_browser.broker._ping_response",
                return_value=None,
            ),
            patch(
                "nexum_browser.broker._state_process_alive",
                return_value=True,
            ),
            patch(
                "nexum_browser.broker._clear_state_if_token"
            ) as clear_state,
            patch("nexum_browser.broker._spawn") as spawn,
        ):
            self.assertEqual(
                broker_status(),
                {
                    "running": True,
                    "unresponsive": True,
                    "pid": 12345,
                },
            )
            with self.assertRaisesRegex(
                RuntimeError,
                "running but not responding",
            ):
                ensure_broker()
            with self.assertRaisesRegex(
                RuntimeError,
                "running but not responding",
            ):
                stop_broker()

        clear_state.assert_not_called()
        spawn.assert_not_called()

    def test_unknown_windows_pid_liveness_never_force_stops_task(
        self,
    ) -> None:
        state = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        with (
            patch("nexum_browser.broker.os.name", "nt"),
            patch(
                "nexum_browser.broker._load_state",
                return_value=state,
            ),
            patch(
                "nexum_browser.broker._ping_response",
                return_value=None,
            ),
            patch(
                "nexum_browser.broker._state_process_alive",
                return_value=None,
            ),
            patch(
                "nexum_browser.broker._windows_task_running",
                return_value=True,
            ),
            patch(
                "nexum_browser.broker._remove_windows_task"
            ) as remove_task,
        ):
            status = broker_status()
            self.assertTrue(status["running"])
            self.assertTrue(status["unresponsive"])
            self.assertTrue(status["livenessUnknown"])
            with self.assertRaisesRegex(
                RuntimeError,
                "running but not responding",
            ):
                stop_broker()

        remove_task.assert_not_called()

    def test_windows_stopped_task_overrides_reused_state_pid(
        self,
    ) -> None:
        stale = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        with (
            patch("nexum_browser.broker.os.name", "nt"),
            patch(
                "nexum_browser.broker._load_state",
                return_value=stale,
            ),
            patch(
                "nexum_browser.broker._ping_response",
                return_value=None,
            ),
            patch(
                "nexum_browser.broker._windows_task_running",
                return_value=False,
            ),
            patch(
                "nexum_browser.broker._state_process_alive",
                return_value=True,
            ),
            patch(
                "nexum_browser.broker._clear_state_if_token"
            ) as clear_state,
            patch(
                "nexum_browser.broker._remove_windows_task"
            ) as remove_task,
        ):
            status = broker_status()
            self.assertFalse(status["running"])
            self.assertTrue(status["confirmedStopped"])
            self.assertFalse(stop_broker())

        clear_state.assert_called_once_with(stale["token"])
        remove_task.assert_called_once()

    def test_windows_stopped_task_allows_broker_replacement(
        self,
    ) -> None:
        stale = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        fresh = {
            "pid": 23456,
            "port": 65432,
            "token": "y" * 48,
        }
        ping = {
            "code": "ok",
            "data": {"brokerProtocol": 3},
        }
        with (
            patch("nexum_browser.broker.os.name", "nt"),
            patch(
                "nexum_browser.broker._load_state",
                side_effect=[stale, fresh],
            ),
            patch(
                "nexum_browser.broker._ping_response",
                side_effect=[None, ping],
            ),
            patch(
                "nexum_browser.broker._windows_task_running",
                side_effect=[False, False],
            ),
            patch(
                "nexum_browser.broker._state_process_alive",
                return_value=True,
            ),
            patch(
                "nexum_browser.broker._clear_state_if_token"
            ) as clear_state,
            patch(
                "nexum_browser.broker._remove_windows_task"
            ) as remove_task,
            patch(
                "nexum_browser.broker._spawn",
                return_value=None,
            ) as spawn,
        ):
            self.assertEqual(ensure_broker(), fresh)

        clear_state.assert_called_once_with(stale["token"])
        remove_task.assert_called_once()
        spawn.assert_called_once()

    def test_unix_missing_state_checks_for_live_broker_process(
        self,
    ) -> None:
        with (
            patch("nexum_browser.broker.os.name", "posix"),
            patch("nexum_browser.broker._load_state", return_value={}),
            patch(
                "nexum_browser.broker._unix_broker_pids",
                return_value=[12345],
            ),
            patch("nexum_browser.broker._spawn") as spawn,
        ):
            status = broker_status()
            self.assertTrue(status["running"])
            self.assertTrue(status["stateUncertain"])
            self.assertEqual(status["pids"], [12345])
            with self.assertRaisesRegex(
                RuntimeError,
                "running without state",
            ):
                ensure_broker()
            with self.assertRaisesRegex(
                RuntimeError,
                "running without state",
            ):
                stop_broker()

        spawn.assert_not_called()

    def test_unix_broker_discovery_requests_full_command_line(self) -> None:
        entry = "/tmp/Nexum Browser Install/scripts/browser"
        long_prefix = "/very/" + "long/" * 80
        with (
            patch("nexum_browser.broker.os.name", "posix"),
            patch(
                "nexum_browser.broker.subprocess.run",
                return_value=types.SimpleNamespace(
                    returncode=0,
                    stdout=(
                        "12345 "
                        + long_prefix
                        + "python "
                        + entry
                        + " _broker\n"
                    ),
                ),
            ) as run_ps,
        ):
            self.assertEqual(_unix_broker_pids(entry), [12345])

        self.assertIn("-ww", run_ps.call_args.args[0])

    def test_unix_state_pid_must_still_be_broker(self) -> None:
        with (
            patch("nexum_browser.broker.os.name", "posix"),
            patch(
                "nexum_browser.broker._unix_broker_pids",
                return_value=[999],
            ),
        ):
            self.assertFalse(_state_process_alive({"pid": 123}))

        with (
            patch("nexum_browser.broker.os.name", "posix"),
            patch(
                "nexum_browser.broker._unix_broker_pids",
                return_value=[123],
            ),
        ):
            self.assertTrue(_state_process_alive({"pid": 123}))

        with (
            patch("nexum_browser.broker.os.name", "posix"),
            patch(
                "nexum_browser.broker._unix_broker_pids",
                return_value=None,
            ),
        ):
            self.assertIsNone(_state_process_alive({"pid": 123}))

    def test_passive_run_is_rechecked_inside_broker(self) -> None:
        broker = Broker()
        with patch.object(broker, "ensure_runtime") as ensure_runtime:
            result = broker.handle(
                {
                    "command": "run",
                    "args": {
                        "code": "await cua.getState()",
                        "timeoutMs": 1000,
                        "noStartupTab": True,
                    },
                }
            )

        self.assertEqual(result["code"], "runtime_not_passive_ready")
        self.assertFalse(result["retryable"])
        ensure_runtime.assert_not_called()

    def test_readiness_watchdog_budget_covers_declared_retries(
        self,
    ) -> None:
        runtime = self.FakeRuntime()
        runtime.policy_ready = False
        runtime.contract = types.SimpleNamespace(startup_timeout=2.0)

        self.assertEqual(
            Broker._completion_budget(runtime, 1000),
            39.0,
        )

    def test_warm_watchdog_budget_includes_tool_refresh(self) -> None:
        runtime = self.FakeRuntime()
        runtime.policy_ready = True
        runtime.contract = types.SimpleNamespace(startup_timeout=120.0)

        self.assertEqual(
            Broker._completion_budget(runtime, 30000),
            165.0,
        )

    def test_mcp_outcome_unknown_discards_runtime(self) -> None:
        class LostRuntime(self.FakeRuntime):
            def run(self, code, *, title, timeout_ms):
                raise McpRequestOutcomeUnknown("lost after dispatch")

        runtime = LostRuntime()
        broker = Broker()
        broker.runtime = runtime

        result = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await sideEffect()",
                    "timeoutMs": 1000,
                },
            }
        )

        self.assertEqual(result["code"], "run_outcome_unknown")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertIsNone(broker.runtime)

    def test_missing_windows_state_never_force_stops_running_task(
        self,
    ) -> None:
        with (
            patch("nexum_browser.broker.os.name", "nt"),
            patch("nexum_browser.broker._load_state", return_value={}),
            patch(
                "nexum_browser.broker._windows_task_running",
                return_value=True,
            ),
            patch(
                "nexum_browser.broker._remove_windows_task"
            ) as remove_task,
            patch("nexum_browser.broker._spawn") as spawn,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "state is unavailable",
            ):
                ensure_broker()
            with self.assertRaisesRegex(
                RuntimeError,
                "state is unavailable",
            ):
                stop_broker()

        remove_task.assert_not_called()
        spawn.assert_not_called()

    def test_incompatible_broker_is_not_replaced_implicitly(self) -> None:
        state = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        incompatible = {
            "code": "ok",
            "data": {"brokerProtocol": 2},
        }
        with (
            patch(
                "nexum_browser.broker._load_state",
                return_value=state,
            ),
            patch(
                "nexum_browser.broker._ping_response",
                return_value=incompatible,
            ),
            patch("nexum_browser.broker._request") as request,
            patch(
                "nexum_browser.broker._clear_state_if_token"
            ) as clear_state,
            patch("nexum_browser.broker._spawn") as spawn,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "refusing automatic replacement",
            ):
                ensure_broker()

        request.assert_not_called()
        clear_state.assert_not_called()
        spawn.assert_not_called()

    def test_stalled_runtime_returns_unknown_and_discards_context(
        self,
    ) -> None:
        class StallingRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self.closed = threading.Event()

            def run(self, code, *, title, timeout_ms):
                self.run_calls.append((code, title, timeout_ms))
                self.closed.wait(1)
                raise RuntimeError("runtime connection closed")

            def close(self):
                self.close_calls += 1
                self.closed.set()

        runtime = StallingRuntime()
        broker = Broker()
        broker.runtime = runtime

        with patch(
            "nexum_browser.broker._RUN_COMPLETION_GRACE_SECONDS",
            0,
        ):
            result = broker.handle(
                {
                    "command": "run",
                    "args": {
                        "code": "await sideEffect()",
                        "title": "unknown",
                        "timeoutMs": 1,
                    },
                }
            )

        self.assertEqual(result["code"], "run_outcome_unknown")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertTrue(result["data"]["runtimeDiscarded"])
        self.assertEqual(runtime.close_calls, 1)
        self.assertIsNone(broker.runtime)
        self.assertIsNone(broker.active_operation)

    def test_close_calls_turn_ended_then_closes_runtime(self) -> None:
        runtime = self.FakeRuntime()
        broker = Broker()
        broker.runtime = runtime

        broker.close()

        self.assertEqual(runtime.release_calls, 1)
        self.assertEqual(runtime.close_calls, 1)
        self.assertIsNone(broker.runtime)

    def test_stop_finishes_turn_ended_before_reporting_success(self) -> None:
        events = []

        class OrderedRuntime(self.FakeRuntime):
            def release(self):
                events.append("turn-ended")
                super().release()

            def close(self):
                events.append("runtime-closed")
                super().close()

        runtime = OrderedRuntime()
        broker = Broker()
        broker.runtime = runtime

        result = broker.handle({"command": "__stop__", "args": {}})

        self.assertEqual(result, {"code": "ok", "data": {"stopped": True}})
        self.assertEqual(events, ["turn-ended", "runtime-closed"])
        self.assertTrue(broker.stop_requested)
        self.assertIsNone(broker.runtime)

    def test_stop_reports_turn_ended_failure_after_closing_runtime(self) -> None:
        class ReleaseFailureRuntime(self.FakeRuntime):
            def release(self):
                self.release_calls += 1
                raise RuntimeError("turn_ended failed")

        runtime = ReleaseFailureRuntime()
        broker = Broker()
        broker.runtime = runtime

        result = broker.handle({"command": "__stop__", "args": {}})

        self.assertEqual(result["code"], "runtime_release_failed")
        self.assertFalse(result["retryable"])
        self.assertEqual(
            result["data"],
            {"stopped": True, "turnEnded": False},
        )
        self.assertIn("turn_ended failed", result["message"])
        self.assertTrue(broker.stop_requested)
        self.assertEqual(runtime.release_calls, 1)
        self.assertEqual(runtime.close_calls, 1)
        self.assertIsNone(broker.runtime)

    def test_paused_run_release_failure_preserves_unknown_run(
        self,
    ) -> None:
        class PausedReleaseFailureRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = PendingElicitation(
                    "el_1",
                    "req-1",
                    {"message": "Allow action?"},
                )

            def pending_elicitation(self):
                return self._elicitation

            def release(self):
                self.release_calls += 1
                raise RuntimeError("turn_ended failed")

        runtime = PausedReleaseFailureRuntime()
        broker = Broker()
        broker.runtime = runtime
        operation = ActiveOperation(
            "await sideEffect()",
            "paused",
            1000,
            1,
        )
        operation.state = "awaiting_confirmation"
        broker.active_operation = operation

        result = broker.handle({"command": "__stop__", "args": {}})

        self.assertEqual(result["code"], "runtime_release_failed")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["stopped"])
        self.assertFalse(result["data"]["turnEnded"])
        self.assertTrue(result["data"]["activeRunOutcomeUnknown"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertEqual(result["data"]["operationId"], operation.id)

    def test_stop_reports_unknown_turn_ended_outcome(self) -> None:
        class UnknownReleaseRuntime(self.FakeRuntime):
            def release(self):
                self.release_calls += 1
                raise McpRequestOutcomeUnknown(
                    "lost turn_ended result"
                )

        runtime = UnknownReleaseRuntime()
        broker = Broker()
        broker.runtime = runtime

        result = broker.handle({"command": "__stop__", "args": {}})

        self.assertEqual(result["code"], "stop_outcome_unknown")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertTrue(broker.stop_requested)
        self.assertEqual(runtime.release_calls, 1)
        self.assertEqual(runtime.close_calls, 1)
        self.assertIsNone(broker.runtime)

    def test_paused_run_unknown_release_preserves_operation_id(
        self,
    ) -> None:
        class PausedUnknownReleaseRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = PendingElicitation(
                    "el_1",
                    "req-1",
                    {"message": "Allow action?"},
                )

            def pending_elicitation(self):
                return self._elicitation

            def release(self):
                self.release_calls += 1
                raise McpRequestOutcomeUnknown(
                    "lost turn_ended result"
                )

        runtime = PausedUnknownReleaseRuntime()
        broker = Broker()
        broker.runtime = runtime
        operation = ActiveOperation(
            "await sideEffect()",
            "paused",
            1000,
            1,
        )
        operation.state = "awaiting_confirmation"
        broker.active_operation = operation

        result = broker.handle({"command": "__stop__", "args": {}})

        self.assertEqual(result["code"], "stop_outcome_unknown")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertTrue(result["data"]["activeRunOutcomeUnknown"])
        self.assertEqual(result["data"]["operationId"], operation.id)

    def test_stop_broker_preserves_unknown_release_result(self) -> None:
        state = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        ping = {
            "code": "ok",
            "data": {"brokerProtocol": 3},
        }
        with (
            patch(
                "nexum_browser.broker._load_state",
                return_value=state,
            ),
            patch(
                "nexum_browser.broker._ping_response",
                side_effect=[ping, None],
            ),
            patch(
                "nexum_browser.broker._request",
                return_value={
                    "code": "stop_outcome_unknown",
                    "message": "lost turn_ended result",
                    "retryable": False,
                    "data": {"outcomeUnknown": True},
                },
            ),
            patch(
                "nexum_browser.broker._clear_state_if_token"
            ) as clear_state,
        ):
            with self.assertRaises(BrokerRequestOutcomeUnknown):
                stop_broker()

        clear_state.assert_called_once_with(state["token"])

    def test_stop_broker_wait_budget_covers_turn_ended_timeout(
        self,
    ) -> None:
        state = {
            "pid": 12345,
            "port": 54321,
            "token": "x" * 48,
        }
        ping = {
            "code": "ok",
            "data": {"brokerProtocol": 3},
        }
        with (
            patch(
                "nexum_browser.broker._load_state",
                return_value=state,
            ),
            patch(
                "nexum_browser.broker._ping_response",
                side_effect=[ping, None],
            ),
            patch(
                "nexum_browser.broker._request",
                return_value={"code": "ok"},
            ) as request,
            patch(
                "nexum_browser.broker._maintenance_request_timeout",
                return_value=42,
            ),
            patch(
                "nexum_browser.broker._clear_state_if_token"
            ),
        ):
            self.assertTrue(stop_broker())

        self.assertEqual(
            request.call_args.kwargs["timeout"],
            42,
        )

    def test_confirmation_resume_continues_same_run(self) -> None:
        class ConfirmRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = None
                self._resume = threading.Event()
                self.responses = []

            def run(self, code, *, title, timeout_ms):
                self.run_calls.append((code, title, timeout_ms))
                self._elicitation = PendingElicitation(
                    "el_1",
                    9,
                    {
                        "message": "Allow CDP?",
                        "requestedSchema": {
                            "type": "object",
                            "properties": {},
                        },
                    },
                )
                self._resume.wait(2)
                return {
                    "content": [
                        {"type": "text", "text": "continued"}
                    ],
                    "isError": False,
                }

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(
                self,
                elicitation_id,
                *,
                action,
                content=None,
            ):
                self.responses.append(
                    (elicitation_id, action, content)
                )
                self._elicitation = None
                self._resume.set()

        runtime = ConfirmRuntime()
        broker = Broker()
        broker.runtime = runtime

        first = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await sideEffect()",
                    "title": "confirm",
                    "timeoutMs": 1000,
                },
            }
        )
        self.assertEqual(first["code"], "confirmation_required")
        operation = first["data"]["operationId"]

        stale = broker.handle(
            {
                "command": "_resume",
                "args": {
                    "operation": operation,
                    "elicitation": "el_stale",
                    "decision": "accept",
                },
            }
        )
        self.assertEqual(stale["code"], "elicitation_mismatch")
        self.assertEqual(runtime.responses, [])

        resumed = broker.handle(
            {
                "command": "_resume",
                "args": {
                    "operation": operation,
                    "elicitation": first["data"]["elicitationId"],
                    "decision": "accept",
                },
            }
        )

        self.assertEqual(resumed["code"], "ok")
        self.assertEqual(len(runtime.run_calls), 1)
        self.assertEqual(
            runtime.responses,
            [("el_1", "accept", None)],
        )

    def test_replacement_confirmation_surfaces_new_elicitation(self) -> None:
        class ReplacementRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = None
                self._resume = threading.Event()
                self.responses = []

            def run(self, code, *, title, timeout_ms):
                self._elicitation = PendingElicitation(
                    "el_1",
                    "req-1",
                    {"message": "Allow first action?"},
                )
                self._resume.wait(2)
                return {
                    "content": [{"type": "text", "text": "continued"}],
                    "isError": False,
                }

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(
                self,
                elicitation_id,
                *,
                action,
                content=None,
            ):
                self.responses.append(
                    (elicitation_id, action, content)
                )
                self._elicitation = None
                self._resume.set()

        runtime = ReplacementRuntime()
        broker = Broker()
        broker.runtime = runtime
        first = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await sideEffect()",
                    "timeoutMs": 1000,
                },
            }
        )
        self.assertEqual(first["code"], "confirmation_required")

        runtime._elicitation = PendingElicitation(
            "el_2",
            "req-2",
            {"message": "Allow replacement action?"},
        )
        replacement = broker.handle(
            {
                "command": "_resume",
                "args": {
                    "operation": first["data"]["operationId"],
                    "elicitation": "el_1",
                    "decision": "accept",
                },
            }
        )

        self.assertEqual(
            replacement["code"],
            "confirmation_required",
        )
        self.assertTrue(replacement["data"]["replacement"])
        self.assertEqual(
            replacement["data"]["elicitationId"],
            "el_2",
        )
        self.assertEqual(runtime.responses, [])

        resumed = broker.handle(
            {
                "command": "_resume",
                "args": {
                    "operation": first["data"]["operationId"],
                    "elicitation": "el_2",
                    "decision": "accept",
                },
            }
        )
        self.assertEqual(resumed["code"], "ok")

    def test_withdrawn_confirmation_clears_busy_state_as_unknown(
        self,
    ) -> None:
        class WithdrawnRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = None
                self._closed = threading.Event()

            def run(self, code, *, title, timeout_ms):
                self._elicitation = PendingElicitation(
                    "el_1",
                    "req-1",
                    {"message": "Allow action?"},
                )
                self._closed.wait(2)
                raise RuntimeError("runtime closed")

            def pending_elicitation(self):
                return self._elicitation

            def close(self):
                self.close_calls += 1
                self._closed.set()

        runtime = WithdrawnRuntime()
        broker = Broker()
        broker.runtime = runtime

        first = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await sideEffect()",
                    "timeoutMs": 1000,
                },
            }
        )
        self.assertEqual(first["code"], "confirmation_required")

        runtime._elicitation = None
        reconciled = broker.handle({"command": "reset", "args": {}})

        self.assertEqual(reconciled["code"], "run_outcome_unknown")
        self.assertFalse(reconciled["retryable"])
        self.assertTrue(reconciled["data"]["confirmationWithdrawn"])
        self.assertTrue(reconciled["data"]["outcomeUnknown"])
        self.assertIsNone(broker.active_operation)
        self.assertIsNone(broker.runtime)

        again = broker.handle({"command": "reset", "args": {}})
        self.assertEqual(
            again,
            {
                "code": "ok",
                "data": {"reset": False, "alreadyReset": True},
            },
        )

    def test_cancel_cannot_report_operation_success(self) -> None:
        class ConfirmRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = None
                self._resume = threading.Event()
                self.responses = []

            def run(self, code, *, title, timeout_ms):
                self._elicitation = PendingElicitation(
                    "el_1",
                    9,
                    {"message": "Allow action?"},
                )
                self._resume.wait(2)
                return {
                    "content": [{"type": "text", "text": "done"}],
                    "isError": False,
                }

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(
                self,
                elicitation_id,
                *,
                action,
                content=None,
            ):
                self.responses.append(
                    (elicitation_id, action, content)
                )
                self._elicitation = None
                self._resume.set()

        runtime = ConfirmRuntime()
        broker = Broker()
        broker.runtime = runtime
        first = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await sideEffect()",
                    "title": "cancel",
                    "timeoutMs": 1000,
                },
            }
        )

        result = broker.handle(
            {
                "command": "_cancel",
                "args": {
                    "operation": first["data"]["operationId"],
                    "elicitation": first["data"]["elicitationId"],
                },
            }
        )

        self.assertEqual(result["code"], "run_outcome_unknown")
        self.assertFalse(result["retryable"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertEqual(
            result["data"]["confirmationDecision"],
            "cancel",
        )
        self.assertEqual(
            result["data"]["result"]["content"][0]["text"],
            "done",
        )
        self.assertEqual(runtime.responses[0][1], "cancel")

    def test_stop_preserves_paused_run_unknown_outcome(self) -> None:
        class PausedRuntime(self.FakeRuntime):
            def __init__(self) -> None:
                super().__init__()
                self._elicitation = None
                self._resume = threading.Event()

            def run(self, code, *, title, timeout_ms):
                self._elicitation = PendingElicitation(
                    "el_1",
                    "req-1",
                    {"message": "Allow action?"},
                )
                self._resume.wait(2)
                return {
                    "content": [{"type": "text", "text": "done"}],
                    "isError": False,
                }

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(
                self,
                elicitation_id,
                *,
                action,
                content=None,
            ):
                self._elicitation = None
                self._resume.set()

        runtime = PausedRuntime()
        broker = Broker()
        broker.runtime = runtime
        first = broker.handle(
            {
                "command": "run",
                "args": {
                    "code": "await sideEffect()",
                    "timeoutMs": 1000,
                },
            }
        )
        self.assertEqual(first["code"], "confirmation_required")

        result = broker.handle({"command": "__stop__", "args": {}})

        self.assertEqual(result["code"], "stop_outcome_unknown")
        self.assertFalse(result["retryable"])
        self.assertEqual(
            result["data"]["operationId"],
            first["data"]["operationId"],
        )
        self.assertTrue(result["data"]["stopped"])
        self.assertTrue(result["data"]["turnEnded"])
        self.assertTrue(result["data"]["activeRunOutcomeUnknown"])
        self.assertTrue(result["data"]["outcomeUnknown"])
        self.assertTrue(broker.stop_requested)

    def test_terminal_decision_precedes_known_runtime_error(self) -> None:
        error_result = {
            "content": [
                {"type": "text", "text": "Runtime rejected continuation"}
            ],
            "isError": True,
        }

        for decision, expected_code in (
            ("decline", "operation_declined"),
            ("cancel", "operation_cancelled"),
        ):
            with self.subTest(decision=decision):
                broker = Broker()
                operation = ActiveOperation(
                    "await sideEffect()",
                    "terminal",
                    1000,
                    1,
                )
                operation.terminal_decision = decision
                operation.error = CuaToolError(
                    "Runtime rejected continuation",
                    error_result,
                )
                operation.done.set()
                broker.active_operation = operation

                result = broker._wait_for_operation(operation)

                self.assertEqual(result["code"], expected_code)
                self.assertFalse(result["retryable"])
                self.assertIs(result["data"], error_result)
                self.assertIsNone(broker.active_operation)


class CliContractTests(unittest.TestCase):
    def test_lost_stop_reply_is_outcome_unknown(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch(
                "nexum_browser.cli.stop_broker",
                side_effect=BrokerRequestOutcomeUnknown(
                    "lost stop reply"
                ),
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["stop"])

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "stop_outcome_unknown")
        self.assertFalse(response["retryable"])
        self.assertTrue(response["data"]["outcomeUnknown"])

    def test_stop_unknown_preserves_shutdown_details(self) -> None:
        output = io.StringIO()
        details = {
            "stopped": True,
            "turnEnded": True,
            "activeRunOutcomeUnknown": True,
            "operationId": "op_1",
            "outcomeUnknown": True,
        }
        with (
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch(
                "nexum_browser.cli.stop_broker",
                side_effect=BrokerRequestOutcomeUnknown(
                    "paused run outcome unknown",
                    data=details,
                ),
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["stop"])

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "stop_outcome_unknown")
        self.assertEqual(response["data"], details)

    def test_windows_pid_liveness_distinguishes_dead_from_unknown(
        self,
    ) -> None:
        fake_kernel = types.SimpleNamespace(
            OpenProcess=lambda *args: 0,
            GetLastError=lambda: 87,
        )
        fake_ctypes = types.SimpleNamespace(
            windll=types.SimpleNamespace(kernel32=fake_kernel)
        )
        with (
            patch("nexum_browser.broker.os.name", "nt"),
            patch.dict(sys.modules, {"ctypes": fake_ctypes}),
        ):
            self.assertFalse(_state_process_alive({"pid": 123}))

        fake_kernel.GetLastError = lambda: 5
        with (
            patch("nexum_browser.broker.os.name", "nt"),
            patch.dict(sys.modules, {"ctypes": fake_ctypes}),
        ):
            self.assertIsNone(_state_process_alive({"pid": 123}))

    def test_reset_requires_confirmed_stopped_state(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": False,
                    "stateUncertain": True,
                    "taskRunning": True,
                },
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["reset"])

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "reset_state_unknown")
        self.assertFalse(response["retryable"])

        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": False,
                    "confirmedStopped": True,
                },
            ),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(cli_main(["reset"]), 0)

        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "ok")
        self.assertTrue(response["data"]["alreadyReset"])

    def test_reset_checks_status_inside_operation_lock(self) -> None:
        state = {"entered": False}

        class Lock:
            def __enter__(self):
                state["entered"] = True

            def __exit__(self, *args):
                state["entered"] = False

        def status():
            self.assertTrue(state["entered"])
            return {
                "running": False,
                "confirmedStopped": True,
            }

        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=Lock(),
            ),
            patch(
                "nexum_browser.cli.broker_status",
                side_effect=status,
            ),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(cli_main(["reset"]), 0)

        response = json.loads(output.getvalue())
        self.assertTrue(response["data"]["alreadyReset"])

    def test_windows_argv_transport_preserves_exact_arguments(
        self,
    ) -> None:
        code = ' // a\r\n' * 4000
        original = [
            "run",
            "--title",
            "Deep validation",
            code,
            "--timeout-ms",
            "4321",
        ]
        serialized = json.dumps(original, ensure_ascii=False)
        self.assertLess(len(code), 32767)
        self.assertGreaterEqual(len(serialized), 32767)
        path = (
            Path(tempfile.gettempdir())
            / f"nexum-browser-argv-{uuid.uuid4().hex}.json"
        )
        try:
            path.write_text(
                serialized,
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {_WINDOWS_ARGV_ROOT_ENV: tempfile.gettempdir()},
                clear=False,
            ):
                prepared = _prepare_argv(
                    [_WINDOWS_ARGV_SENTINEL, str(path)]
                )
                self.assertNotIn(_WINDOWS_ARGV_ROOT_ENV, os.environ)
            self.assertTrue(path.exists())
        finally:
            path.unlink(missing_ok=True)

        parsed = build_parser().parse_args(prepared)
        self.assertEqual(parsed.code, code)
        self.assertEqual(parsed.title, "Deep validation")
        self.assertEqual(parsed.timeout_ms, 4321)

    def test_windows_argv_transport_requires_existing_file(
        self,
    ) -> None:
        path = (
            Path(tempfile.gettempdir())
            / f"nexum-browser-argv-{uuid.uuid4().hex}.json"
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "argv file is unavailable",
        ):
            with patch.dict(
                os.environ,
                {_WINDOWS_ARGV_ROOT_ENV: tempfile.gettempdir()},
                clear=False,
            ):
                _prepare_argv(
                    [
                        _WINDOWS_ARGV_SENTINEL,
                        str(path),
                    ]
                )

    def test_windows_argv_transport_preserves_non_launcher_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "user-file.txt"
            path.write_text("do not delete", encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError,
                "not a launcher-owned temp file",
            ):
                with patch.dict(
                    os.environ,
                    {_WINDOWS_ARGV_ROOT_ENV: tempfile.gettempdir()},
                    clear=False,
                ):
                    _prepare_argv(
                        [_WINDOWS_ARGV_SENTINEL, str(path)]
                    )
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "do not delete",
            )

    def test_windows_argv_transport_rejects_symlink_without_touching_target(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target.json"
            target.write_text('["run","1+1"]', encoding="utf-8")
            link = (
                Path(tempfile.gettempdir())
                / f"nexum-browser-argv-{uuid.uuid4().hex}.json"
            )
            link.unlink(missing_ok=True)
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "not a launcher-owned temp file",
                ):
                    with patch.dict(
                        os.environ,
                        {_WINDOWS_ARGV_ROOT_ENV: tempfile.gettempdir()},
                        clear=False,
                    ):
                        _prepare_argv(
                            [_WINDOWS_ARGV_SENTINEL, str(link)]
                        )
                self.assertTrue(link.is_symlink())
                self.assertEqual(
                    target.read_text(encoding="utf-8"),
                    '["run","1+1"]',
                )
            finally:
                link.unlink(missing_ok=True)

    def test_windows_launcher_protocol_matches_python_transport(
        self,
    ) -> None:
        launcher = (ROOT / "scripts/browser.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            f'$argvSentinel = "{_WINDOWS_ARGV_SENTINEL}"',
            launcher,
        )
        self.assertIn(
            f'$argvRootEnvName = "{_WINDOWS_ARGV_ROOT_ENV}"',
            launcher,
        )
        self.assertIn(
            'ConvertTo-Json -Compress -InputObject @($browserArgs)',
            launcher,
        )
        self.assertIn(
            '[IO.File]::WriteAllText($argvFile, $argvJson, $utf8NoBom)',
            launcher,
        )
        self.assertIn(
            '& $pythonCommand.Executable @prefixArgs $browser $argvSentinel $argvFile',
            launcher,
        )
        self.assertIn(
            'Remove-Item -LiteralPath $argvFile -Force',
            launcher,
        )

    def test_windows_argv_transport_uses_launcher_temp_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            launcher_root = root / "launcher"
            python_root = root / "python"
            launcher_root.mkdir()
            python_root.mkdir()
            path = (
                launcher_root
                / f"nexum-browser-argv-{uuid.uuid4().hex}.json"
            )
            path.write_text('["doctor"]', encoding="utf-8")
            with patch.dict(
                os.environ,
                {
                    _WINDOWS_ARGV_ROOT_ENV: str(launcher_root),
                    "TMPDIR": str(python_root),
                },
                clear=False,
            ):
                prepared = _prepare_argv(
                    [_WINDOWS_ARGV_SENTINEL, str(path)]
                )
            self.assertEqual(prepared, ["doctor"])
            self.assertTrue(path.exists())

    def test_windows_argv_transport_requires_launcher_temp_root(
        self,
    ) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(_WINDOWS_ARGV_ROOT_ENV, None)
            with self.assertRaisesRegex(
                RuntimeError,
                _WINDOWS_ARGV_ROOT_ENV,
            ):
                _prepare_argv(
                    [
                        _WINDOWS_ARGV_SENTINEL,
                        str(
                            Path(tempfile.gettempdir())
                            / f"nexum-browser-argv-{uuid.uuid4().hex}.json"
                        ),
                    ]
                )

    def test_windows_transport_ignores_file_without_sentinel(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leave-me.json"
            path.write_text('["leave-me"]', encoding="utf-8")
            prepared = _prepare_argv(["run", str(path)])
            self.assertEqual(prepared, ["run", str(path)])
            self.assertTrue(path.exists())

    def test_public_cli_exposes_only_four_commands(self) -> None:
        parser = build_parser()
        cases = [
            ["doctor"],
            ["run", "1 + 1"],
            ["reset"],
            ["stop"],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                self.assertEqual(
                    parser.parse_args(argv).command,
                    argv[0],
                )

        help_text = parser.format_help()
        for old in (
            "api-call",
            "api-list",
            "click",
            "fill",
            "observe",
            "setup",
            "status",
            "visible-dom",
        ):
            self.assertNotIn(old, help_text)
        self.assertNotIn("_resume", help_text)
        self.assertNotIn("_cancel", help_text)

    def test_no_startup_tab_requires_passive_ready_runtime(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": True,
                    "runtimeActive": True,
                    "policyReady": False,
                },
            ),
            patch("nexum_browser.cli.send_request") as send_request_mock,
            patch(
                "nexum_browser.cli.send_existing_request"
            ) as send_existing_mock,
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["run", "--no-startup-tab", "1 + 1"])

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(
            json.loads(output.getvalue())["code"],
            "runtime_not_passive_ready",
        )
        send_request_mock.assert_not_called()
        send_existing_mock.assert_not_called()

    def test_no_startup_tab_uses_existing_runtime_only(self) -> None:
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": True,
                    "runtimeActive": True,
                    "policyReady": True,
                },
            ),
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch("nexum_browser.cli.send_request") as send_request_mock,
            patch(
                "nexum_browser.cli.send_existing_request",
                return_value={"code": "ok", "data": {"content": []}},
            ) as send_existing_mock,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(
                cli_main(["run", "--no-startup-tab", "1 + 1"]),
                0,
            )

        send_request_mock.assert_not_called()
        send_existing_mock.assert_called_once()
        self.assertTrue(
            send_existing_mock.call_args.args[1]["noStartupTab"]
        )

    def test_run_request_timeout_uses_launch_contract_budget(self) -> None:
        with patch(
            "nexum_browser.cli.discover_launch_contract",
            return_value=types.SimpleNamespace(startup_timeout=10.0),
        ):
            timeout = _run_request_timeout(1000)
        self.assertEqual(timeout, 176.0)

    def test_continuation_timeout_uses_operation_budget(self) -> None:
        with patch(
            "nexum_browser.cli.discover_launch_contract",
            return_value=types.SimpleNamespace(startup_timeout=10.0),
        ):
            self.assertEqual(
                _continuation_request_timeout(
                    {"activeOperation": {"timeoutMs": 300000}}
                ),
                1970.0,
            )

    def test_cancel_uses_operation_continuation_budget(self) -> None:
        status = {
            "running": True,
            "activeOperation": {"timeoutMs": 300000},
        }
        expected_timeout = _continuation_request_timeout(status)
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value=status,
            ),
            patch(
                "nexum_browser.cli.send_existing_request",
                return_value={
                    "code": "operation_cancelled",
                    "retryable": False,
                },
            ) as request,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(
                cli_main(
                    [
                        "_cancel",
                        "--operation",
                        "op_1",
                        "--elicitation",
                        "el_1",
                    ]
                ),
                1,
            )

        self.assertEqual(
            request.call_args.kwargs["timeout"],
            expected_timeout,
        )

    def test_passive_busy_is_not_reported_as_not_ready(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": True,
                    "unresponsive": True,
                },
            ),
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch(
                "nexum_browser.cli.send_existing_request"
            ) as send_existing,
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "run",
                        "--no-startup-tab",
                        "await cua.getState()",
                    ]
                )

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "broker_busy")
        self.assertTrue(response["retryable"])
        self.assertTrue(response["data"]["outcomeUnknown"])
        send_existing.assert_not_called()

    def test_dispatched_timeout_is_not_reported_as_retryable(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": True,
                    "runtimeActive": True,
                    "policyReady": True,
                },
            ),
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch(
                "nexum_browser.cli.send_request",
                side_effect=BrokerRequestTimeout("outcome may be unknown"),
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["run", "await sideEffect()"])

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "run_outcome_unknown")
        self.assertFalse(response["retryable"])
        self.assertTrue(response["data"]["outcomeUnknown"])

    def test_stop_release_failure_is_nonretryable_after_shutdown(
        self,
    ) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch(
                "nexum_browser.cli.stop_broker",
                side_effect=BrokerRuntimeReleaseFailed(
                    "turn_ended failed",
                    data={
                        "stopped": True,
                        "turnEnded": False,
                        "activeRunOutcomeUnknown": True,
                        "operationId": "op_paused",
                        "outcomeUnknown": True,
                    },
                ),
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["stop"])

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "runtime_release_failed")
        self.assertFalse(response["retryable"])
        self.assertEqual(
            response["data"],
            {
                "stopped": True,
                "turnEnded": False,
                "activeRunOutcomeUnknown": True,
                "operationId": "op_paused",
                "outcomeUnknown": True,
            },
        )

    def test_stop_busy_preserves_busy_outcome(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.operation_lock",
                return_value=contextlib.nullcontext(),
            ),
            patch(
                "nexum_browser.cli.stop_broker",
                side_effect=BrokerBusy("run still active"),
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(["stop"])

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "broker_busy")
        self.assertTrue(response["retryable"])

    def test_resume_lost_reply_is_outcome_unknown(self) -> None:
        output = io.StringIO()
        with (
            patch(
                "nexum_browser.cli.broker_status",
                return_value={
                    "running": True,
                    "activeOperation": {"timeoutMs": 300000},
                },
            ),
            patch(
                "nexum_browser.cli.send_existing_request",
                side_effect=BrokerRequestOutcomeUnknown("lost reply"),
            ),
            contextlib.redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as raised:
                cli_main(
                    [
                        "_resume",
                        "--operation",
                        "op_1",
                        "--elicitation",
                        "el_1",
                        "--decision",
                        "accept",
                    ]
                )

        self.assertEqual(raised.exception.code, 1)
        response = json.loads(output.getvalue())
        self.assertEqual(response["code"], "run_outcome_unknown")
        self.assertFalse(response["retryable"])
        self.assertTrue(response["data"]["outcomeUnknown"])

    def test_lost_response_after_dispatch_is_unknown(self) -> None:
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def sendall(self, data):
                self.data = data

            def shutdown(self, how):
                pass

        state = {
            "port": 12345,
            "token": "x" * 48,
        }
        with (
            patch(
                "nexum_browser.broker.socket.create_connection",
                return_value=FakeConnection(),
            ),
            patch(
                "nexum_browser.broker._recv_line",
                return_value=b"",
            ),
        ):
            with self.assertRaises(BrokerRequestOutcomeUnknown):
                _request(
                    state,
                    "run",
                    {"code": "await sideEffect()"},
                    timeout=1,
                )

    def test_incomplete_success_response_after_dispatch_is_unknown(
        self,
    ) -> None:
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def sendall(self, data):
                self.data = data

            def shutdown(self, how):
                pass

        state = {
            "port": 12345,
            "token": "x" * 48,
        }
        for raw in (
            b'{"code":"ok"}\n',
            b'{"code":"ok","data":{}}\n',
            b'{"code":"confirmation_required","data":{}}\n',
        ):
            with (
                patch(
                    "nexum_browser.broker.socket.create_connection",
                    return_value=FakeConnection(),
                ),
                patch(
                    "nexum_browser.broker._recv_line",
                    return_value=raw,
                ),
            ):
                with self.assertRaises(BrokerRequestOutcomeUnknown):
                    _request(
                        state,
                        "run",
                        {"code": "await sideEffect()"},
                        timeout=1,
                    )

    def test_success_without_is_error_is_known(self) -> None:
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def sendall(self, data):
                self.data = data

            def shutdown(self, how):
                pass

        state = {
            "port": 12345,
            "token": "x" * 48,
        }
        with (
            patch(
                "nexum_browser.broker.socket.create_connection",
                return_value=FakeConnection(),
            ),
            patch(
                "nexum_browser.broker._recv_line",
                return_value=b'{"code":"ok","data":{"content":[]}}\n',
            ),
        ):
            result = _request(
                state,
                "run",
                {"code": "1 + 1"},
                timeout=1,
            )

        self.assertEqual(result["code"], "ok")
        self.assertNotIn("isError", result["data"])

    def test_oversized_response_after_dispatch_is_unknown(self) -> None:
        class FakeConnection:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def sendall(self, data):
                self.data = data

            def shutdown(self, how):
                pass

        state = {
            "port": 12345,
            "token": "x" * 48,
        }
        with (
            patch(
                "nexum_browser.broker.socket.create_connection",
                return_value=FakeConnection(),
            ),
            patch(
                "nexum_browser.broker._recv_line",
                side_effect=RuntimeError("message exceeded"),
            ),
        ):
            with self.assertRaises(BrokerRequestOutcomeUnknown):
                _request(
                    state,
                    "run",
                    {"code": "await sideEffect()"},
                    timeout=1,
                )

    def test_internal_resume_and_cancel_contract(self) -> None:
        parser = build_internal_parser()
        resumed = parser.parse_args(
            [
                "_resume",
                "--operation",
                "op_1",
                "--elicitation",
                "el_1",
                "--decision",
                "accept",
                "--content-json",
                '{"confirmed":true}',
            ]
        )
        self.assertEqual(resumed.operation, "op_1")
        self.assertEqual(resumed.elicitation, "el_1")
        self.assertEqual(resumed.decision, "accept")
        self.assertEqual(
            resumed.content,
            {"confirmed": True},
        )

        cancelled = parser.parse_args(
            [
                "_cancel",
                "--operation",
                "op_1",
                "--elicitation",
                "el_1",
            ]
        )
        self.assertEqual(cancelled.operation, "op_1")
        self.assertEqual(cancelled.elicitation, "el_1")

    def test_legacy_browser_dsl_modules_are_removed(self) -> None:
        package = ROOT / "scripts/nexum_browser"
        for name in (
            "direct_cua.py",
            "operations.py",
            "transport.py",
        ):
            self.assertFalse((package / name).exists(), name)
        self.assertFalse((ROOT / "references/advanced.md").exists())


class McpTests(unittest.TestCase):
    @staticmethod
    def make_request_client() -> StdioMcpClient:
        client = object.__new__(StdioMcpClient)
        client._state_lock = threading.Lock()
        client._write_lock = threading.Lock()
        client._closed = threading.Event()
        client._next_request_id = 0
        client._pending = {}
        client._elicitations = {}
        client._tools_dirty = False
        client._allowed_tools = {"js"}
        client._configured_tools = {"js"}
        client._tool_names = {"js"}
        client._write_json = lambda message: None
        return client

    def test_dispatched_tool_connection_loss_is_unknown(self) -> None:
        client = self.make_request_client()

        def send(message):
            pending = client._pending[message["id"]]
            pending.error = McpError("cua_repl exited")
            pending.event.set()

        client._send = send
        with self.assertRaises(McpRequestOutcomeUnknown):
            client.request(
                "tools/call",
                {"name": "js", "arguments": {}},
                timeout=1,
            )

    def test_ambiguous_tool_send_failure_is_unknown(self) -> None:
        client = self.make_request_client()
        client._send = Mock(side_effect=BrokenPipeError("closed"))

        with self.assertRaises(McpRequestOutcomeUnknown):
            client.request(
                "tools/call",
                {"name": "js", "arguments": {}},
                timeout=1,
            )

    def test_tool_jsonrpc_error_is_unknown(self) -> None:
        client = self.make_request_client()

        def send(message):
            pending = client._pending[message["id"]]
            pending.response = {
                "jsonrpc": "2.0",
                "id": message["id"],
                "error": {"code": -32000, "message": "tool lost"},
            }
            pending.event.set()

        client._send = send
        with self.assertRaises(McpRequestOutcomeUnknown):
            client.request(
                "tools/call",
                {"name": "js", "arguments": {}},
                timeout=1,
            )

    def test_invalid_tool_result_is_unknown(self) -> None:
        client = self.make_request_client()

        def send(message):
            pending = client._pending[message["id"]]
            pending.response = {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {},
            }
            pending.event.set()

        client._send = send
        with self.assertRaises(McpRequestOutcomeUnknown):
            client.call_tool("js", {}, timeout=1)

    def test_invalid_tool_result_field_types_are_unknown(self) -> None:
        for result in (
            {"content": [7], "isError": False},
            {"content": [], "isError": "false"},
            {"content": [{"type": 7}], "isError": False},
            {"content": [{"type": "text"}], "isError": False},
            {
                "content": [
                    {
                        "type": "image",
                        "mimeType": "image/png",
                    }
                ],
                "isError": False,
            },
            {
                "content": [
                    {
                        "type": "audio",
                        "data": "abc",
                    }
                ],
                "isError": False,
            },
            {
                "content": [{"type": "resource"}],
                "isError": False,
            },
        ):
            with self.subTest(result=result):
                client = self.make_request_client()

                def send(message, result=result):
                    pending = client._pending[message["id"]]
                    pending.response = {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": result,
                    }
                    pending.event.set()

                client._send = send
                with self.assertRaises(McpRequestOutcomeUnknown):
                    client.call_tool("js", {}, timeout=1)

    def test_tool_list_change_during_refresh_stays_dirty(self) -> None:
        client = self.make_request_client()
        client._configured_tools = {
            "js",
            "js_reset",
            "turn_ended",
        }

        def request(method, params, *, timeout):
            self.assertEqual(method, "tools/list")
            with client._state_lock:
                client._tools_dirty = True
            return {
                "tools": [
                    {"name": "js"},
                    {"name": "js_reset"},
                    {"name": "turn_ended"},
                ]
            }

        client.request = request
        allowed = client.refresh_tools(timeout=1)

        self.assertEqual(
            allowed,
            {"js", "js_reset", "turn_ended"},
        )
        self.assertTrue(client._tools_dirty)

    def test_cancelled_server_elicitation_is_removed(self) -> None:
        client = self.make_request_client()
        client._elicitations["el_1"] = PendingElicitation(
            "el_1",
            "req-1",
            {"message": "Allow action?"},
        )

        client._dispatch(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {
                    "requestId": "req-1",
                    "reason": "server cancelled",
                },
            }
        )

        self.assertIsNone(client.pending_elicitation())

    def test_server_cancel_does_not_cancel_same_id_client_request(
        self,
    ) -> None:
        client = self.make_request_client()
        pending = types.SimpleNamespace(
            error=None,
            event=threading.Event(),
        )
        client._pending[1] = pending
        client._elicitations["el_1"] = PendingElicitation(
            "el_1",
            1,
            {"message": "Allow action?"},
        )

        client._dispatch(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {
                    "requestId": 1,
                    "reason": "server cancelled",
                },
            }
        )

        self.assertIsNone(client.pending_elicitation())
        self.assertIs(client._pending[1], pending)
        self.assertIsNone(pending.error)
        self.assertFalse(pending.event.is_set())

    def test_initialize_rejects_unexpected_protocol_version(self) -> None:
        client = object.__new__(StdioMcpClient)
        client._startup_timeout = 1
        client.request = lambda *args, **kwargs: {
            "protocolVersion": "2024-11-05"
        }
        client.notify = lambda *args, **kwargs: None
        client.refresh_tools = lambda *args, **kwargs: set()
        with self.assertRaisesRegex(
            McpError,
            "unsupported MCP protocol version",
        ):
            client.initialize()


class DoctorTests(unittest.TestCase):
    def test_unknown_probe_skips_reset_reprobe_and_release(self) -> None:
        class UnknownRuntime:
            def __init__(self) -> None:
                self.run_calls = 0
                self.reset_calls = 0
                self.release_calls = 0
                self.close_calls = 0

            def run(self, *args, **kwargs):
                self.run_calls += 1
                raise McpRequestOutcomeUnknown(
                    "lost Browser Runtime result"
                )

            def reset(self):
                self.reset_calls += 1

            def release(self):
                self.release_calls += 1

            def close(self):
                self.close_calls += 1

        checks = []
        runtime = UnknownRuntime()
        contract = types.SimpleNamespace(
            startup_timeout=30.0,
            node_path=Path("/tmp/node"),
        )

        _runtime_browser_checks(checks, contract, runtime)

        self.assertEqual(runtime.run_calls, 1)
        self.assertEqual(runtime.reset_calls, 0)
        self.assertEqual(runtime.release_calls, 0)
        self.assertEqual(runtime.close_calls, 1)
        by_name = {item["name"]: item for item in checks}
        self.assertTrue(
            by_name["js + Browser backend"]["details"]["outcomeUnknown"]
        )
        for name in (
            "js_reset",
            "post-reset bootstrap",
            "turn_ended",
        ):
            self.assertEqual(by_name[name]["status"], "skip")

    def test_unknown_reset_skips_post_reset_probe_and_release(self) -> None:
        class UnknownResetRuntime:
            def __init__(self) -> None:
                self.run_calls = 0
                self.reset_calls = 0
                self.release_calls = 0
                self.close_calls = 0

            def run(self, *args, **kwargs):
                self.run_calls += 1
                return {
                    "content": [{"type": "text", "text": "ok"}],
                    "isError": False,
                }

            def reset(self):
                self.reset_calls += 1
                raise McpRequestOutcomeUnknown("lost reset result")

            def release(self):
                self.release_calls += 1

            def close(self):
                self.close_calls += 1

        checks = []
        runtime = UnknownResetRuntime()
        contract = types.SimpleNamespace(
            startup_timeout=30.0,
            node_path=Path("/tmp/node"),
        )

        _runtime_browser_checks(checks, contract, runtime)

        self.assertEqual(runtime.run_calls, 1)
        self.assertEqual(runtime.reset_calls, 1)
        self.assertEqual(runtime.release_calls, 0)
        self.assertEqual(runtime.close_calls, 1)
        by_name = {item["name"]: item for item in checks}
        self.assertTrue(
            by_name["js_reset"]["details"]["outcomeUnknown"]
        )
        self.assertEqual(
            by_name["post-reset bootstrap"]["status"],
            "skip",
        )
        self.assertEqual(by_name["turn_ended"]["status"], "skip")

    def test_reset_tool_error_is_treated_as_unknown_state(self) -> None:
        class ResetToolErrorRuntime:
            def __init__(self) -> None:
                self.run_calls = 0
                self.reset_calls = 0
                self.release_calls = 0
                self.close_calls = 0

            def run(self, *args, **kwargs):
                self.run_calls += 1
                return {
                    "content": [{"type": "text", "text": "ok"}],
                    "isError": False,
                }

            def reset(self):
                self.reset_calls += 1
                raise CuaToolError(
                    "reset failed",
                    {
                        "content": [
                            {"type": "text", "text": "reset failed"}
                        ],
                        "isError": True,
                    },
                )

            def release(self):
                self.release_calls += 1

            def close(self):
                self.close_calls += 1

        checks = []
        runtime = ResetToolErrorRuntime()
        contract = types.SimpleNamespace(
            startup_timeout=30.0,
            node_path=Path("/tmp/node"),
        )

        _runtime_browser_checks(checks, contract, runtime)

        self.assertEqual(runtime.run_calls, 1)
        self.assertEqual(runtime.reset_calls, 1)
        self.assertEqual(runtime.release_calls, 0)
        self.assertEqual(runtime.close_calls, 1)
        by_name = {item["name"]: item for item in checks}
        self.assertTrue(
            by_name["js_reset"]["details"]["outcomeUnknown"]
        )
        self.assertEqual(
            by_name["post-reset bootstrap"]["status"],
            "skip",
        )
        self.assertEqual(by_name["turn_ended"]["status"], "skip")

    def test_post_reset_probe_failure_skips_release(self) -> None:
        class PostResetFailureRuntime:
            def __init__(self) -> None:
                self.run_calls = 0
                self.reset_calls = 0
                self.release_calls = 0
                self.close_calls = 0

            def run(self, *args, **kwargs):
                self.run_calls += 1
                if self.run_calls == 2:
                    raise CuaToolError(
                        "tab close failed",
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "tab close failed",
                                }
                            ],
                            "isError": True,
                        },
                    )
                return {
                    "content": [{"type": "text", "text": "ok"}],
                    "isError": False,
                }

            def reset(self):
                self.reset_calls += 1

            def release(self):
                self.release_calls += 1

            def close(self):
                self.close_calls += 1

        checks = []
        runtime = PostResetFailureRuntime()
        contract = types.SimpleNamespace(
            startup_timeout=30.0,
            node_path=Path("/tmp/node"),
        )

        _runtime_browser_checks(checks, contract, runtime)

        self.assertEqual(runtime.run_calls, 2)
        self.assertEqual(runtime.reset_calls, 1)
        self.assertEqual(runtime.release_calls, 0)
        self.assertEqual(runtime.close_calls, 1)
        by_name = {item["name"]: item for item in checks}
        self.assertEqual(
            by_name["post-reset bootstrap"]["status"],
            "fail",
        )
        self.assertEqual(by_name["turn_ended"]["status"], "skip")

    def test_failure_category_keeps_network_errors_out_of_acl_path(
        self,
    ) -> None:
        self.assertEqual(
            _failure_category("nodeRepl.fetch request failed"),
            "network",
        )
        self.assertEqual(
            _failure_category("proxy connection access denied"),
            "network",
        )
        self.assertEqual(
            _failure_category("CreateProcessAsUserW failed: 5"),
            "sandbox-acl",
        )

    def test_runtime_failure_details_only_collect_acl_for_access_denied(
        self,
    ) -> None:
        contract = types.SimpleNamespace(
            node_path=Path(r"C:\Runtime\node.exe")
        )
        with (
            patch("nexum_browser.doctor.os.name", "nt"),
            patch(
                "nexum_browser.doctor._windows_acl_details"
            ) as acl_details,
        ):
            network = _runtime_failure_details(
                contract,
                "sandbox probe timed out",
            )
            self.assertEqual(network["category"], "network")
            acl_details.assert_not_called()

            acl_details.return_value = {"aclMismatch": "suspected"}
            denied = _runtime_failure_details(
                contract,
                "CreateProcessAsUserW failed: 5",
            )
            self.assertEqual(denied["category"], "sandbox-acl")
            acl_details.assert_called_once()
            self.assertEqual(denied["aclMismatch"], "suspected")

    def test_proxy_credentials_are_redacted_from_doctor_messages(
        self,
    ) -> None:
        value = _redact_sensitive_text(
            "proxy http://user:secret@proxy.invalid:8080 failed"
        )
        self.assertNotIn("user:secret", value)
        self.assertIn(
            "http://***@proxy.invalid:8080",
            value,
        )

    def test_windows_registry_default_value_is_locale_independent(
        self,
    ) -> None:
        class FakeKey:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        fake = types.SimpleNamespace(
            HKEY_CURRENT_USER=object(),
            HKEY_LOCAL_MACHINE=object(),
        )

        def open_key(root, subkey):
            self.assertIs(root, fake.HKEY_CURRENT_USER)
            self.assertEqual(
                subkey,
                (
                    "Software\\Google\\Chrome\\"
                    "NativeMessagingHosts\\host"
                ),
            )
            return FakeKey()

        fake.OpenKey = open_key
        fake.QueryValueEx = lambda key, name: (
            r"C:\Users\test\native-host.json",
            1,
        )

        with patch.dict(sys.modules, {"winreg": fake}):
            value = _read_windows_registry_default_value(
                (
                    "HKCU\\Software\\Google\\Chrome\\"
                    "NativeMessagingHosts\\host"
                )
            )

        self.assertEqual(
            value,
            r"C:\Users\test\native-host.json",
        )

    def test_windows_acl_diagnostic_is_read_only_and_flags_suspected_mismatch(
        self,
    ) -> None:
        calls = []

        def fake_run(args, timeout=20):
            calls.append(args)
            if args[0] == "whoami":
                return subprocess.CompletedProcess(
                    args,
                    0,
                    stdout=(
                        '"BUILTIN\\\\CodexSandboxUsers",'
                        '"Alias","S-1-5-21-123-456-789-1001"\n'
                    ),
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=(
                    "C:\\\\Runtime\\\\node.exe "
                    "BUILTIN\\\\Users:(I)(RX)\n"
                ),
                stderr="",
            )

        with patch(
            "nexum_browser.doctor._run_process",
            side_effect=fake_run,
        ):
            details = _windows_acl_details(
                Path(r"C:\Runtime\node.exe"),
                "CreateProcessAsUserW failed: 5",
            )

        self.assertEqual(details["aclMismatch"], "suspected")
        self.assertTrue(details["sandboxGroup"])
        self.assertTrue(
            all(
                command[0] in {"whoami", "icacls"}
                for command in calls
            )
        )
        flattened = " ".join(
            part for command in calls for part in command
        ).lower()
        self.assertNotIn("/grant", flattened)
        self.assertNotIn("/reset", flattened)


if __name__ == "__main__":
    unittest.main()
