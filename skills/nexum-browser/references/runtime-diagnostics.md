# Browser Runtime diagnostics

Read for startup, transport, proxy, sandbox or doctor investigation, not ordinary
browsing. The installed launch contract and implementation determine behavior.

## Runtime contract

nexum-browser discovers Codex's generated
unified-computer-use/<version>/.mcp.json and consumes its cua_repl command,
arguments, environment, forwarded environment variables, enabled tools, Node
REPL path, and module paths.

The bridge deliberately overrides:

~~~
NODE_REPL_JS_BANNER=""
~~~

Do not initialize CUA in the Node startup banner. Browser authenticated policy
initialization requires a real js tool-call context.

On every platform, the first run in a fresh JS context prepends this in the
**same js tool call** as the requested code:

~~~js
await import("@oai/cua/tinyskyAlt");
~~~

The bridge owns that request bootstrap. Do not add a separate public bootstrap
command. The installed Browser service starts request-header policy
initialization asynchronously. For a newly started cua_repl process, the bridge
therefore creates one temporary blank controlled tab through the public Browser
API and immediately closes it before the user's JavaScript. This is the
smallest public check that proves the controlled-tab path is actually ready; a
tab listing alone can succeed while request-header policy initialization is
still incomplete. If that preflight returns the Runtime's exact temporary
request-header-policy initialization error, the bridge discards that cua_repl
process and retries a fresh startup, for at most five total attempts. The
preflight throws before user JavaScript begins, so this recovery never replays
user JavaScript.

Mac and Windows use the same direct cua_repl transport. Do not route Windows
through Codex model turns or an app-server Browser adapter.

On Windows, caller-provided `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and
`NO_PROXY` settings are preserved through the persistent Scheduled Task broker.
If the caller did not explicitly provide a proxy for HTTP or HTTPS, the bridge
uses the current user's WinINET proxy only in the Runtime child environment. It
also maps NO_PROXY-compatible entries from the current user's WinINET bypass
list into the Runtime child's `NO_PROXY` when the caller did not explicitly
provide `NO_PROXY`. WinINET-only patterns that cannot keep the same meaning in
`NO_PROXY` are not widened; doctor reports the bypass mapping as partial or
unsupported instead. It does not change the user's system proxy.

## Doctor

Run browser doctor for setup failures, transport failures, or explicit health
checks. It verifies the real installed environment rather than repairing it.

It checks:

- Codex installation and the generated unified-computer-use launch contract;
- cua_repl, Node, node_repl, Browser API manifest, MCP initialize, tools list,
  js, js_reset, post-reset bootstrap, and turn_ended;
- Browser plugin presence, Chrome installation/running state, extension state,
  native messaging host, and Browser Runtime connectivity;
- effective proxy sources without printing proxy URLs; on Windows, WinINET is
  used only as the fallback described above;
- on Windows, whether codex sandbox can execute the Runtime node.exe.

On Windows, native messaging host registration is verified through the Registry
without depending on localized `reg.exe` default-value labels. When the Windows
sandbox execution probe fails because access is denied, doctor reports the
Runtime path, resolved Junction target, Codex sandbox group evidence, relevant
ACL output, and whether an ACL mismatch is suspected. It must not modify system
ACLs. Network and proxy failures do not trigger ACL diagnostics.

Use the diagnostic evidence to repair the actual environment outside this Skill;
do not add alternate product architecture to mask a machine-specific
installation problem.
