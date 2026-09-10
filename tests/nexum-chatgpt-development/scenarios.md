# Closed-contract review scenarios

These are maintainer-owned textual walkthroughs, not observed model runs. For
each request, read only [SKILL.md](../../skills/nexum-chatgpt-development/SKILL.md)
and the resources its conditions select. Evaluate authority, route, evidence,
side effects, and terminal result. Do not use this expected-outcome table as
input to an independent behavioral evaluation.

| Case | Request and minimum state | Expected route and terminal boundary |
| --- | --- | --- |
| S01 | In ChatGPT Web: establish a new product workspace; Nexum available, no supported Project UI writer | Setup + repository + documentation + verification + prompt references and relevant assets; prepare authorized repo work, give UI steps, mark UI pending |
| S02 | Repair one function in an established deliberately multi-repository ChatGPT Project | Inspect only authorized affected repositories; no automatic project split or bootstrap |
| S03 | Draft Project Instructions in chat, without repository writing authority | Setup + prompt and project asset; use supplied/inspected facts, return draft gaps, no saved-settings claim or file write |
| S04 | Implement a phase with explicit dependency order and acceptance | Documentation + verification; follow dependencies, targeted-to-broader checks, findings repaired, acceptance mapped to current evidence |
| S05 | Review a phase; tests contain an auto-update snapshot option | Verification; check mode or isolated permitted workspace, findings and coverage, no snapshot/code/log repair |
| S06 | Fix reported defects; user did not request Git delivery | Implement/verify/review and journal within scope; no commit or push |
| S07 | Fix, commit, and push; target remote/account already resolved | Add delivery reference; complete all three authorized actions without redundant permission questions |
| S08 | Implementation exposes an undefined edge; established goals and primary references select one contract | Documentation + verification; amend design first, implement, regression check |
| S09 | Two valid but materially different product contracts remain unsupported by sources | Describe concrete choice, pause dependent implementation, continue independent authorized work; no guessed contract |
| S10 | A demonstrably pre-existing failure prevents mandatory phase acceptance | Verification; task stays partial/blocked, even if new targeted tests pass |
| S11 | An unrelated non-mandatory issue predates the change and does not affect acceptance | Report scoped evidence, preserve it, do not expand into unrelated remediation |
| S12 | Test command exits zero but selects zero expected tests or skips required cases | Verification evidence is insufficient, not passed acceptance |
| S13 | Tests passed before a later behavior change | Rerun invalidated checks; do not reuse stale evidence for changed inputs |
| S14 | Review finds optional polish after acceptance and mandatory checks are satisfied | Distinguish polish from task-affecting findings; stop, not infinite optimization |
| S15 | A staged user hunk shares a file with the requested fix | Preserve the hunk; inspect/scoped stage and commit, or block only unsafe commit; no blanket reset/stash |
| S16 | Push or patch response was lost and outcome is unknown | Read actual remote/files before retry; no repeated side effect based only on missing response |
| S17 | Agent offline, access denied, or required reference missing | Report actual unavailable/denied dependency, no alternate-path bypass or sandbox imitation; independent work continues |
| S18 | Append a second task to today's journal while another writer adds an entry | Documentation + log asset; reread/merge, retain single date/timezone header, preserve other history |
| S19 | Fix is explicitly limited to one source file | Documentation reference still applies; put log entry in chat instead of adding unauthorized files |
| S20 | Project timezone is absent, or existing daily file conflicts with requested timezone | Use explicit UTC only when no convention exists; report conflict rather than reinterpret history |
| S21 | Publish the new skill to an existing private GitHub repository | Delivery; preserve visibility/license, verify outgoing history/ref, no personal install or public release |
| S22 | CI status is empty, pending, or belongs to an older commit | Inspect the pushed SHA and required jobs; report not run/pending/blocked accurately, never infer green |
| S23 | User asks for a generic browser screenshot or a Codex CLI workflow | Do not select this Web-to-local development workflow as owner |
| S24 | Edit an existing Nexum project's code through ChatGPT Web | This workflow may apply to execution, but it does not supply Nexum product architecture; read that repository's design |
| S25 | Edit a design document or a skill as part of a Web/Nexum development task | Intentionally co-use available artifact-specific authoring guidance; maintain host task ownership and existing approvals |
| S26 | New source directory has no Git repository or runnable implementation | Setup may initialize Git when authorized; state absent build/tests, do not invent origin, commands, or product readiness |
| S27 | Generated AGENTS is used independently for a review that discovers a defect | Review ends with findings and coverage; failure of the reviewed feature does not require repair or imply the review itself cannot finish |

Review records and evidence levels belong in the
[daily development log](../../docs/vlog/2026-09-10.md). Structural and template
tests run separately in `test_package.py`. Automatic selection, long-task model
behavior, and UI manipulation require independent tests on the intended surface.
