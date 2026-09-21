from __future__ import annotations

import json
from typing import Any, Protocol

from .common import MARKER, PUBLIC_API_SURFACES, save_images


class BrowserRuntime(Protocol):
    def execute_js(
        self,
        code: str,
        *,
        title: str = "Browser action",
        timeout_ms: int = 30000,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]: ...


def _output_js(expression: str) -> str:
    return (
        f"nodeRepl.write({json.dumps(MARKER)} + "
        f"Buffer.from(JSON.stringify(({expression}))).toString('base64'));"
    )


def _tab(tab_id: str) -> str:
    return f"var __tab = await globalThis.__nexumBrowser.tabs.get({json.dumps(tab_id)});"


def _locator_js(args: dict[str, Any]) -> str:
    if args.get("selector") is not None:
        return f"__tab.playwright.locator({json.dumps(args['selector'])})"
    if args.get("role") is not None:
        options: dict[str, Any] = {}
        if args.get("name") is not None:
            options["name"] = args["name"]
        if args.get("exact"):
            options["exact"] = True
        return f"__tab.playwright.getByRole({json.dumps(args['role'])},{json.dumps(options)})"
    for key, method in (
        ("locatorText", "getByText"),
        ("label", "getByLabel"),
        ("placeholder", "getByPlaceholder"),
    ):
        if args.get(key) is not None:
            options = {"exact": True} if args.get("exact") else {}
            return f"__tab.playwright.{method}({json.dumps(args[key])},{json.dumps(options)})"
    if args.get("testId") is not None:
        return f"__tab.playwright.getByTestId({json.dumps(args['testId'])})"
    raise RuntimeError("A locator is required")


def _has_locator(args: dict[str, Any]) -> bool:
    return any(
        args.get(key) is not None
        for key in (
            "selector",
            "role",
            "locatorText",
            "label",
            "placeholder",
            "testId",
        )
    )


def _point(args: dict[str, Any]) -> list[int | float] | None:
    value = args.get("point")
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(
            isinstance(item, bool) or not isinstance(item, (int, float))
            for item in value
        )
    ):
        raise RuntimeError("--point must be a JSON array with two numeric values: [x,y]")
    return value


def _key_sequence(key: str) -> list[str]:
    parts = [part for part in key.split("+") if part]
    return parts or [key]


