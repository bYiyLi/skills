# Advanced Browser Runtime access

Read this reference only when the simple `nexum-browser` commands cannot express the required browser operation.

The CLI exposes the installed OpenAI Browser Runtime in two layers: a stable
intent-level command set for normal browser work and a generic bridge for the
installed public Runtime API. Prefer the stable commands first. Do not use
`api-call` merely because it is more general.

The public API schema and the selected backend's active surfaces are different
things. Use `api-list` / `api-type` for the installed schema, `surfaces`
for actual tab surfaces, and `capabilities` for advertised optional
capabilities. A schema member can exist while the selected backend disables its
surface.

For page observation, prefer `observe --mode auto`. It returns the Runtime
surface used in `source` and the compatible stable-command target form in
`targetKind`. Use `snapshot` when the task specifically needs the Playwright
semantic DOM. `visible-dom` is retained for compatibility and adapts when
legacy DOM CUA is unavailable.

## Discover the public API before calling it

Use `browser api-list` to list installed Runtime interfaces. Narrow the result before making an advanced call:

```text
browser api-list --interface PlaywrightLocator
browser api-list --interface PlaywrightLocator --member selectOption
browser api-list --interface AXAPI --member get
browser api-type --name SelectOptionInput
```

Treat the installed manifest as the available public interface description for this Runtime version. Runtime backends and optional capabilities may still reject an otherwise documented member.

On the macOS direct-CUA backend the manifest comes from the Browser environment
selected by the active OpenAI `cua_repl` launch contract (for example
`environment-docs/codex-app/api.json`). Do not substitute a cached schema from a
different Runtime environment.

Use `browser api-coverage` when validating a Runtime upgrade or this Skill.
`complete: true` means every installed public interface is reachable through a
direct bridge root or through a typed object returned by another public member,
and every directly-declared callback shape is representable by the bridge. The
report lists callback members and any unsupported callback shapes separately.
It is a bridge-coverage check, not a backend-support check.

Before using a backend-specific tab API, inspect the live surfaces:

```text
browser surfaces --tab <tabId>
```

For example, a Chrome extension backend may expose `ax` while disabling
`domCua` and `cua`. In that state use the accessibility surface rather than
assuming that `DomCUAAPI` is callable merely because it appears in `api-list`.

## Advanced API surfaces

`browser api-call` accepts these surfaces:

- `agent`, `browsers-api`, `docs-api`
- `browser`, `tabs`, `user`
- `tab`, `playwright`, `cua`, `dom-cua`, `ax`, `content`, `clipboard`, `dev`
- `browser-capability`, `tab-capability`
- `handle`

The `agent`, `browser`, and `tab` surfaces also accept dot-separated
public member paths. For example,
`--surface tab --method playwright.waitForLoadState` reaches the same public
API as the `playwright` convenience surface. These paths and handle calls are
validated against the installed `api.json` public interface contract; guessed
private or implementation-only members are rejected even if they exist on the
underlying JavaScript object.

The bridge roots plus typed handles cover the full installed public interface
graph. Interfaces returned from a root call, including Playwright locators,
frame locators, dialogs, downloads, and file choosers, remain available through
the `handle` surface rather than being flattened into a smaller wrapper API.

Pass method arguments as a JSON array with `--args-json`. Example:

```text
browser api-call --tab <tabId> --surface playwright --method waitForLoadState --args-json '[{"state":"domcontentloaded"}]'
```

For optional capabilities, discover first:

```text
browser capabilities
browser capabilities --tab <tabId>
```

Then call the advertised capability. The adapter reads the capability's Runtime documentation before invoking it:

```text
browser api-call --tab <tabId> --surface tab-capability --capability cdp --method send --args-json '["Runtime.evaluate",{"expression":"document.title","returnByValue":true}]'
```

Do not treat `cdp` as unrestricted Chrome DevTools access. The Browser Runtime may reject CDP methods that are not allowed by the current backend.

## Handles and chaining

