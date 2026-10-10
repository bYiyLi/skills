# Technical design and ADRs

Use for a software project's intended technical contract or an explicitly
requested account of its current design. Read the owning design, requirements,
decisions and relevant code/interfaces. Distinguish target behavior from observed
implementation. A missing implementation does not imply a missing design.

## Define only the contract this work needs

Design drivers include declared goals, constraints, quality requirements,
stakeholder concerns, and required compatibility/migration conditions. Map every
in-scope driver to the affected design, including concerns from non-user parties.
Reuse confirmed decisions. Routine fields, encodings or adapter mappings derivable
from the existing contract are engineering choices, not new user approval gates.
Where viable alternatives change external results, ownership, identity/lifecycle
or compatibility and sources do not select one, explain the concrete difference
and leave that choice unresolved. Resolve the needed contract before dependent
implementation; an existing valid contract needs no rewrite for a code repair.

Use the views selected by actual questions, observable signals or repository
requirements. They are not compulsory headings or a requirement for diagrams.

| View | Trigger and content |
| --- | --- |
| Context | External actors/systems, trust boundary, ownership or responsibility transfer |
| Structure | Deployment units, components/modules, responsibilities and dependency direction |
| Interface | API/event/command/configuration/schema, inputs/outputs, errors, permissions and compatibility |
| Runtime | Interaction order, concurrency, timeouts, retry, idempotency, degraded operation and recovery |
| Data | Entities, ownership, state, persistence, consistency, retention and migration |
| Deployment/operations | Environment, rollout/rollback, capacity, observability and operational responsibility |
| Security | Identity/authorization, sensitive data, abuse paths and controls |
| Decisions/risks | Significant alternatives, consequences and unresolved gaps |

A significant decision changes a boundary, data/state/ownership, caller-visible
behavior or recovery, compatibility, deployment/security, declared quality goal,
or a costly hard-to-reverse choice. For a decision being made or reassessed,
record evidence, alternatives, trade-offs, consequences and risks. A description
of current design need not invent unavailable historical rationale; mark it as
a gap only if the requested judgment depends on that rationale.

## Maintain consistency and traceability

For each design driver, identify the response in a design element/decision and
its verification, rollout/migration entry or explicit gap. State responsibility,
dependencies, supported interaction/state and failure behavior that changes
implementation or verification. A gap identifies missing input and affected work.

Keep overlapping facts in one canonical location and link other views to it.
Preserve valid out-of-scope design on revision; remove unused views only when
creating a new artifact or adapting a template. Keep progress, work lists and
execution evidence in the plan rather than making design a second task ledger.

For a new design without a suitable repository template, optionally adapt
[../assets/design-spec-template.md.tmpl](../assets/design-spec-template.md.tmpl)
from the inspected drivers, selected views and decisions. A single ADR covers
its decision and affected views, not the entire system. Existing files do not
need to be recast into that template.

## Review and finish

Review all applicable views within the requested scope, including failure,
compatibility/migration, deployment or security when affected. Report a missing
view only when its semantic questions lack equivalent coverage, not because a
heading or drawing is absent. Check text, examples, diagrams and references agree.

Completion requires the requested drivers have supported responses, selected
views be covered, conflicts/gaps not be disguised as decisions and the actual
output be delivered. A bounded draft can retain clearly named gaps; do not call
it a frozen baseline. Textual consistency does not prove runtime, integration or
performance. In review-only mode return findings, without changing the subject.
