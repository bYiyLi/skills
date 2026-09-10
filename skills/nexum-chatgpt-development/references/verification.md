# Verification and review loop

Use this for implementation, repair, acceptance assessment, and repository
review. Verification collects evidence for behavior; review checks correctness,
design consistency, and omissions beyond the exercised cases. Neither proves
the absence of every possible defect.

## Establish the verification target

Before editing, identify the acceptance criteria, affected interfaces, repository
gates, and current staged/unstaged changes. Choose commands from inspected
manifests, tests, and CI, not framework guesses. Run a relevant baseline when a
regression, environment uncertainty, or existing failure would make attribution
ambiguous. Preserve its command, scope, outcome, and source state. Missing
baseline evidence means the origin of a later failure is unknown.

For review-only work, inspect without patching code, docs, snapshots, or logs.
Check commands for auto-fix, fixture mutation, external writes, and production
access before running them. Use check mode or an isolated permitted test
workspace; if the necessary check cannot respect scope, report it unverified.
Do not turn "review" into permission to repair findings.

## Run the feedback loop

The following steps govern implementation. In review-only mode, collect scoped
evidence and apply the review criteria, then return findings without steps that
implement or repair the subject.

1. Implement a coherent change within the authorized scope.
2. Run the smallest verification that can detect that change's expected failure.
   Inspect terminal exit status and actual output, including collected tests,
   skipped cases, warnings, and generated artifacts.
3. Resolve or classify a failure before expanding dependent implementation.
4. Review the change against design, acceptance, and failure paths. Fix findings
   within implementation authority, then rerun checks invalidated by the fix.
5. Expand to affected subsystem/integration checks and required task-level gates.
   Continue until the completion gate below is supported, or a real blocker is
   identified. Repeat for changed evidence or unresolved findings, not to reach
   an arbitrary number of review rounds.

| Changed surface | Evidence to consider; repository requirements still govern |
| --- | --- |
| Local behavior | Targeted tests, boundary/error cases, regression reproduction |
| Module or cross-module state | Module/integration tests, failure cleanup and state invariants |
| Public contract or persistent data | Compatibility/migration tests and versioned fixtures |
| Declared scale/resource requirement | Reproducible workload, measured limit, environment |
| Documentation or templates | Actual paths/links, example consistency, placeholder instantiation |
| Skill or prompt | Format/resource validation and closed-contract scenarios; observed model behavior only when separately tested |

The matrix is not a requirement to run every category for every change. A small
verification radius never waives a repository-mandated final gate.

## Classify failures without hiding them

| Observed cause | Required response |
| --- | --- |
| Implementation defect | Repair it and add/adjust a regression test that detects it |
| Incorrect test expectation | Confirm the contract first, then fix the test; do not weaken assertions just to pass |
| Missing or conflicting design | Apply the design-gap path before choosing behavior |
| Environment/tool failure | Diagnose from outputs; use an authorized documented alternative or mark the check blocked |
| Demonstrably pre-existing unrelated defect | Preserve it, report the evidence and scope; do not silently expand the task |
| Unknown or flaky failure | Investigate and report uncertainty; one successful retry does not erase a reproduced failure |

A pre-existing failure still blocks completion when it prevents current
acceptance or a mandatory gate. A command that collected no expected tests,
skipped required cases, or has not terminated is not a passing verification.
Do not disable gates or redefine acceptance to make the task appear complete.

For a repeated failure, inspect new evidence and change the diagnostic approach.
Do not retry an unchanged mutating command with an uncertain result. On process
timeout or lost session, inspect current processes and resulting files before
resuming. Respect execution/resource limits and report the blocked check rather
than claiming background completion.

## Review more than the happy path

Review changed code and its affected callers against the contract. Inspect
negative/boundary behavior, failure cleanup, tests' ability to detect the bug,
module ownership, avoidable complexity, and documentation consistency. Include
security, concurrency, compatibility, or performance when the changed surface
can affect them; do not append an unrelated universal audit.

For each actionable finding, identify severity/impact, path and location,
reachable failure, evidence, and the smallest correction. Distinguish observed
defects from hypotheses and optional polish. A review-only result is the findings
and coverage limits; an implementation result additionally resolves findings
that affect its contract, acceptance, or required quality gates.

## Close against fresh evidence

Before declaring implementation complete, map each acceptance criterion to a
concrete check/result, confirm required gates, and inspect final Git status plus
the full staged/unstaged/task-owned untracked diff. Include documentation,
fixtures, generated files, and accidental changes in that inspection. Record
what was actually reviewed and any non-blocking limitations.

Bind evidence to the checked revision or worktree state. After a later change,
rerun the checks whose inputs or behavior it affects; an old successful run is
not evidence for changed code. Documentation-only bookkeeping does not require
repeating an unaffected full code suite, but does require its own final checks.

Use `passed`, `failed`, `blocked`, or `not run` accurately for individual checks.
An unmet acceptance criterion or missing mandatory result keeps the task partial
or blocked. Finish after the requested acceptance and review boundary is met;
report "no remaining task-affecting findings in the reviewed scope", not "zero
bugs" or a guarantee about untested behavior.