Runtime objects such as Playwright locators, frame locators, dialogs, downloads,
file choosers, and other class instances are returned as opaque handles such as
`g1:h_1`. The generation prefix changes when the persistent JavaScript Runtime
is reset, so an older-generation handle must be treated as stale rather than
retried. When the Runtime declaration identifies the result interface, the
handle also carries that public interface so subsequent calls can be checked
against the installed API contract.

Call a method on a returned handle with:

```text
browser api-call --surface handle --handle <returnedHandle> --method click --args-json '[{}]'
```

When an API argument itself must be another Runtime object, pass a handle reference in JSON:

```json
{"$handle":"<returnedHandle>"}
```

This enables operations such as locator `and` / `or` without exposing arbitrary Node.js execution.

When a documented public method requires an action callback, pass a public call
descriptor as `{"$call": ...}`. The adapter turns only that descriptor into an
async callback and validates the nested call against the same public API
contract. It does not evaluate arbitrary Node.js callback source.

For example, `PlaywrightAPI.expectNavigation` can wrap a click on a locator
handle:

```json
[
  {
    "$call": {
      "surface": "handle",
      "handle": "<returnedHandle>",
      "method": "click",
      "args": []
    }
  },
  {
    "url": "http://127.0.0.1:8766/page2.html",
    "waitUntil": "load",
    "timeoutMs": 10000
  }
]
```

The nested descriptor may target any direct public surface listed by
`api-call --help`, an advertised `browser-capability` or
`tab-capability`, or a typed `handle`. Capability descriptors must name the
capability and one documented member; the adapter verifies that the capability
is currently advertised before invoking it. Backend-disabled surfaces still
fail normally.

Use `$value` to inspect a handle's safe metadata, `$release` when it is no longer needed, and `$image` only for a handle representing `Uint8Array` image bytes. The adapter does not expose arbitrary object internals through handle inspection.

## Event and callback flows

Use the dedicated flows when Browser Runtime requires the event wait and triggering action to be submitted together:

```text
browser upload --tab <tabId> --selector 'input[type="file"]' --file /absolute/path/file.txt
browser download --tab <tabId> --role link --name Download
browser click-nav --tab <tabId> --role link --name Next --wait-until load
```

These wrap `waitForEvent` / `expectNavigation` and the triggering action in one Browser Runtime submission. Prefer them for uploads, downloads, and navigation-coupled clicks.

If a Chromium `upload` reaches the file chooser but `setFiles` is denied, read the current Runtime guidance with `browser docs --name chrome-file-upload-troubleshooting` and follow that supported setup path. Do not bypass the browser extension's file-access restriction.

For other asynchronous Runtime calls, `api-call --no-await` stores the returned Promise as a guarded handle. Resolve it with `$await`:

```text
browser api-call --tab <tabId> --surface playwright --method waitForTimeout --args-json '[500]' --no-await
browser api-call --surface handle --handle <promiseHandle> --method '$await'
```

The resolved result may itself be a handle. Continue through the `handle` surface. For file uploads, use only files the user authorized for upload.

## Image-returning advanced methods

When the selected API method directly returns `Uint8Array` image bytes, add `--result image`. The adapter writes the image into this Skill's `.runtime/screenshots` directory and returns the local path.

For a nested binary value returned inside another object, the value is represented as a binary handle. Use the handle surface with `$image` to materialize it.

## Browser selection

Normal work uses the Runtime default. When the user's request requires a specific browser surface, select it explicitly:

```text
browser browsers
browser select --browser chrome
browser select --browser edge
browser select --browser iab
browser select --browser extension
browser select --url https://example.com/
```

Do not silently substitute another browser when the user explicitly named a browser family.

## Runtime confirmations

An advanced capability such as raw CDP can cause the Browser Runtime to pause
the current call and return `confirmation_required` through the stable CLI.
Apply the main Skill's authorization rules to the exact Runtime request and
resume that same operation; do not rerun the original `api-call`, because its
result may be unknown or its side effects may already have started.

## Boundary

`api-call` can invoke documented Browser Runtime members and advertised optional capabilities, but it does not expose arbitrary Node REPL JavaScript, Codex turns, or private Browser service RPCs. A Runtime-side denial is a real boundary; do not work around it with private or undocumented Browser internals.
