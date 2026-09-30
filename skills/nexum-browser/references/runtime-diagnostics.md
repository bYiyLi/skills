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

On every platform, the first run in a fresh JS context performs a bridge-owned
readiness js call before the requested code. That call imports:

~~~js
await import("@oai/cua/tinyskyAlt");
~~~

The user JavaScript runs only after that bridge call completes, so it cannot
forge the bridge's readiness result and bootstrap recovery never replays user
JavaScript. Do not add a separate public bootstrap command. The installed Browser
service starts request-header policy
initialization asynchronously. For a newly started cua_repl process, when the
Runtime advertises browsers, the bridge probes them through the public Browser
API, preferring the extension path but continuing to other advertised browsers
when a probe fails. It creates and immediately closes one temporary blank tab on
the first usable browser before the user's JavaScript. That preflight checks the
controlled-tab path; a tab listing alone can succeed while request-header policy
initialization is still incomplete. Fallback to another advertised browser occurs
only after any created probe tab has been confirmed closed; an unconfirmed cleanup
failure stops readiness before user JavaScript. If the browser list is empty, no controlled-
tab readiness has been established; successful JavaScript establishes only the
bootstrap/tool path, and tab-dependent operations remain unverified. Readiness is
recorded from the successful probe itself, independently of whether the user's
JavaScript later succeeds. If all advertised browser probes fail and a failure
contains the Runtime's exact temporary
request-header-policy initialization error, the bridge discards that cua_repl
process and retries a fresh startup, for at most five total attempts.

Each non-confirmation execution segment has a bounded broker completion budget.
When readiness recovery is still needed, that budget includes the declared
startup timeout, one possible tool-list refresh, all supported preflight attempts,
and the one user JavaScript call. After readiness it still includes one possible
tool-list refresh, the
requested JavaScript timeout and transport grace. Runtime confirmation pauses the
deadline and accepting confirmation starts a fresh execution segment using the
same cold-safe bound if readiness is still pending.
The CLI uses a cold-start-safe wait budget that also covers initial MCP
initialization and tool discovery, regardless of a pre-lock status sample.
Reset and stop waits likewise include a possible tool-list refresh plus their
Runtime tool-call timeout.
If a request times out, loses its connection, or returns an invalid/empty response
after dispatch, or cua_repl never reports completion, return
`run_outcome_unknown`; do not replay the JavaScript before inspecting current
browser state because prior side effects may have succeeded.

The same unknown-outcome rule applies when a dispatched MCP `tools/call` loses
its Runtime response or returns no valid typed ToolResult. Tool-list change
notifications received during refresh remain pending for the next call instead
of being cleared by the refresh that was already in flight. A confirmation continuation
is bound to both its operation ID and elicitation ID; a stale continuation must
not accept or cancel a later confirmation. If Runtime withdraws a pending
confirmation before continuation, the broker discards that Runtime and returns
`run_outcome_unknown` instead of remaining permanently busy.

Mac and Windows use the same direct cua_repl transport. Do not route Windows
through Codex model turns or an app-server Browser adapter.

On Windows, caller-provided `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and
`NO_PROXY` settings are captured when the persistent Scheduled Task broker is
started and preserved for that broker lifecycle.
If the caller did not explicitly provide a proxy for HTTP or HTTPS, the bridge
uses the current user's WinINET proxy only in the Runtime child environment. It
also maps semantically compatible WinINET bypass entries into the Runtime
child's `NO_PROXY` when the caller did not explicitly provide `NO_PROXY`.
WinINET-only patterns are not widened: the bridge may retain only a safe
loopback subset such as `127.0.0.1` from `127.*`; `<local>` remains partial
because `NO_PROXY` cannot express all simple hostnames. The `<-loopback>`
rule is applied in order so later subtraction removes earlier mapped loopback
entries. Doctor reports incomplete mappings as partial or unsupported. An explicit
`NO_PROXY`, including an empty value, always wins. The bridge does not change
the user's system proxy. If the caller changes proxy environment values while
the broker is already running, stop that broker and let the next authorized run
start a fresh one before claiming the new proxy settings are active.
If the Scheduled Task still appears to be running but broker state is missing or
unreadable, the bridge refuses to replace or force-stop it because an operation
outcome may be unknown.
Likewise, a responding broker with an incompatible protocol is never replaced
implicitly by `browser run`; resolve any active operation and stop it explicitly
before starting the current broker.
Reset reports `alreadyReset` only when stopped state is positively established;
uncertain task/state or an incompatible responding broker returns
`reset_state_unknown`.

## Doctor

Run browser doctor for Chrome-extension setup failures, shared Runtime transport
failures, or explicit Chrome-path health checks. It verifies rather than repairs
the environment. For an IAB-only session, use observed Runtime state for IAB
health and treat Chrome-specific doctor failures as separate diagnostics.

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
