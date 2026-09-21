from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.dont_write_bytecode = True
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "skills/nexum-browser"
sys.path.insert(0, str(ROOT / "scripts"))

from nexum_browser.cli import build_internal_parser, build_parser
from nexum_browser.broker import Broker, _compatible_ping
from nexum_browser.common import codex_home, emit, public_api_coverage
from nexum_browser.direct_cua import DirectCuaRuntime, _read_contract
from nexum_browser.mcp import McpError, PendingElicitation, StdioMcpClient
from nexum_browser.operations import BrowserOperations, _output_js
from nexum_browser.runtime import (
    AppServer,
    _ALLOWED_APP_SERVER_METHODS,
    _CONFIG_FALLBACK_REASON,
    _is_missing_config_path_error,
    _parse_json_output,
    diagnose_browser_runtime_error,
    prepare_runtime,
    release_persisted_state,
)


class RuntimeContractTests(unittest.TestCase):
    def test_cli_json_output_is_ascii_safe_for_windows_code_pages(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            emit({"tabGroup": "🔎 Nexum Browser", "title": "中文"})
        raw = output.getvalue()
        self.assertTrue(raw.isascii())
        self.assertEqual(
            json.loads(raw),
            {"tabGroup": "🔎 Nexum Browser", "title": "中文"},
        )

    def test_codex_home_honors_environment_override(self) -> None:
        import os

        with patch.dict(os.environ, {"CODEX_HOME": str(ROOT / ".test-codex-home")}, clear=False):
            self.assertEqual(codex_home(), ROOT / ".test-codex-home")

    def test_multiline_json_diagnostic_output_is_parsed(self) -> None:
        value = """{
          "correct": false,
          "problem": "native host registry key is missing"
        }"""
        self.assertEqual(
            _parse_json_output(value),
            {
                "correct": False,
                "problem": "native host registry key is missing",
            },
        )

    def test_browser_bootstrap_supports_old_and_new_setup_signatures(self) -> None:
        server = object.__new__(AppServer)
        server.browser_client = ROOT / ".test-browser-client.mjs"
        captured = []

        captured_kwargs = []

        def execute(code, **kwargs):
            captured.append(code)
            captured_kwargs.append(kwargs)
            return {}, []

        server._execute_js_once = execute
        with patch(
            "nexum_browser.runtime.build_public_api_contract",
            return_value={"interfaces": {}, "aliases": {}},
        ):
            server._bootstrap_browser()

        self.assertEqual(len(captured), 1)
        self.assertEqual(captured_kwargs[0]["timeout_ms"], 90000)
        self.assertIn("globals: __nexumSetupGlobals", captured[0])
        self.assertIn("elicitationDisplayName: 'Nexum Browser'", captured[0])
        self.assertIn("__nexumSetupResult ?? __nexumSetupGlobals.agent", captured[0])
        self.assertIn("__nexumInvokeDescriptor", captured[0])
        self.assertIn("value.$call", captured[0])
        self.assertIn("Object.prototype.hasOwnProperty.call", captured[0])
        self.assertIn("surface === 'browser-capability'", captured[0])
        self.assertIn("dynamicCapability", captured[0])
        self.assertIn("Optional capability callback member is invalid", captured[0])
        self.assertIn("Browser API surface user is unavailable", captured[0])

    def test_app_server_allowlist_has_no_model_turn_methods(self) -> None:
        self.assertEqual(
            _ALLOWED_APP_SERVER_METHODS,
            {
                "initialize",
                "thread/start",
                "mcpServerStatus/list",
                "mcpServer/tool/call",
            },
        )
        self.assertFalse(any(method.startswith("turn/") for method in _ALLOWED_APP_SERVER_METHODS))
        self.assertFalse(any(method.startswith("review/") for method in _ALLOWED_APP_SERVER_METHODS))

    def test_app_server_rejects_model_turn_before_transport(self) -> None:
        server = object.__new__(AppServer)
        server.proxy = None
        server.seq = 0
        with self.assertRaisesRegex(RuntimeError, "not allowed"):
            server._request("turn/start", {})

    def test_prepare_runtime_uses_private_fallback_for_elevated_windows(self) -> None:
        elevation_error = RuntimeError(
            "Error: start the Windows daemon from a non-elevated terminal; "
            "shared clients must not inherit administrator privileges"
        )
        with (
            patch("nexum_browser.runtime.os.name", "nt"),
            patch(
                "nexum_browser.runtime.daemon_version",
                return_value=({}, "daemon is not running"),
            ),
            patch(
                "nexum_browser.runtime.bootstrap_daemon",
                side_effect=elevation_error,
            ),
        ):
            result = prepare_runtime(ROOT / "codex.exe")

        self.assertEqual(result["backend"], "local-websocket")
        self.assertIn("authenticated loopback app-server", result["fallbackReason"])

    def test_prepare_runtime_reuses_running_managed_daemon(self) -> None:
        with (
            patch(
                "nexum_browser.runtime.daemon_version",
                return_value=({"status": "running"}, None),
            ),
            patch("nexum_browser.runtime.bootstrap_daemon") as bootstrap,
        ):
            result = prepare_runtime(ROOT / "codex")

        self.assertEqual(result["backend"], "managed-daemon")
        self.assertEqual(result["bootstrap"]["status"], "already-running")
        bootstrap.assert_not_called()

    def test_missing_config_path_error_is_narrowly_detected(self) -> None:
        self.assertTrue(
            _is_missing_config_path_error(
                "failed to load configuration: No such file or directory (os error 2)"
            )
        )
        self.assertFalse(_is_missing_config_path_error("failed to load configuration"))
        self.assertFalse(_is_missing_config_path_error("No such file or directory"))
        self.assertIn("Codex Skill loading disabled", _CONFIG_FALLBACK_REASON)

    def test_windows_untrusted_browser_client_error_is_actionable(self) -> None:
        with patch("nexum_browser.runtime.os.name", "nt"):
            message = diagnose_browser_runtime_error(
                "privileged native pipe bridge is not available; browser-client is not trusted"
            )

        self.assertIn("stale or overwritten", message)
        self.assertIn("desktop plugin UI", message)
        self.assertIn("will not repair", message)

    def test_windows_no_browser_surfaces_native_host_diagnostic(self) -> None:
        with (
            patch("nexum_browser.runtime.os.name", "nt"),
            patch(
                "nexum_browser.runtime._run_browser_diagnostic",
                return_value={
                    "correct": False,
                    "problem": (
                        "Windows native host registry key does not exist: "
                        r"HKCU\Software\Google\Chrome\NativeMessagingHosts\com.openai.codexextension"
                    ),
                },
            ),
        ):
            message = diagnose_browser_runtime_error("No browser is available")

        self.assertIn("native host registry key does not exist", message)
        self.assertIn("desktop plugin UI", message)
        self.assertIn("Do not create or repair", message)

    def test_turn_cleanup_uses_node_repl_hook_without_model_turn(self) -> None:
        server = object.__new__(AppServer)
        server.thread_id = "thread-1"
        server.browser_turn_id = "browser-turn-1"
        calls = []

        def request(method, params, timeout=30):
            calls.append((method, params, timeout))
            return {}

        server._request = request
        server._signal_browser_turn_ended()
        server._reset_browser_globals()

        self.assertEqual([call[0] for call in calls], ["mcpServer/tool/call", "mcpServer/tool/call"])
        self.assertEqual(calls[0][1]["tool"], "turn_ended")
        self.assertEqual(calls[0][1]["arguments"]["hook_event_name"], "Stop")
        self.assertEqual(calls[0][1]["arguments"]["session_id"], "thread-1")
        self.assertEqual(calls[0][1]["arguments"]["turn_id"], "browser-turn-1")
        self.assertEqual(calls[1][1]["tool"], "js_reset")

    def test_stale_turn_cleanup_targets_the_stale_thread(self) -> None:
        server = object.__new__(AppServer)
        server.thread_id = "fresh-thread"
        server.browser_turn_id = "fresh-turn"
        calls = []

        def request(method, params, timeout=30):
            calls.append((method, params, timeout))
            return {}

        server._request = request
        server._signal_specific_browser_turn_ended(
            session_id="stale-thread",
            turn_id="stale-turn",
        )

        self.assertEqual(calls[0][0], "mcpServer/tool/call")
        self.assertEqual(calls[0][1]["threadId"], "stale-thread")
        self.assertEqual(calls[0][1]["arguments"]["hook_event_name"], "Stop")
        metadata = json.loads(calls[0][1]["_meta"]["x-codex-turn-metadata"])
        self.assertEqual(metadata["session_id"], "stale-thread")
        self.assertEqual(metadata["turn_id"], "stale-turn")

    def test_selected_returns_object_when_no_tab_is_selected(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"selected": None}, []

        server = FakeServer()
        result = BrowserOperations(server).execute("selected", {})
        self.assertEqual(result, {"selected": None})
        self.assertIn("{selected:null}", server.code)

    def test_visible_dom_adapts_to_available_observation_surface(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {
                    "tabId": "1",
                    "source": "ax",
                    "kind": "accessibility",
                    "dom": "state",
                }, []

        server = FakeServer()
        result = BrowserOperations(server).execute("visible-dom", {"tab": "1"})
        self.assertEqual(result["source"], "ax")
        self.assertIn("__tab.dom_cua!=null", server.code)
        self.assertIn("__tab.ax!=null", server.code)
        self.assertIn("__tab.ax.get('state')", server.code)
        self.assertIn("__targetKind='ax-index'", server.code)

    def test_observe_supports_explicit_semantic_mode(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {
                    "tabId": "1",
                    "mode": "semantic",
                    "source": "playwright",
                    "kind": "semantic-dom",
                    "observation": "snapshot",
                }, []

        server = FakeServer()
        result = BrowserOperations(server).execute(
            "observe", {"tab": "1", "mode": "semantic"}
        )
        self.assertEqual(result["source"], "playwright")
        self.assertIn("domSnapshot()", server.code)
        self.assertIn("__targetKind='locator'", server.code)

    def test_tabs_does_not_require_user_tab_surface(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {
                    "controlled": [],
                    "user": [],
                    "userTabsSupported": False,
                }, []

        server = FakeServer()
        result = BrowserOperations(server).execute("tabs", {})
        self.assertFalse(result["userTabsSupported"])
        self.assertIn("__userApi!=null", server.code)
        self.assertIn("__userApi.openTabs()", server.code)

    def test_snapshot_checks_live_playwright_surface(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "snapshot": "state"}, []

        server = FakeServer()
        BrowserOperations(server).execute("snapshot", {"tab": "1"})
        self.assertIn("__tab.playwright==null", server.code)
        self.assertIn("domSnapshot()", server.code)

    def test_mark_checks_backend_method_before_calling(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "mode": "handoff"}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "mark", {"tab": "1", "mode": "handoff"}
        )
        self.assertIn("typeof __tab.markHandoff!=='function'", server.code)
        self.assertIn("await __tab.markHandoff()", server.code)

    def test_click_accepts_accessibility_index(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "action": "click", "source": "ax"}, []

        server = FakeServer()
        result = BrowserOperations(server).execute(
            "click",
            {"tab": "1", "axIndex": 4},
        )
        self.assertEqual(result["source"], "ax")
        self.assertIn("typeof __tab.click==='function'", server.code)
        self.assertIn("await __tab.click(4)", server.code)
        self.assertIn("__tab.ax!=null", server.code)
        self.assertIn("await __tab.ax.click(4)", server.code)

    def test_fill_uses_ax_set_value_for_replace_semantics(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "action": "fill", "source": "ax"}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "fill",
            {"tab": "1", "axIndex": 2, "text": "replacement"},
        )
        self.assertIn('__tab.setValue(2,"replacement")', server.code)
        self.assertIn('__tab.ax.setValue(2,"replacement")', server.code)
        self.assertNotIn("__tab.ax.typeText", server.code)

    def test_type_accepts_dom_cua_node_id(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "action": "type", "source": "dom-cua"}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "type",
            {"tab": "1", "nodeId": "node-7", "text": "hello"},
        )
        self.assertIn("__tab.dom_cua==null", server.code)
        self.assertIn('"node_id": "node-7"', server.code)
        self.assertIn('__tab.dom_cua.type({"text": "hello"})', server.code)

    def test_point_click_routes_between_ax_and_cua(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "action": "click", "source": "ax"}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "click",
            {"tab": "1", "point": [120, 80]},
        )
        self.assertIn("typeof __tab.click==='function'", server.code)
        self.assertIn("__tab.click([120, 80])", server.code)
        self.assertIn("__tab.ax!=null", server.code)
        self.assertIn("__tab.ax.click([120, 80])", server.code)
        self.assertIn("__tab.cua!=null", server.code)
        self.assertIn('__tab.cua.click({"x": 120, "y": 80})', server.code)

    def test_scroll_prefers_backend_native_or_advertised_capability(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"tabId": "1", "source": "cdp", "result": {}}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "scroll",
            {"tab": "1", "dx": 0, "dy": 300},
        )
        self.assertIn("__tab.dom_cua!=null", server.code)
        self.assertIn("__caps.some(x=>x.id==='cdp')", server.code)
        self.assertIn("__source='cdp'", server.code)

    def test_capability_call_checks_requested_member_exists(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"result": {}}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "api-call",
            {
                "tab": "1",
                "surface": "tab-capability",
                "capability": "cdp",
                "method": "send",
                "args": ["Runtime.evaluate", {"expression": "1"}],
            },
        )
        self.assertIn('"send" in __cap', server.code)
        self.assertIn("Browser capability member is unavailable", server.code)

    def test_advanced_user_surface_checks_live_backend_support(self) -> None:
        class FakeServer:
            def execute_js(self, code, **_kwargs):
                self.code = code
                return {"result": None}, []

        server = FakeServer()
        BrowserOperations(server).execute(
            "api-call",
            {
                "surface": "user",
                "method": "openTabs",
                "args": [],
            },
        )
        self.assertIn("__nexumBrowser.user == null", server.code)
        self.assertIn("Browser API surface user is unavailable", server.code)

    def test_public_api_bridge_covers_every_installed_interface(self) -> None:
        fake_contract = {
            "interfaces": {
                "Browser": {},
                "Tab": {
                    "getJsDialog": {
                        "returns": ["Dialog"],
                        "callbackKinds": [],
                    }
                },
                "AlertDialog": {},
                "PlaywrightAPI": {
                    "locator": {
                        "returns": ["PlaywrightLocator"],
                        "callbackKinds": [],
                    },
                    "expectNavigation": {
                        "returns": [],
                        "callbackKinds": ["zero-arg-async"],
                    },
                },
                "PlaywrightLocator": {
                    "innerText": {"returns": [], "callbackKinds": []}
                },
            },
            "aliases": {"Dialog": ["AlertDialog"]},
        }
        with patch(
            "nexum_browser.common.build_public_api_contract",
            return_value=fake_contract,
        ):
            coverage = public_api_coverage()
        self.assertTrue(
            coverage["complete"],
            f"unreachable public interfaces: {coverage['unreachableInterfaces']}",
        )
        self.assertEqual(coverage["unreachableInterfaces"], [])
        self.assertIn("PlaywrightLocator", coverage["reachableInterfaces"])
        self.assertIn("AlertDialog", coverage["reachableInterfaces"])
        self.assertEqual(coverage["unsupportedCallbackMembers"], [])
        self.assertEqual(
            coverage["callbackMembers"],
            [
                {
                    "member": "PlaywrightAPI.expectNavigation",
                    "kinds": ["zero-arg-async"],
                }
            ],
        )

    def test_public_api_coverage_flags_unrepresentable_callbacks(self) -> None:
        fake_contract = {
            "interfaces": {
                "PlaywrightAPI": {
                    "futureCallback": {
                        "returns": [],
                        "callbackKinds": ["unsupported"],
                    }
                }
            },
            "aliases": {},
        }
        with patch(
            "nexum_browser.common.build_public_api_contract",
            return_value=fake_contract,
        ):
            coverage = public_api_coverage()
        self.assertFalse(coverage["complete"])
        self.assertEqual(
            coverage["unsupportedCallbackMembers"],
            ["PlaywrightAPI.futureCallback"],
        )

    def test_output_js_does_not_redeclare_persistent_repl_variable(self) -> None:
        code = _output_js("{ok:true}")
        self.assertNotIn("const __value", code)
        self.assertNotIn("let __value", code)

    def test_broker_reuses_one_app_server(self) -> None:
        first = object()
        with (
            patch("nexum_browser.broker.is_direct_cua_platform", return_value=False),
            patch("nexum_browser.broker.AppServer", return_value=first) as app_server,
        ):
            broker = Broker()
            self.assertIs(broker.ensure_server(), first)
            self.assertIs(broker.ensure_server(), first)
        app_server.assert_called_once_with()

    def test_broker_reuses_one_direct_cua_runtime(self) -> None:
        first = object()
        with (
            patch("nexum_browser.broker.is_direct_cua_platform", return_value=True),
            patch(
                "nexum_browser.broker.DirectCuaRuntime",
                return_value=first,
            ) as direct,
        ):
            broker = Broker()
            self.assertIs(broker.ensure_server(), first)
            self.assertIs(broker.ensure_server(), first)
        direct.assert_called_once_with()

    def test_broker_ping_reports_runtime_fallback_reason(self) -> None:
        class FakeServer:
            backend = "local-websocket"
            fallback_reason = "isolated browser runtime"

        broker = Broker()
        broker.server = FakeServer()
        response = broker.handle({"command": "__ping__"})
        self.assertEqual(response["data"]["runtimeBackend"], "local-websocket")
        self.assertEqual(
            response["data"]["runtimeFallbackReason"],
            "isolated browser runtime",
        )

    def test_broker_protocol_distinguishes_legacy_and_current_ping(self) -> None:
        legacy = {"code": "ok", "data": {"running": True}}
        current = {
            "code": "ok",
            "data": {"running": True, "brokerProtocol": 2},
        }
        self.assertFalse(_compatible_ping(legacy))
        self.assertTrue(_compatible_ping(current))

    def test_broker_close_releases_runtime(self) -> None:
        class FakeServer:
            def __init__(self) -> None:
                self.released = 0
                self.closed = 0

            def release(self) -> None:
                self.released += 1

            def close(self) -> None:
                self.closed += 1

        server = FakeServer()
        broker = Broker()
        broker.server = server
        broker.close()
        self.assertEqual(server.released, 1)
        self.assertEqual(server.closed, 1)
        self.assertIsNone(broker.server)

    def test_release_persisted_state_targets_saved_session(self) -> None:
        class FakeServer:
            def __init__(
                self,
                *,
                create_thread=True,
                allow_local_fallback=True,
            ) -> None:
                self.create_thread = create_thread
                self.allow_local_fallback = allow_local_fallback
                self.calls = []
                self.closed = False

            def _signal_specific_browser_turn_ended(self, *, session_id, turn_id):
                self.calls.append((session_id, turn_id))

            def close(self) -> None:
                self.closed = True

        server = FakeServer(create_thread=False)
        with (
            patch(
                "nexum_browser.runtime._load_state",
                return_value={
                    "active": True,
                    "threadId": "stale-thread",
                    "browserTurnId": "stale-turn",
                },
            ),
            patch("nexum_browser.runtime.AppServer", return_value=server) as app_server,
            patch("nexum_browser.runtime.deactivate_state") as deactivate,
        ):
            released = release_persisted_state()

        self.assertTrue(released)
        app_server.assert_called_once_with(
            create_thread=False,
            allow_local_fallback=False,
        )
        self.assertEqual(server.calls, [("stale-thread", "stale-turn")])
        self.assertTrue(server.closed)
        deactivate.assert_called_once_with()

    def test_release_persisted_local_state_terminates_owned_app_server(self) -> None:
        with (
            patch(
                "nexum_browser.runtime._load_state",
                return_value={
                    "active": True,
                    "threadId": "local-thread",
                    "browserTurnId": "local-turn",
                    "backend": "local-websocket",
                    "localProcessId": 4321,
                },
            ),
            patch("nexum_browser.runtime._terminate_process_pid") as terminate,
            patch("nexum_browser.runtime.AppServer") as app_server,
            patch("nexum_browser.runtime.deactivate_state") as deactivate,
        ):
            released = release_persisted_state()

        self.assertTrue(released)
        terminate.assert_called_once_with(4321)
        app_server.assert_not_called()
        deactivate.assert_called_once_with()

    def test_stale_thread_recovery_releases_previous_browser_turn(self) -> None:
        server = object.__new__(AppServer)
        server.thread_id = "stale-thread"
        server.browser_turn_id = "stale-turn"
        server._active = True
        server._released = False
        calls = []
        attempts = 0

        def execute_once(_code, **_kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("thread not found")
            return {"ok": True}, []

        def create_thread():
            server.thread_id = "fresh-thread"
            server.browser_turn_id = "fresh-turn"
            server._active = True

        def signal_specific(*, session_id, turn_id):
            calls.append((session_id, turn_id, server.thread_id))

        server._execute_js_once = execute_once
        server._create_thread = create_thread
        server._signal_specific_browser_turn_ended = signal_specific
        server._bootstrap_browser = lambda: None
        server._persist_state = lambda **_kwargs: None

        result = server.execute_js("void 0")
        self.assertEqual(result, ({"ok": True}, []))
        self.assertEqual(calls, [("stale-thread", "stale-turn", "fresh-thread")])

    def test_cli_exposes_setup_status_and_stop(self) -> None:
        parser = build_parser()
        for command in (
            "setup",
            "status",
            "stop",
            "tabs",
            "snapshot",
            "observe",
            "surfaces",
            "api-coverage",
            "api-call",
        ):
            with self.subTest(command=command):
                if command in {"snapshot", "observe", "surfaces"}:
                    parsed = parser.parse_args([command, "--tab", "1"])
                elif command == "api-call":
                    parsed = parser.parse_args([command, "--surface", "browser", "--method", "documentation"])
                else:
                    parsed = parser.parse_args([command])
                self.assertEqual(parsed.command, command)

    def test_cli_exposes_internal_elicitation_resume(self) -> None:
        parser = build_internal_parser()
        parsed = parser.parse_args(
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
        self.assertEqual(parsed.operation, "op_1")
        self.assertEqual(parsed.decision, "accept")
        self.assertEqual(parsed.content, {"confirmed": True})

    def test_public_cli_help_omits_internal_operation_controls(self) -> None:
        help_text = build_parser().format_help()
        self.assertNotIn("_resume", help_text)
        self.assertNotIn("_cancel-operation", help_text)

    def test_mcp_initialize_rejects_unexpected_protocol_version(self) -> None:
        client = object.__new__(StdioMcpClient)
        client._startup_timeout = 1
        client.request = lambda *args, **kwargs: {"protocolVersion": "2024-11-05"}
        client.notify = lambda *args, **kwargs: None
        client.refresh_tools = lambda *args, **kwargs: set()
        with self.assertRaisesRegex(McpError, "unsupported MCP protocol version"):
            client.initialize()

    def test_direct_launch_contract_uses_openai_generated_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            node = root / "node"
            node_repl = root / "node_repl"
            entry = root / "node_modules/@oai/cua-repl/bin/cua-repl.mjs"
            api = (
                root
                / "node_modules/@oai/browser-desktop/environment-docs/codex-app/api.json"
            )
            for executable in (node, node_repl):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text("#!/bin/sh\n", encoding="utf-8")
                executable.chmod(0o755)
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("", encoding="utf-8")
            api.parent.mkdir(parents=True, exist_ok=True)
            api.write_text('{"interfaces":{},"types":{}}', encoding="utf-8")
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
                                "enabled_tools": ["js", "js_reset", "turn_ended"],
                                "startup_timeout_sec": 17,
                                "env_vars": [],
                                "env": {
                                    "CUA_REPL_NODE_REPL_PATH": str(node_repl),
                                    "CUA_REPL_ENABLED_SURFACES": "browser,computer",
                                    "NODE_REPL_NODE_MODULE_DIRS": str(
                                        root / "node_modules"
                                    ),
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            contract = _read_contract(config)

        self.assertEqual(contract.command, str(node))
        self.assertEqual(contract.runtime_version, "26.1")
        self.assertEqual(contract.startup_timeout, 17)
        self.assertEqual(contract.api_json, api)
        self.assertEqual(
            contract.enabled_tools,
            frozenset({"js", "js_reset", "turn_ended"}),
        )

    def test_direct_metadata_stays_stable_across_operations(self) -> None:
        runtime = object.__new__(DirectCuaRuntime)
        runtime.session_id = "session-1"
        runtime.turn_id = "turn-1"
        first = json.loads(runtime._meta()["x-codex-turn-metadata"])
        second = json.loads(runtime._meta()["x-codex-turn-metadata"])
        self.assertEqual(first["session_id"], "session-1")
        self.assertEqual(first["turn_id"], "turn-1")
        self.assertEqual(first, second)

    def test_direct_reset_invalidates_handle_generation(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.calls = []

            def call_tool(self, name, arguments, **kwargs):
                self.calls.append((name, arguments, kwargs))
                return {"content": [], "isError": False}

        runtime = object.__new__(DirectCuaRuntime)
        runtime.client = FakeClient()
        runtime.session_id = "session-1"
        runtime.turn_id = "turn-1"
        runtime.runtime_state = "initialized"
        runtime.handle_generation = 3
        runtime._bridge_installed = True
        runtime.reset()
        self.assertEqual(runtime.runtime_state, "fresh")
        self.assertFalse(runtime._bridge_installed)
        self.assertEqual(runtime.handle_generation, 4)
        self.assertEqual(runtime.client.calls[0][0], "js_reset")

    def test_broker_pauses_and_resumes_direct_elicitation(self) -> None:
        class FakeDirectRuntime(DirectCuaRuntime):
            def __init__(self) -> None:
                self._elicitation = None
                self._resume = threading.Event()
                self.backend = "direct-cua"
                self.fallback_reason = None

            def execute_js(self, _code, **_kwargs):
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
                return {"available": True}, []

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(self, elicitation_id, *, action, content=None):
                self.assertions = (elicitation_id, action, content)
                self._elicitation = None
                self._resume.set()

            def release(self):
                pass

            def close(self):
                pass

        runtime = FakeDirectRuntime()
        broker = Broker()
        broker.server = runtime
        first = broker.handle({"command": "status", "args": {}})
        self.assertEqual(first["code"], "confirmation_required")
        operation_id = first["data"]["operationId"]
        resumed = broker.handle(
            {
                "command": "_resume",
                "args": {
                    "operation": operation_id,
                    "decision": "accept",
                },
            }
        )
        self.assertEqual(resumed, {"code": "ok", "data": {"available": True}})
        self.assertEqual(runtime.assertions, ("el_1", "accept", None))

    def test_broker_decline_and_cancel_cannot_report_operation_success(self) -> None:
        class FakeDirectRuntime(DirectCuaRuntime):
            def __init__(self) -> None:
                self._elicitation = None
                self._resume = threading.Event()
                self.backend = "direct-cua"
                self.fallback_reason = None
                self.responses = []

            def execute_js(self, _code, **_kwargs):
                self._elicitation = PendingElicitation(
                    "el_1",
                    9,
                    {"message": "Allow CDP?", "requestedSchema": {"type": "object"}},
                )
                self._resume.wait(2)
                return {"wouldOtherwiseLookSuccessful": True}, []

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(self, elicitation_id, *, action, content=None):
                self.responses.append((elicitation_id, action, content))
                self._elicitation = None
                self._resume.set()

            def release(self):
                pass

            def close(self):
                pass

        for mode, expected_code in (
            ("decline", "operation_declined"),
            ("cancel", "operation_cancelled"),
        ):
            with self.subTest(mode=mode):
                runtime = FakeDirectRuntime()
                broker = Broker()
                broker.server = runtime
                first = broker.handle({"command": "status", "args": {}})
                operation_id = first["data"]["operationId"]
                if mode == "decline":
                    result = broker.handle(
                        {
                            "command": "_resume",
                            "args": {
                                "operation": operation_id,
                                "decision": "decline",
                            },
                        }
                    )
                else:
                    result = broker.handle(
                        {
                            "command": "_cancel-operation",
                            "args": {"operation": operation_id},
                        }
                    )
                self.assertEqual(result["code"], expected_code)
                self.assertFalse(result["retryable"])
                self.assertEqual(runtime.responses[0][1], mode)

    def test_broker_stop_cancels_pending_elicitation_before_release(self) -> None:
        class FakeDirectRuntime(DirectCuaRuntime):
            def __init__(self) -> None:
                self._elicitation = None
                self._resume = threading.Event()
                self.backend = "direct-cua"
                self.fallback_reason = None
                self.events = []

            def execute_js(self, _code, **_kwargs):
                self._elicitation = PendingElicitation(
                    "el_1",
                    9,
                    {"message": "Allow CDP?"},
                )
                self._resume.wait(2)
                self.events.append("operation-finished")
                return {}, []

            def pending_elicitation(self):
                return self._elicitation

            def respond_elicitation(self, elicitation_id, *, action, content=None):
                self.events.append(f"elicitation-{action}")
                self._elicitation = None
                self._resume.set()

            def release(self):
                self.events.append("turn-ended")

            def close(self):
                self.events.append("runtime-closed")

        runtime = FakeDirectRuntime()
        broker = Broker()
        broker.server = runtime
        first = broker.handle({"command": "status", "args": {}})
        self.assertEqual(first["code"], "confirmation_required")
        broker.handle({"command": "__stop__", "args": {}})
        broker.close()
        self.assertEqual(
            runtime.events,
            [
                "elicitation-cancel",
                "operation-finished",
                "turn-ended",
                "runtime-closed",
            ],
        )

    def test_cli_interaction_targets_are_surface_neutral(self) -> None:
        parser = build_parser()
        click = parser.parse_args(["click", "--tab", "1", "--ax-index", "4"])
        self.assertEqual(click.axIndex, 4)
        typed = parser.parse_args(
            ["type", "--tab", "1", "--node-id", "node-7", "--text", "hello"]
        )
        self.assertEqual(typed.nodeId, "node-7")
        point = parser.parse_args(
            ["press", "--tab", "1", "--point", "[10,20]", "--key", "Enter"]
        )
        self.assertEqual(point.point, [10, 20])


if __name__ == "__main__":
    unittest.main()
