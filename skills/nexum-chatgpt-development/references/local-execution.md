# Nexum local execution

Use live Nexum tool schemas; this guide does not add tools or expand their
accepted arguments. Confirm the correct Nexum environment before selecting IDs.

## Resolve and open the actual target

Discover tools, call `project.list`, and match the requested Agent and absolute
repository from current results and the user's workspace map. Do not infer a
path from a product name or silently substitute another OS/Agent. If the intended
Agent is offline, report that boundary instead of transferring its facts to an
available machine. Ask only when inspected sources leave materially different
targets plausible. Open each authorized repository separately.

Call `project.open` before Files or Process work. Use its returned `contextId`
for that work, not `project.id`; copy all opaque IDs exactly. On a new user turn
continuing the project, refresh with the same Agent, absolute path and current
context ID. On an expired/invalid context, inspect the actual response and
rediscover/open only as its contract permits; do not fabricate replacement IDs.
Read applicable personal, project and nested instructions before dependent work.

To create a project directory, first open an authorized existing parent, inspect
the destination and preserve existing contents, then open the new repository.
An `authorization_required` response needs its actual approval flow. Do not
use another command or parent context to bypass denial. Tool availability never
supplies missing user authority.

## Read and change files in their real location

Use Project-relative paths or canonical paths explicitly accepted by Files,
including discovered Instruction/Skill roots. Agent paths are not sandbox paths.
Locate unknown text with `files.search` (literal text, not regex); read known
files with `files.read`. Follow the returned single-use cursor while `hasMore`
for any required complete instruction. Reuse exact file revisions to guard
`files.apply_patch` updates; on conflict reread before reconciling.

A multi-file patch can partially succeed. After an error, timeout or missing
response, inspect the affected files/revisions before any retry. Preserve known
successful writes and concurrent user edits; do not replay the entire patch on
an assumption of rollback.

For requested artifacts, use supported download/preview tools. A download URL
is a transfer channel, not proof the host received bytes. Confirm the actual
host file before reporting a sandbox attachment. Use upload/import only with
the supported new-target and host-file contracts; do not encode arbitrary file
contents as invented file references.

## Run and finish processes

Choose direct `command` plus `args`, or `shellCommand`, as the current schema
requires. Resolve executable, platform, working directory and prerequisites
from the Agent; prefer direct arguments when shell syntax is unnecessary.
Project-relative `cwd` and explicit environment overrides are not evidence that
a different shell, PATH or runtime exists. Diagnose missing commands from actual
outputs. Use `tty` only for a terminal-dependent program.

A process may finish inline or return a `processId`. Poll that session with the
latest cursor until terminal status; inspect exit status and actual output.
Use process discovery for lost sessions and inspect resulting files before
resuming an interrupted mutation. Do not use `project.open` as process polling,
treat tool acceptance as command success, or promise completion after the reply.

Signal/cancel only the task's processes through their supported operations and
check terminal state afterward. An accepted signal need not mean termination.
Preserve unrelated services and user processes. A timeout or session loss makes
side effects uncertain, not automatically failed or rolled back.

Keep environment diagnoses scoped: a successful local test proves its actual
Agent/run, not Windows, another repository, browser operation, CI or deployment.
