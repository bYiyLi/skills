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
from unittest.mock import patch


sys.dont_write_bytecode = True

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "skills/nexum-browser"
sys.path.insert(0, str(ROOT / "scripts"))

import browser_task

from nexum_browser.broker import (
    Broker,
    _compatible_ping,
    _write_windows_task_environment,
)
from nexum_browser.cli import build_internal_parser, build_parser
from nexum_browser.common import codex_home, emit
from nexum_browser.doctor import (
    _failure_category,
    _read_windows_registry_default_value,
    _redact_sensitive_text,
    _windows_acl_details,
)
from nexum_browser.mcp import McpError, PendingElicitation, StdioMcpClient
from nexum_browser.runtime import (
    _BOOTSTRAP,
    _BOOTSTRAP_RETRY_PREFIX,
    _BOOTSTRAP_WITH_READINESS,
    CuaRuntime,
    CuaToolError,
    _apply_windows_proxy_fallback,
    _read_contract,
)


class LaunchContractTests(unittest.TestCase):
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
        }
        status = _apply_windows_proxy_fallback(
            env,
            explicit_names={"HTTPS_PROXY", "ALL_PROXY"},
            system_proxies={
                "http": "http://system.invalid:8080",
                "https": "http://system.invalid:8080",
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
        self.assertEqual(status["wininetProxy"], "configured")

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

    def test_first_run_bootstraps_in_same_js_tool_call(self) -> None:
        runtime, client = self.make_runtime()

        result = runtime.run("let probe = 41; probe")

        self.assertEqual(result["content"][0]["text"], "ok")
        self.assertEqual(len(client.calls), 1)
        first = client.calls[0]
        self.assertEqual(first["name"], "js")
        self.assertTrue(
            first["arguments"]["code"].startswith(
                'await import("@oai/cua/tinyskyAlt");\n'
            )
        )
        self.assertIn("agent.browsers.list()", _BOOTSTRAP_WITH_READINESS)
        self.assertIn(
            "__nexumProbeTab = await __nexumBrowser.tabs.new()",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "await __nexumProbeTab.close()",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertIn(
            "Unable to load browser request-header policy",
            _BOOTSTRAP_WITH_READINESS,
        )
        self.assertNotIn(
            "__NEXUM_BROWSER_BOOTSTRAP_RETRY_MARKER__",
            first["arguments"]["code"],
        )
        self.assertIn(
            _BOOTSTRAP_RETRY_PREFIX,
            first["arguments"]["code"],
        )
        self.assertNotIn("setTimeout(", _BOOTSTRAP_WITH_READINESS)
        self.assertLess(
            first["arguments"]["code"].index(
                "__nexumProbeTab = await __nexumBrowser.tabs.new()"
            ),
            first["arguments"]["code"].index("let probe = 41; probe"),
        )
        self.assertIn(
            "let probe = 41; probe",
            first["arguments"]["code"],
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
                        "text": marker
                        + "Unable to load browser request-header policy.",
                    }
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
        self.assertEqual(len(second.calls), 1)
        self.assertTrue(
            second.calls[0]["arguments"]["code"].startswith(
                'await import("@oai/cua/tinyskyAlt");\n'
            )
        )
        first_code = first.calls[0]["arguments"]["code"]
        second_code = second.calls[0]["arguments"]["code"]
        self.assertEqual(first_code, second_code)
        self.assertIn("nodeRepl.write('user-js-ran')", first_code)
        self.assertIn("nodeRepl.write('user-js-ran')", second_code)
        self.assertTrue(runtime.bootstrapped)
        self.assertTrue(runtime.policy_ready)

    def test_user_error_cannot_spoof_bootstrap_retry_marker(self) -> None:
        runtime, client = self.make_runtime()
        calls = 0

        def user_error(name, arguments, *, meta=None, timeout=None):
            nonlocal calls
            calls += 1
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

        self.assertEqual(calls, 1)
        self.assertFalse(runtime.bootstrapped)

    def test_later_runs_reuse_same_context_without_rebootstrap(self) -> None:
        runtime, client = self.make_runtime()
        runtime.run("let probe = 41")
        runtime.run("probe + 1")

        self.assertEqual(len(client.calls), 2)
        self.assertNotIn(
            '@oai/cua/tinyskyAlt',
            client.calls[1]["arguments"]["code"],
        )
        self.assertEqual(
            client.calls[1]["arguments"]["code"],
            "probe + 1",
        )

    def test_reset_uses_js_reset_and_next_run_rebootstraps(self) -> None:
        runtime, client = self.make_runtime()
        runtime.run("let probe = 41")
        result = runtime.reset()
        self.assertFalse(runtime.bootstrapped)
        self.assertTrue(runtime.policy_ready)
        self.assertEqual(client.calls[-1]["name"], "js_reset")
        self.assertEqual(result["content"][0]["text"], "ok")

        runtime.run("typeof probe")
        code = client.calls[-1]["arguments"]["code"]
        self.assertTrue(
            code.startswith('await import("@oai/cua/tinyskyAlt");\n')
        )
        self.assertNotIn("__nexumProbeTab", code)

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
        client.call_tool = lambda *args, **kwargs: expected

        self.assertIs(runtime.run("1 + 1"), expected)

    def test_tool_error_becomes_run_failure(self) -> None:
        runtime, client = self.make_runtime()
        client.call_tool = lambda *args, **kwargs: {
            "content": [
                {"type": "text", "text": "ReferenceError: missing"}
            ],
            "isError": True,
        }

        with self.assertRaisesRegex(CuaToolError, "ReferenceError") as raised:
            runtime.run("missing")

        self.assertTrue(raised.exception.result["isError"])
        self.assertEqual(
            raised.exception.result["content"][0]["text"],
            "ReferenceError: missing",
        )
        self.assertFalse(runtime.bootstrapped)

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
        self.assertIn("turn_ended failed", result["message"])
        self.assertTrue(broker.stop_requested)
        self.assertEqual(runtime.release_calls, 1)
        self.assertEqual(runtime.close_calls, 1)
        self.assertIsNone(broker.runtime)

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

        resumed = broker.handle(
            {
                "command": "_resume",
                "args": {
                    "operation": operation,
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
                    "operation": first["data"]["operationId"]
                },
            }
        )

        self.assertEqual(result["code"], "operation_cancelled")
        self.assertEqual(runtime.responses[0][1], "cancel")


class CliContractTests(unittest.TestCase):
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

    def test_internal_resume_and_cancel_contract(self) -> None:
        parser = build_internal_parser()
        resumed = parser.parse_args(
            [
                "_resume",
                "--operation",
                "op_1",
                "--decision",
                "accept",
                "--content-json",
                '{"confirmed":true}',
            ]
        )
        self.assertEqual(resumed.operation, "op_1")
        self.assertEqual(resumed.decision, "accept")
        self.assertEqual(
            resumed.content,
            {"confirmed": True},
        )

        cancelled = parser.parse_args(
            ["_cancel", "--operation", "op_1"]
        )
        self.assertEqual(cancelled.operation, "op_1")

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
    def test_failure_category_keeps_network_errors_out_of_acl_path(
        self,
    ) -> None:
        self.assertEqual(
            _failure_category("nodeRepl.fetch request failed"),
            "network",
        )
        self.assertEqual(
            _failure_category("CreateProcessAsUserW failed: 5"),
            "sandbox-acl",
        )

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
