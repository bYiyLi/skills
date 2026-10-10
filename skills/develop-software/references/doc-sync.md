# Documentation impact and synchronization

Use for one software change affecting several sources, or a requested inventory
and cleanup of related documents. First determine the requested result: impact
analysis (read-only), synchronization plan (write only if requested), or actual
synchronization. The first two do not authorize changes to the target documents.

## Discover affected facts

Inspect the task's baseline, repository rules, document entrypoints, generators,
current sources and references. Choose candidates from observed change and
inventory, not from a list of document types every project supposedly needs.

| Changed fact | Candidate owner and comparison |
| --- | --- |
| Product promise, actors, constraints or acceptance | Requirements: does the accepted product answer change? |
| Structure/interface/data/runtime or significant choice | Design/ADR: does the implementation contract change? |
| Work, dependency, deliverable or completion evidence | Plan: do work, inputs, criteria and state still correspond? |
| Learning/task/operation path, risk or impact | Guide: do prerequisites, steps, permissions, impact/risk notices or recovery change, even with unchanged commands? |
| API/CLI/configuration/error/compatibility surface | Reference: do published interface facts change? |
| Duplicate/stale/broken/state-conflicting documents | Existing sources: which authority determines the intended relationship? |

An API change need not change every requirement. Compare each document's owned
facts; unknown is not no-change. If the target repository is unreadable, analyze
only supplied inventory and mark collection completeness unverified.

## Decide actions and their evidence

For each candidate and applicable change dimension, choose an action and record
its source/baseline, reason, dependency/authority, verification and any blocker.
Use multiple entries when one document needs independent actions. A compact
explanation may suffice; use a matrix when it helps the requested result.

| Action | Meaning and required distinction |
| --- | --- |
| create / update | Missing needed reader result / existing owning content changed |
| update-metadata | Non-state fields allowed by the target contract; exact before/after values |
| change-state | Existing general lifecycle state; real entry condition and authority |
| move | Current source changes location; old/new paths and consumers |
| deprecate | Retained but no longer current; actual declaration and replacement source |
| archive | Move non-current material to its historical location under retention rules |
| delete | Specific authorized target; checked references, retention and recovery |
| no-change | Evidence rules out changes in all applicable dimensions |
| unresolved | A particular decision lacks source, target contract or canonical ownership |

No-change is incompatible with another action for the same document. Unresolved
can coexist with an independent decided action, identifying the unresolved
dimension. Missing execution permission is not uncertainty about a known action.
Use existing state expressions; plain deprecation text may suffice where no
metadata contract exists. Never add a lifecycle framework just for this change.

## Execute the requested scope

Order by actual inputs, state and side effects, not an unconditional sequence
of document types. File/status or purely mechanical edits use doc-management.
Meaning-changing content also uses documentation and the matching requirements/
design/planning/usage reference from the main entrypoint before writing it.
Analysis and lifecycle-only operations
do not require every type's body contract. Preserve unrelated content and history.

For a saved synchronization plan without a suitable repository template, optionally
adapt [../assets/doc-sync-plan-template.md.tmpl](../assets/doc-sync-plan-template.md.tmpl)
from the inspected change, inventory, action decisions and verification state.
A plan is not proof its actions have executed. Preserve unresolved choices;
a missing approval pauses only the action that requires it.

After a failed or uncertain action inspect its actual state before retrying.
Verify content/links, metadata/state before-and-after values, moves at both paths,
archive history, deprecation declaration, and authorized deletion/reference
cleanup as applicable. An analysis covers each candidate with a decision or
specific gap; a plan adds order, prerequisites and checks; actual synchronization
needs observed results. Report partial combinations without hiding independent
success or claiming blocked actions complete.