class BrowserOperations:
    def __init__(self, server: BrowserRuntime) -> None:
        self.server = server

    def _js(self, code: str, *, title: str, timeout_ms: int = 30000) -> dict[str, Any]:
        return self.server.execute_js(code, title=title, timeout_ms=timeout_ms)[0]

    def execute(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        b = "globalThis.__nexumBrowser"

        if command == "status":
            code = self._output_status()
            return self._js(code, title="Check browser status")

        if command == "browsers":
            return self._js(
                _output_js("{selectedBrowserId:globalThis.__nexumBrowser.browserId,browsers:await globalThis.__nexumBrowserAgent.browsers.list()}"),
                title="List browsers",
            )

        if command == "select":
            mode = "url" if args.get("url") else ("default" if args.get("browser") == "default" else "selector")
            value = args.get("url") or args.get("browser")
            code = f"var __selected=await globalThis.__nexumSelectBrowser({json.dumps(mode)},{json.dumps(value)});" + _output_js(
                "{selectedBrowserId:globalThis.__nexumBrowser.browserId,selected:__selected}"
            )
            return self._js(code, title="Select browser")

        if command == "docs":
            code = f"var __doc=await globalThis.__nexumReadDoc({json.dumps(args['name'])});" + _output_js("{name:" + json.dumps(args["name"]) + ",content:__doc}")
            return self._js(code, title="Read browser documentation")

        if command == "tabs":
            return self._js(
                (
                    "var __controlled=await globalThis.__nexumBrowser.tabs.list();"
                    "var __userApi=globalThis.__nexumBrowser.user;"
                    "var __userTabs=__userApi!=null?await __userApi.openTabs():[];"
                    + _output_js(
                        "{controlled:__controlled,user:__userTabs,"
                        "userTabsSupported:__userApi!=null}"
                    )
                ),
                title="List browser tabs",
            )

        if command == "selected":
            code = f"var __tab=await {b}.tabs.selected();" + _output_js(
                "__tab?{tabId:__tab.id,title:await __tab.title(),url:await __tab.url()}:{selected:null}"
            )
            return self._js(code, title="Get selected browser tab")

        if command == "claim":
            code = (
                f"if({b}.user==null)throw new Error('User-tab claiming is unavailable on the selected backend');"
                f"var __tab=await {b}.user.claimTab({json.dumps(str(args['tab']))});"
            ) + _output_js(
                "{tabId:__tab.id,title:await __tab.title(),url:await __tab.url()}"
            )
            return self._js(code, title="Claim browser tab")

        if command == "open":
            url = json.dumps(args["url"])
            code = (
                f"var __tab=await {b}.tabs.new();"
                f"try {{ await __tab.goto({url}); }} catch (__error) {{ try {{ await __tab.close(); }} catch {{}} throw __error; }}"
                + _output_js("{tabId:__tab.id,title:await __tab.title(),url:await __tab.url()}")
            )
            return self._js(code, title="Open browser tab")

        if command in {"goto", "back", "forward", "reload", "close"}:
            code = _tab(args["tab"])
            if command == "goto":
                code += f"await __tab.goto({json.dumps(args['url'])});"
            else:
                code += f"await __tab.{command}();"
            if command == "close":
                code += _output_js("{tabId:" + json.dumps(args["tab"]) + ",closed:true}")
            else:
                code += _output_js("{tabId:__tab.id,title:await __tab.title(),url:await __tab.url()}")
            return self._js(code, title=f"Browser {command}")

        if command == "mark":
            code = _tab(args["tab"])
            method = "markHandoff" if args["mode"] == "handoff" else "markDeliverable"
            code += (
                f"if(typeof __tab.{method}!=='function')"
                f"throw new Error('Tab {args['mode']} marking is unavailable on the selected backend');"
                f"await __tab.{method}();"
                + _output_js("{tabId:__tab.id,mode:" + json.dumps(args["mode"]) + "}")
            )
            return self._js(code, title="Mark browser tab")

        if command == "snapshot":
            code = (
                _tab(args["tab"])
                + "if(__tab.playwright==null)throw new Error('Playwright semantic DOM is unavailable on the selected backend');"
                + "var __snapshot=await __tab.playwright.domSnapshot();"
                + _output_js(
                    "{tabId:__tab.id,title:await __tab.title(),url:await __tab.url(),snapshot:__snapshot}"
                )
            )
            return self._js(code, title="Inspect browser DOM")

        if command == "observe":
            return self._observe(args)

        if command == "visible-dom":
            legacy = dict(args)
            legacy["mode"] = "visible"
            return self._observe(legacy, legacy_visible_dom=True)

        if command == "surfaces":
            code = (
                _tab(args["tab"])
                + "var __caps=await __tab.capabilities.list();"
                + "var __infos=await globalThis.__nexumBrowserAgent.browsers.list();"
                + "var __browserInfo=__infos.find(x=>x.id===globalThis.__nexumBrowser.browserId)||{id:globalThis.__nexumBrowser.browserId};"
                + _output_js(
                    "{tabId:__tab.id,browser:__browserInfo,"
                    "surfaces:{unified:typeof __tab.getAXState==='function',"
                    "playwright:__tab.playwright!=null,ax:__tab.ax!=null,"
                    "cua:__tab.cua!=null,domCua:__tab.dom_cua!=null,"
                    "content:__tab.content!=null,clipboard:__tab.clipboard!=null,"
                    "dev:__tab.dev!=null},capabilities:__caps}"
                )
            )
            return self._js(code, title="Inspect browser API surfaces")

        if command in {"click", "fill", "type", "press"}:
            code = _tab(args["tab"]) + "var __source=null;"
            point = _point(args)
            if _has_locator(args):
                code += (
                    "if(__tab.playwright==null)throw new Error('Playwright interaction is unavailable on the selected backend');"
                    f"var __loc={_locator_js(args)};"
                    "__source='playwright';"
                )
                if command == "click":
                    code += "await __loc.click();"
                elif command == "fill":
                    code += f"await __loc.fill({json.dumps(args['text'])});"
                elif command == "type":
                    code += f"await __loc.type({json.dumps(args['text'])});"
                else:
                    code += f"await __loc.press({json.dumps(args['key'])});"
            elif args.get("axIndex") is not None:
                index = int(args["axIndex"])
                code += (
                    "__source='ax';"
                )
                if command == "click":
                    code += (
                        f"if(typeof __tab.click==='function')await __tab.click({index});"
                        f"else if(__tab.ax!=null)await __tab.ax.click({index});"
                        "else throw new Error('Accessibility interaction is unavailable on the selected backend');"
                    )
                elif command == "fill":
                    code += (
                        f"if(typeof __tab.setValue==='function')await __tab.setValue({index},{json.dumps(args['text'])});"
                        f"else if(__tab.ax!=null)await __tab.ax.setValue({index},{json.dumps(args['text'])});"
                        "else throw new Error('Accessibility value replacement is unavailable on the selected backend');"
                    )
                elif command == "type":
                    code += (
                        f"if(typeof __tab.typeText==='function')await __tab.typeText({index},{json.dumps(args['text'])});"
                        f"else if(__tab.ax!=null)await __tab.ax.typeText({index},{json.dumps(args['text'])});"
                        "else throw new Error('Accessibility text entry is unavailable on the selected backend');"
                    )
                else:
                    code += (
                        f"if(typeof __tab.pressKey==='function')await __tab.pressKey({index},{json.dumps(args['key'])});"
                        f"else if(__tab.ax!=null)await __tab.ax.pressKey({index},{json.dumps(args['key'])});"
                        "else throw new Error('Accessibility key input is unavailable on the selected backend');"
                    )
            elif args.get("nodeId") is not None:
                if command == "fill":
                    raise RuntimeError(
                        "fill requires a Playwright locator or AX index because DOM-CUA type does not replace the existing value"
                    )
                node_id = str(args["nodeId"])
                code += (
                    "if(__tab.dom_cua==null)throw new Error('DOM-CUA interaction is unavailable on the selected backend');"
                    "__source='dom-cua';"
                )
                if command == "click":
                    code += f"await __tab.dom_cua.click({json.dumps({'node_id': node_id})});"
                elif command == "type":
                    code += (
                        f"await __tab.dom_cua.click({json.dumps({'node_id': node_id})});"
                        f"await __tab.dom_cua.type({json.dumps({'text': args['text']})});"
                    )
                else:
                    code += (
                        f"await __tab.dom_cua.click({json.dumps({'node_id': node_id})});"
                        f"await __tab.dom_cua.keypress({json.dumps({'keys': _key_sequence(str(args['key']))})});"
                    )
            elif point is not None:
                if command == "fill":
                    raise RuntimeError(
                        "fill requires a Playwright locator or AX index; use type for coordinate-based text entry"
                    )
                point_json = json.dumps(point)
                cua_point = {"x": point[0], "y": point[1]}
                code += (
                    "if(typeof __tab.click==='function'){"
                    "__source='ax';"
                )
                if command == "click":
                    code += f"await __tab.click({point_json});"
                elif command == "type":
                    code += (
                        f"await __tab.click({point_json});"
                        f"if(typeof __tab.typeText==='function')await __tab.typeText(null,{json.dumps(args['text'])});"
                        f"else if(__tab.ax!=null)await __tab.ax.typeText(null,{json.dumps(args['text'])});"
                        "else throw new Error('Coordinate text entry is unavailable on the selected backend');"
                    )
                else:
                    code += (
                        f"await __tab.click({point_json});"
                        f"if(typeof __tab.pressKey==='function')await __tab.pressKey(null,{json.dumps(args['key'])});"
                        f"else if(__tab.ax!=null)await __tab.ax.pressKey(null,{json.dumps(args['key'])});"
                        "else throw new Error('Coordinate key input is unavailable on the selected backend');"
                    )
                code += "}else if(__tab.ax!=null){__source='ax';"
                if command == "click":
                    code += f"await __tab.ax.click({point_json});"
                elif command == "type":
                    code += (
                        f"await __tab.ax.click({point_json});"
                        f"await __tab.ax.typeText(null,{json.dumps(args['text'])});"
                    )
                else:
                    code += (
                        f"await __tab.ax.click({point_json});"
                        f"await __tab.ax.pressKey(null,{json.dumps(args['key'])});"
                    )
                code += "}else if(__tab.cua!=null){__source='cua';"
                if command == "click":
                    code += f"await __tab.cua.click({json.dumps(cua_point)});"
                elif command == "type":
                    code += (
                        f"await __tab.cua.click({json.dumps(cua_point)});"
                        f"await __tab.cua.type({json.dumps({'text': args['text']})});"
                    )
                else:
                    code += (
                        f"await __tab.cua.click({json.dumps(cua_point)});"
                        f"await __tab.cua.keypress({json.dumps({'keys': _key_sequence(str(args['key']))})});"
                    )
                code += (
                    "}else{throw new Error('Coordinate interaction requires AX or CUA on the selected backend');}"
                )
            else:
                raise RuntimeError("An interaction target is required")
            code += _output_js(
                "{tabId:__tab.id,title:await __tab.title(),url:await __tab.url(),"
                "action:" + json.dumps(command) + ",source:__source}"
            )
            return self._js(code, title=f"Browser {command}")

        if command == "upload":
            timeout_ms = int(args.get("timeoutMs") or 10000)
            files = args.get("files") or []
            code = (
                "try { await globalThis.__nexumReadDoc('file-uploads'); } catch {}"
                + _tab(args["tab"])
                + "if(__tab.playwright==null)throw new Error('File upload requires the Playwright surface on the selected backend');"
                + f"var __loc={_locator_js(args)};"
                + f"var __chooserPromise=__tab.playwright.waitForEvent('filechooser',{{timeoutMs:{timeout_ms}}});"
                + "var __chooserGuarded=__chooserPromise.then(value=>({ok:true,value}),error=>({ok:false,error:String(error?.message||error)}));"
                + "await __loc.click();"
                + "var __chooserSettled=await __chooserGuarded;"
                + "if (!__chooserSettled.ok) throw new Error(__chooserSettled.error);"
                + "var __chooser=__chooserSettled.value;"
                + "var __multiple=await __chooser.isMultiple();"
                + f"var __files={json.dumps(files)};"
                + "if (__files.length>1 && !__multiple) throw new Error('File chooser does not accept multiple files');"
                + f"await __chooser.setFiles(__files,{{timeoutMs:{timeout_ms}}});"
                + _output_js("{tabId:__tab.id,files:__files,multiple:__multiple}")
            )
            return self._js(code, title="Upload browser files", timeout_ms=timeout_ms + 5000)

        if command == "download":
            timeout_ms = int(args.get("timeoutMs") or 10000)
            code = (
                _tab(args["tab"])
                + "if(__tab.playwright==null)throw new Error('Download event handling requires the Playwright surface on the selected backend');"
                + f"var __loc={_locator_js(args)};"
                + f"var __downloadPromise=__tab.playwright.waitForEvent('download',{{timeoutMs:{timeout_ms}}});"
                + "var __downloadGuarded=__downloadPromise.then(value=>({ok:true,value}),error=>({ok:false,error:String(error?.message||error)}));"
                + "await __loc.click();"
                + "var __downloadSettled=await __downloadGuarded;"
                + "if (!__downloadSettled.ok) throw new Error(__downloadSettled.error);"
                + "var __download=__downloadSettled.value;"
                + "var __path=await __download.path();"
                + _output_js("{tabId:__tab.id,path:__path}")
            )
            return self._js(code, title="Download browser file", timeout_ms=timeout_ms + 5000)

        if command == "click-nav":
            timeout_ms = int(args.get("timeoutMs") or 10000)
            nav_options: dict[str, Any] = {"timeoutMs": timeout_ms}
            if args.get("url"):
                nav_options["url"] = args["url"]
            if args.get("waitUntil"):
                nav_options["waitUntil"] = args["waitUntil"]
            code = (
                _tab(args["tab"])
                + "if(__tab.playwright==null)throw new Error('Navigation-coupled clicking requires the Playwright surface on the selected backend');"
                + f"var __loc={_locator_js(args)};"
                + f"await __tab.playwright.expectNavigation(async()=>await __loc.click(),{json.dumps(nav_options)});"
                + (f"await __tab.playwright.waitForURL({json.dumps(args['url'])},{json.dumps({'timeoutMs': timeout_ms, 'waitUntil': args.get('waitUntil') or 'load'})});" if args.get("url") else "")
                + "await __tab.playwright.waitForTimeout(50);"
                + _output_js("{tabId:__tab.id,title:await __tab.title(),url:await __tab.url()}")
            )
            return self._js(code, title="Click and wait for navigation", timeout_ms=timeout_ms + 5000)

        if command == "scroll":
            dx = int(args["dx"])
            dy = int(args["dy"])
            point = _point(args)
            scroll_node_id = args.get("nodeId")
            code = _tab(args["tab"]) + "var __source=null;var __result=null;"
            if scroll_node_id is not None:
                code += (
                    "if(__tab.dom_cua==null)throw new Error('Node-targeted scrolling requires DOM-CUA on the selected backend');"
                    "__source='dom-cua';"
                    f"await __tab.dom_cua.scroll({json.dumps({'node_id': str(scroll_node_id), 'x': dx, 'y': dy})});"
                    "__result={x:null,y:null};"
                )
            elif point is not None:
                code += (
                    "if(__tab.cua==null)throw new Error('Point-targeted pixel scrolling requires CUA on the selected backend');"
                    "__source='cua';"
                    f"await __tab.cua.scroll({json.dumps({'x': point[0], 'y': point[1], 'scrollX': dx, 'scrollY': dy})});"
                    "__result={x:null,y:null};"
                )
            else:
                expression = (
                    f"window.scrollBy({dx},{dy}); "
                    "({x:window.scrollX,y:window.scrollY})"
                )
                code += (
                    "if(__tab.dom_cua!=null){__source='dom-cua';"
                    f"await __tab.dom_cua.scroll({json.dumps({'x': dx, 'y': dy})});"
                    "__result={x:null,y:null};"
                    "}else{"
                    "var __caps=await __tab.capabilities.list();"
                    "if(!__caps.some(x=>x.id==='cdp'))throw new Error('Pixel page scrolling requires DOM-CUA or the cdp capability on the selected backend');"
                    "__source='cdp';"
                    "var __cdp=await __tab.capabilities.get('cdp');await __cdp.documentation();"
                    "var __cdpResult=await __cdp.send('Runtime.evaluate',"
                    + json.dumps({"expression": expression, "returnByValue": True})
                    + ");__result=__cdpResult;}"
                )
            code += _output_js(
                "{tabId:__tab.id,source:__source,result:__result}"
            )
            return self._js(code, title="Scroll browser page")

        if command == "evaluate":
            code = _tab(args["tab"]) + (
                "var __caps=await __tab.capabilities.list();"
                "if(!__caps.some(x=>x.id==='cdp'))throw new Error('JavaScript evaluation requires the cdp capability on the selected backend');"
                "var __cdp=await __tab.capabilities.get('cdp');await __cdp.documentation();"
                "var __result=await __cdp.send('Runtime.evaluate',"
                + json.dumps({"expression": args["expression"], "awaitPromise": True, "returnByValue": True})
                + ");"
                + _output_js("{tabId:__tab.id,result:__result}")
            )
            return self._js(code, title="Evaluate page JavaScript")

        if command == "screenshot":
            return self._screenshot(args)

        if command == "dev-logs":
            code = (
                _tab(args["tab"])
                + "if(__tab.dev==null)throw new Error('Developer logs are unavailable on the selected backend');"
                + f"var __logs=await __tab.dev.logs({json.dumps(args.get('options') or {})});"
                + _output_js("{tabId:__tab.id,logs:__logs}")
            )
            return self._js(code, title="Read browser developer logs")

        if command == "history":
            history_args = {k: v for k, v in args.items() if v is not None}
            code = (
                f"if(typeof {b}.history!=='function')throw new Error('Browser history is unavailable on the selected backend');"
                f"var __history=await {b}.history({json.dumps(history_args)});"
                + _output_js("{items:__history}")
            )
            return self._js(code, title="Read browser history")

        if command == "capabilities":
            if args.get("tab"):
                code = _tab(args["tab"]) + "var __caps=await __tab.capabilities.list();" + _output_js("{scope:'tab',tabId:__tab.id,capabilities:__caps}")
            else:
                code = "var __caps=await globalThis.__nexumBrowser.capabilities.list();" + _output_js("{scope:'browser',browserId:globalThis.__nexumBrowser.browserId,capabilities:__caps}")
            return self._js(code, title="List browser capabilities")

        if command == "api-call":
            return self._api_call(args)

        raise RuntimeError(f"Unsupported browser command: {command}")

    def _observe(
        self,
        args: dict[str, Any],
        *,
        legacy_visible_dom: bool = False,
    ) -> dict[str, Any]:
        mode = str(args.get("mode") or "auto")
        code = (
            _tab(args["tab"])
            + f"var __mode={json.dumps(mode)};"
            + "var __source=null;var __kind=null;var __targetKind=null;var __observation=null;"
            + "if(__mode==='semantic'){"
            + "if(__tab.playwright==null)throw new Error('Playwright observation is unavailable on the selected backend');"
            + "__source='playwright';__kind='semantic-dom';__targetKind='locator';__observation=await __tab.playwright.domSnapshot();"
            + "}else if(__mode==='accessibility'){"
            + "if(typeof __tab.getAXState==='function'){"
            + "__source='ax';__kind='accessibility';__targetKind='ax-index';__observation=await __tab.getAXState({emit:false});"
            + "}else if(__tab.ax!=null){try{await globalThis.__nexumReadDoc('accessibility')}catch{};"
            + "__source='ax';__kind='accessibility';__targetKind='ax-index';__observation=await __tab.ax.get('state');"
            + "}else if(__tab.dom_cua!=null){__source='dom-cua';__kind='visible-dom';__targetKind='node-id';__observation=await __tab.dom_cua.get_visible_dom();"
            + "}else{throw new Error('Accessibility observation is unavailable on the selected backend');}"
            + "}else if(__mode==='visible'){"
            + "if(__tab.dom_cua!=null){__source='dom-cua';__kind='visible-dom';__targetKind='node-id';__observation=await __tab.dom_cua.get_visible_dom();"
            + "}else if(typeof __tab.getAXState==='function'){__source='ax';__kind='accessibility';__targetKind='ax-index';__observation=await __tab.getAXState({emit:false});"
            + "}else if(__tab.ax!=null){try{await globalThis.__nexumReadDoc('accessibility')}catch{};"
            + "__source='ax';__kind='accessibility';__targetKind='ax-index';__observation=await __tab.ax.get('state');"
            + "}else if(__tab.playwright!=null){__source='playwright';__kind='semantic-dom';__targetKind='locator';__observation=await __tab.playwright.domSnapshot();"
            + "}else{throw new Error('No supported observation surface is available on the selected backend');}"
            + "}else{"
            + "if(typeof __tab.getAXState==='function'){__source='ax';__kind='accessibility';__targetKind='ax-index';__observation=await __tab.getAXState({emit:false});"
            + "}else if(__tab.ax!=null){try{await globalThis.__nexumReadDoc('accessibility')}catch{};"
            + "__source='ax';__kind='accessibility';__targetKind='ax-index';__observation=await __tab.ax.get('state');"
            + "}else if(__tab.dom_cua!=null){__source='dom-cua';__kind='visible-dom';__targetKind='node-id';__observation=await __tab.dom_cua.get_visible_dom();"
            + "}else if(__tab.playwright!=null){__source='playwright';__kind='semantic-dom';__targetKind='locator';__observation=await __tab.playwright.domSnapshot();"
            + "}else{throw new Error('No supported observation surface is available on the selected backend');}"
            + "}"
        )
        if legacy_visible_dom:
            code += _output_js(
                "{tabId:__tab.id,title:await __tab.title(),url:await __tab.url(),"
                "source:__source,kind:__kind,targetKind:__targetKind,dom:__observation}"
            )
            return self._js(code, title="Inspect visible browser state")
        code += _output_js(
            "{tabId:__tab.id,title:await __tab.title(),url:await __tab.url(),"
            "mode:__mode,source:__source,kind:__kind,targetKind:__targetKind,"
            "observation:__observation}"
        )
        return self._js(code, title="Observe browser tab")

    def _output_status(self) -> str:
        return _output_js(
            "{available:true,selectedBrowserId:globalThis.__nexumBrowser.browserId,browsers:await globalThis.__nexumBrowserAgent.browsers.list(),handles:[...globalThis.__nexumBrowserHandles.keys()]}"
        )

    def _screenshot(self, args: dict[str, Any]) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if args.get("fullPage"):
            options["fullPage"] = True
        if args.get("clip") is not None:
            options["clip"] = args["clip"]
        code = (
            f"try {{ await globalThis.__nexumReadDoc('screenshots'); }} catch {{}}"
            + _tab(args["tab"])
            + f"var __image=await __tab.screenshot({json.dumps(options)}); await nodeRepl.emitImage(__image);"
            + _output_js("{tabId:__tab.id,title:await __tab.title(),url:await __tab.url(),byteLength:__image.byteLength}")
        )
        data, content = self.server.execute_js(code, title="Capture browser screenshot")
        images = save_images(content, "shot")
        if not images:
            raise RuntimeError("Browser screenshot did not return image bytes")
        data.update(images[0])
        if len(images) > 1:
            data["images"] = images
        return data

    def _api_call(self, args: dict[str, Any]) -> dict[str, Any]:
        surface = args["surface"]
        method = args["method"]
        call_args = args.get("args") or []
        await_result = not bool(args.get("noAwait"))
        result_mode = args.get("result") or "auto"
        setup: list[str] = []
        interface_name: str | None = None
        handle_id: str | None = None

        if surface == "agent":
            receiver = "globalThis.__nexumBrowserAgent"
            interface_name = "Agent"
        elif surface == "browsers-api":
            receiver = "globalThis.__nexumBrowserAgent.browsers"
            interface_name = "Browsers"
        elif surface == "docs-api":
            receiver = "globalThis.__nexumBrowserAgent.documentation"
            interface_name = "Documentation"
        elif surface == "browser":
            receiver = "globalThis.__nexumBrowser"
            interface_name = "Browser"
        elif surface == "tabs":
            receiver = "globalThis.__nexumBrowser.tabs"
            interface_name = "Tabs"
        elif surface == "user":
            receiver = "globalThis.__nexumBrowser.user"
            interface_name = "BrowserUser"
            setup.append(
                "if (globalThis.__nexumBrowser.user == null) "
                "throw new Error('Browser API surface user is unavailable on the selected backend');"
            )
        elif surface in {"tab", "playwright", "cua", "dom-cua", "ax", "content", "clipboard", "dev"}:
            if not args.get("tab"):
                raise RuntimeError(f"--tab is required for surface {surface}")
            setup.append(_tab(args["tab"]))
            receiver = {
                "tab": "__tab",
                "playwright": "__tab.playwright",
                "cua": "__tab.cua",
                "dom-cua": "__tab.dom_cua",
                "ax": "__tab.ax",
                "content": "__tab.content",
                "clipboard": "__tab.clipboard",
                "dev": "__tab.dev",
            }[surface]
            interface_name = {
                name: PUBLIC_API_SURFACES[name]
                for name in (
                    "tab",
                    "playwright",
                    "cua",
                    "dom-cua",
                    "ax",
                    "content",
                    "clipboard",
                    "dev",
                )
            }[surface]
            if surface != "tab":
                setup.append(f"if ({receiver} == null) throw new Error('Browser API surface {surface} is unavailable on the selected backend');")
            if surface == "ax":
                setup.append("try { await globalThis.__nexumReadDoc('accessibility'); } catch {}")
            if surface == "playwright" and method == "waitForEvent":
                setup.append("try { await globalThis.__nexumReadDoc('file-uploads'); } catch {}")
        elif surface in {"browser-capability", "tab-capability"}:
            if "." in method:
                raise RuntimeError("Optional capability methods must use one public member name at a time")
            capability = args.get("capability")
            if not capability:
                raise RuntimeError(f"--capability is required for surface {surface}")
            if surface == "tab-capability":
                if not args.get("tab"):
                    raise RuntimeError("--tab is required for tab-capability")
                setup.append(_tab(args["tab"]))
                setup.append(f"var __cap=await __tab.capabilities.get({json.dumps(capability)});")
            else:
                setup.append(f"var __cap=await globalThis.__nexumBrowser.capabilities.get({json.dumps(capability)});")
            setup.append("try { await __cap.documentation(); } catch {}")
            setup.append(
                f"if (!({json.dumps(method)} in __cap)) "
                f"throw new Error('Browser capability member is unavailable: {method}');"
            )
            receiver = "__cap"
        elif surface == "handle":
            handle_id = args.get("handle")
            if not handle_id:
                raise RuntimeError("--handle is required for surface handle")
            receiver = f"globalThis.__nexumBrowserHandles.get({json.dumps(handle_id)})"
        else:
            raise RuntimeError(f"Unsupported API surface: {surface}")

        prefix = "".join(setup)
        if method == "$release":
            if surface != "handle":
                raise RuntimeError("$release requires surface handle")
            code = prefix + f"if (!globalThis.__nexumBrowserHandles.has({json.dumps(handle_id)})) throw new Error('Unknown browser handle: '+{json.dumps(handle_id)}); globalThis.__nexumBrowserHandles.delete({json.dumps(handle_id)}); globalThis.__nexumBrowserHandleMeta.delete({json.dumps(handle_id)});" + _output_js("{released:true,handle:" + json.dumps(handle_id) + "}")
            return self._js(code, title="Release browser handle")

        if method == "$value":
            if surface != "handle":
                raise RuntimeError("$value requires surface handle")
            code = prefix + f"var __info=globalThis.__nexumHandleInfo({json.dumps(handle_id)});" + _output_js("{result:__info}")
            return self._js(code, title="Inspect browser handle")

        if method == "$await":
            if surface != "handle":
                raise RuntimeError("$await requires surface handle")
            if result_mode == "image":
                raise RuntimeError("Use $await first, then $image on the returned binary handle")
            code = prefix + f"var __result=await globalThis.__nexumAwaitHandle({json.dumps(handle_id)});" + _output_js("{result:__result}")
            return self._js(code, title="Await browser handle", timeout_ms=int(args.get("timeoutMs") or 30000))

        if method == "$image":
            if surface != "handle":
                raise RuntimeError("$image requires surface handle")
            code = prefix + f"if (!globalThis.__nexumBrowserHandles.has({json.dumps(handle_id)})) throw new Error('Unknown browser handle: '+{json.dumps(handle_id)}); var __raw={receiver}; if (!(__raw instanceof Uint8Array)) throw new Error('Handle is not Uint8Array'); await nodeRepl.emitImage(__raw);" + _output_js("{handle:" + json.dumps(handle_id) + ",byteLength:__raw.byteLength}")
            data, content = self.server.execute_js(code, title="Read browser image handle")
            images = save_images(content, "api")
            if not images:
                raise RuntimeError("Browser handle did not emit image bytes")
            data.update(images[0])
            return data

        if result_mode == "image":
            if not await_result:
                raise RuntimeError("--result image cannot be combined with --no-await")
            if surface == "handle":
                image_expr = f"globalThis.__nexumCallHandleRaw({json.dumps(handle_id)},{json.dumps(method)},{json.dumps(call_args)})"
            else:
                image_expr = f"globalThis.__nexumCallRaw({receiver},{json.dumps(interface_name) if interface_name else 'null'},{json.dumps(method)},{json.dumps(call_args)})"
            code = prefix + f"var __raw=await ({image_expr}); if (!(__raw instanceof Uint8Array)) throw new Error('API result is not Uint8Array'); await nodeRepl.emitImage(__raw);" + _output_js("{byteLength:__raw.byteLength}")
            data, content = self.server.execute_js(code, title=f"Browser API {method}", timeout_ms=int(args.get("timeoutMs") or 30000))
            images = save_images(content, "api")
            if not images:
                raise RuntimeError("Browser API did not emit image bytes")
            data.update(images[0])
            return data

        if surface == "handle":
            raw_expr = f"globalThis.__nexumCallHandle({json.dumps(handle_id)},{json.dumps(method)},{json.dumps(call_args)},{str(await_result).lower()})"
        else:
            raw_expr = f"globalThis.__nexumCall({receiver},{json.dumps(interface_name) if interface_name else 'null'},{json.dumps(method)},{json.dumps(call_args)},{str(await_result).lower()})"
        code = prefix + f"var __result=await ({raw_expr});" + _output_js("{result:__result}")
        return self._js(code, title=f"Browser API {method}", timeout_ms=int(args.get("timeoutMs") or 30000))
