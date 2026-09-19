from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .broker import broker_status, daemon_main, ensure_broker, send_request, stop_broker
from .common import (
    emit,
    fail,
    find_codex,
    load_api_manifest,
    operation_lock,
    parse_json_array,
    parse_json_object,
    PUBLIC_API_SURFACES,
    public_api_coverage,
    validate_member_path,
)
from .runtime import (
    diagnose_browser_runtime_error,
    prepare_runtime,
    release_persisted_state,
    runtime_diagnostics,
)


def add_locator(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    add_locator_arguments(group)
    add_locator_options(parser)


def add_locator_arguments(group: Any) -> None:
    group.add_argument("--selector", help="CSS selector")
    group.add_argument("--role", help="ARIA role, optionally combined with --name")
    group.add_argument("--locator-text", dest="locatorText", help="Visible text")
    group.add_argument("--label", help="Associated label text")
    group.add_argument("--placeholder", help="Input placeholder text")
    group.add_argument("--test-id", dest="testId", help="data-testid value")


def add_locator_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", help="Accessible name used with --role")
    parser.add_argument("--exact", action="store_true", help="Require an exact semantic match")


def add_action_target(
    parser: argparse.ArgumentParser,
    *,
    allow_ax: bool = True,
    allow_dom: bool = True,
    allow_point: bool = True,
) -> None:
    group = parser.add_mutually_exclusive_group(required=True)
    add_locator_arguments(group)
    if allow_ax:
        group.add_argument(
            "--ax-index",
            dest="axIndex",
            type=int,
            help="Accessibility element index returned by an AX observation",
        )
    if allow_dom:
        group.add_argument(
            "--node-id",
            dest="nodeId",
            help="DOM node id returned by a DOM-CUA observation",
        )
    if allow_point:
        group.add_argument(
            "--point",
            type=parse_json_array,
            help='Viewport point as JSON [x,y]; uses AX or CUA when available',
        )
    add_locator_options(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="browser", description="Nexum CLI adapter for the installed OpenAI Browser Runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Check Browser Runtime availability and selected browser")
    sub.add_parser("setup", help="Configure and verify the Codex app-server runtime")
    sub.add_parser("browsers", help="List Browser Runtime browser backends")
    select = sub.add_parser("select", help="Select the browser backend used by later commands")
    group = select.add_mutually_exclusive_group(required=True)
    group.add_argument("--browser", help="default, chrome, edge, iab, extension, or a runtime browser id")
    group.add_argument("--url", help="Let Browser Runtime choose the best browser for a target URL")

    docs = sub.add_parser("docs", help="Read one Browser Runtime documentation topic")
    docs.add_argument("--name", required=True)

    api_list = sub.add_parser("api-list", help="Inspect the installed Browser Runtime public API manifest")
    api_list.add_argument("--interface", dest="interface_name")
    api_list.add_argument("--member")

    api_type = sub.add_parser("api-type", help="Inspect one Browser Runtime API type definition")
    api_type.add_argument("--name", required=True)
    sub.add_parser(
        "api-coverage",
        help="Verify that every installed public Browser Runtime interface is reachable",
    )

    sub.add_parser("tabs", help="List controlled tabs and claimable user tabs")
    sub.add_parser("selected", help="Return the currently selected controlled tab")
    claim = sub.add_parser("claim", help="Claim an existing user tab")
    claim.add_argument("--tab", required=True)
    opened = sub.add_parser("open", help="Open a URL in a new controlled tab")
    opened.add_argument("--url", required=True)

    for name in ("back", "forward", "reload", "close"):
        child = sub.add_parser(name)
        child.add_argument("--tab", required=True)

    snapshot = sub.add_parser(
        "snapshot",
        help="Read the Playwright semantic DOM snapshot for a controlled tab",
    )
    snapshot.add_argument("--tab", required=True)

    visible_dom = sub.add_parser(
        "visible-dom",
        help="Compatibility observation command that adapts to backend surface support",
    )
    visible_dom.add_argument("--tab", required=True)

    observe = sub.add_parser(
        "observe",
        help="Inspect a tab through the best supported Browser Runtime observation surface",
    )
    observe.add_argument("--tab", required=True)
    observe.add_argument(
        "--mode",
        choices=["auto", "semantic", "accessibility", "visible"],
        default="auto",
    )

    surfaces = sub.add_parser(
        "surfaces",
        help="Inspect Browser Runtime surfaces actually available on a controlled tab",
    )
    surfaces.add_argument("--tab", required=True)

    goto = sub.add_parser("goto", help="Navigate a controlled tab")
    goto.add_argument("--tab", required=True)
    goto.add_argument("--url", required=True)

    mark = sub.add_parser("mark", help="Keep a tab as a handoff or deliverable across browser-turn cleanup")
    mark.add_argument("--tab", required=True)
    mark.add_argument("--mode", choices=["handoff", "deliverable"], required=True)

    click = sub.add_parser(
        "click",
        help="Click through a semantic locator, AX index, DOM node id, or viewport point",
    )
    click.add_argument("--tab", required=True)
    add_action_target(click)

    fill = sub.add_parser(
        "fill",
        help="Replace an input value through a semantic locator or AX index",
    )
    fill.add_argument("--tab", required=True)
    add_action_target(fill, allow_dom=False, allow_point=False)
    fill.add_argument("--text", required=True)

    typed = sub.add_parser(
        "type",
        help="Type text without clearing existing content through a supported interaction surface",
    )
    typed.add_argument("--tab", required=True)
    add_action_target(typed)
    typed.add_argument("--text", required=True)

    press = sub.add_parser(
        "press",
        help="Press a key through a semantic locator, AX index, DOM node id, or viewport point",
    )
    press.add_argument("--tab", required=True)
    add_action_target(press)
    press.add_argument("--key", required=True)

    upload = sub.add_parser("upload", help="Advanced file chooser flow: click a file input/control and set local files")
    upload.add_argument("--tab", required=True)
    add_locator(upload)
    upload.add_argument("--file", action="append", dest="files", required=True, help="Absolute local file path; repeat for multiple files")
    upload.add_argument("--timeout-ms", dest="timeoutMs", type=int, default=10000)

    download = sub.add_parser("download", help="Advanced download flow: wait for a download while clicking a locator")
    download.add_argument("--tab", required=True)
    add_locator(download)
    download.add_argument("--timeout-ms", dest="timeoutMs", type=int, default=10000)

    click_nav = sub.add_parser("click-nav", help="Advanced click that is expected to cause navigation")
    click_nav.add_argument("--tab", required=True)
    add_locator(click_nav)
    click_nav.add_argument("--url", help="Optional expected URL")
    click_nav.add_argument("--wait-until", dest="waitUntil", choices=["commit", "domcontentloaded", "load", "networkidle"])
    click_nav.add_argument("--timeout-ms", dest="timeoutMs", type=int, default=10000)

    scroll = sub.add_parser(
        "scroll",
        help="Scroll the page by CSS pixels through DOM-CUA, CUA, or CDP as available",
    )
    scroll.add_argument("--tab", required=True)
    scroll.add_argument("--dx", type=int, default=0)
    scroll.add_argument("--dy", type=int, required=True)
    scroll.add_argument(
        "--point",
        type=parse_json_array,
        help='Optional viewport anchor as JSON [x,y] for CUA scrolling',
    )
    scroll.add_argument(
        "--node-id",
        dest="nodeId",
        help="Optional DOM-CUA node id to scroll within",
    )

    evaluate = sub.add_parser("evaluate", help="Evaluate JavaScript in the page through CDP Runtime.evaluate")
    evaluate.add_argument("--tab", required=True)
    evaluate.add_argument("--expression", required=True)

    screenshot = sub.add_parser("screenshot", help="Capture a screenshot and return a local image path")
    screenshot.add_argument("--tab", required=True)
    screenshot.add_argument("--full-page", dest="fullPage", action="store_true")
    screenshot.add_argument("--clip", type=parse_json_object, help='JSON: {"x":0,"y":0,"width":100,"height":100}')

    logs = sub.add_parser("dev-logs", help="Read developer console logs")
    logs.add_argument("--tab", required=True)
    logs.add_argument("--options", type=parse_json_object, default={})

    history = sub.add_parser("history", help="Read browser history only when explicitly required")
    history.add_argument("--query", action="append", dest="queries")
    history.add_argument("--limit", type=int)
    history.add_argument("--from", dest="from_time")
    history.add_argument("--to", dest="to_time")

    capabilities = sub.add_parser("capabilities", help="List optional browser- or tab-scoped runtime capabilities")
    capabilities.add_argument("--tab")

    api = sub.add_parser("api-call", help="Advanced call into the documented Browser Runtime API surface")
    api.add_argument(
        "--surface",
        required=True,
        choices=[
            *PUBLIC_API_SURFACES,
            "browser-capability",
            "tab-capability",
            "handle",
        ],
    )
    api.add_argument("--tab")
    api.add_argument("--capability")
    api.add_argument("--handle")
    api.add_argument("--method", required=True, type=validate_member_path)
    api.add_argument("--args-json", dest="args", type=parse_json_array, default=[])
    api.add_argument("--no-await", dest="noAwait", action="store_true", help="Store a returned Promise/handle without awaiting it")
    api.add_argument("--result", choices=["auto", "image"], default="auto")
    api.add_argument("--timeout-ms", dest="timeoutMs", type=int, default=30000)

    sub.add_parser("stop", help="Release the nexum-browser runtime session")
    return parser


def api_list(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_api_manifest()
    interfaces = manifest.get("interfaces") or {}
    if args.interface_name is None:
        return {
            "interfaces": [
                {"name": name, "members": sorted(value.keys()) if isinstance(value, dict) else []}
                for name, value in sorted(interfaces.items())
            ]
        }
    interface = interfaces.get(args.interface_name)
    if not isinstance(interface, dict):
        raise RuntimeError(f"Unknown Browser API interface: {args.interface_name}")
    if args.member is not None:
        member = interface.get(args.member)
        if not isinstance(member, dict):
            raise RuntimeError(f"Unknown Browser API member: {args.interface_name}.{args.member}")
        return {"interface": args.interface_name, "member": args.member, "declarations": member.get("declarations") or [], "metadata": {k: v for k, v in member.items() if k != "declarations"}}
    return {
        "interface": args.interface_name,
        "members": [
            {"name": name, "declarations": value.get("declarations") or [], "metadata": {k: v for k, v in value.items() if k != "declarations"}}
            for name, value in interface.items()
            if isinstance(value, dict)
        ],
    }


def api_type(args: argparse.Namespace) -> dict[str, Any]:
    manifest = load_api_manifest()
    types = manifest.get("types") or {}
    value = types.get(args.name)
    if value is None:
        raise RuntimeError(f"Unknown Browser API type: {args.name}")
    return {"name": args.name, "definition": value}


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "_broker":
        return daemon_main()

    parser = build_parser()
    ns = parser.parse_args()

    if ns.command == "api-list":
        try:
            emit({"code": "ok", "data": api_list(ns)})
            return 0
        except Exception as exc:
            fail("api_manifest_error", str(exc), retryable=False)

    if ns.command == "api-type":
        try:
            emit({"code": "ok", "data": api_type(ns)})
            return 0
        except Exception as exc:
            fail("api_manifest_error", str(exc), retryable=False)

    if ns.command == "api-coverage":
        try:
            emit({"code": "ok", "data": public_api_coverage()})
            return 0
        except Exception as exc:
            fail("api_manifest_error", str(exc), retryable=False)

    if ns.command == "status":
        data = runtime_diagnostics()
        broker = broker_status()
        data["broker"] = broker
        if broker.get("running") and broker.get("runtimeActive"):
            data["available"] = True
            if broker.get("runtimeBackend"):
                data["runtimeBackend"] = broker["runtimeBackend"]
        emit({"code": "ok", "data": data})
        return 0

    if ns.command == "setup":
        broker_was_running = bool(broker_status().get("running"))
        try:
            with operation_lock(timeout=180):
                runtime = prepare_runtime(find_codex())
                ensure_broker()
                response = send_request("status", {}, timeout=120)
                if response.get("code") != "ok":
                    raise RuntimeError(str(response.get("message") or response))
                broker = broker_status()
                active_backend = broker.get("runtimeBackend")
                if active_backend and active_backend != runtime.get("backend"):
                    runtime = {
                        **runtime,
                        "preparedBackend": runtime.get("backend"),
                        "backend": active_backend,
                    }
                if broker.get("runtimeFallbackReason"):
                    runtime["fallbackReason"] = broker["runtimeFallbackReason"]
            emit(
                {
                    "code": "ok",
                    "data": {
                        "runtime": runtime,
                        "broker": broker,
                        "browser": response.get("data") or {},
                    },
                }
            )
            return 0
        except Exception as exc:
            if not broker_was_running:
                try:
                    stop_broker()
                except Exception:
                    pass
            fail("setup_failed", diagnose_browser_runtime_error(exc), retryable=False)

    if ns.command == "stop":
        try:
            with operation_lock(timeout=60):
                stopped = stop_broker()
                if not stopped:
                    released_stale = release_persisted_state()
                else:
                    released_stale = False
            emit(
                {
                    "code": "ok",
                    "data": {
                        "released": stopped or released_stale,
                        "alreadyReleased": not stopped and not released_stale,
                    },
                }
            )
            return 0
        except Exception as exc:
            fail("runtime_release_failed", str(exc), retryable=True)

    args = vars(ns).copy()
    command = args.pop("command")
    if command == "history":
        args["from"] = args.pop("from_time", None)
        args["to"] = args.pop("to_time", None)

    broker = broker_status()
    cold_start_timeout = (
        120 if not (broker.get("running") and broker.get("runtimeActive")) else 60
    )
    request_timeout = max(
        cold_start_timeout,
        int(args.get("timeoutMs") or 0) / 1000 + 15,
    )
    try:
        with operation_lock(timeout=request_timeout + 15):
            response = send_request(command, args, timeout=request_timeout)
    except Exception as exc:
        fail("runtime_unavailable", diagnose_browser_runtime_error(exc), retryable=True)
    emit(response)
    return 0 if response.get("code") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
