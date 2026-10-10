# Project setup and incremental evolution

Use the current scope and state, not a global phase number. A new product may
need foundations; an existing product reuses them; an unfinished setup needs only
its missing prerequisites. A prototype, initialization-only request or one
subsystem does not authorize the whole product backlog.

## Establish enough foundation for the target

Determine the current release goal, users, boundaries and observable acceptance
from authoritative requirements or explicit decisions. Resolve choices that
would change the product promise before their dependent design. Persist needed
requirements through the requirements route; no separate PRD is required merely
to restate an adequate existing source.

Establish the architectural decisions needed by the first increments: component
responsibility, interfaces/data, runtime and relevant quality constraints. Use
the design route when creating or changing this contract. Test a consequential
technical uncertainty with a bounded experiment when authorized; record what it
establishes and what remains unknown. Do not design every future feature first.

Build the necessary engineering foundation using the repository-contract route.
The exit evidence is a reproducible starting point appropriate to the target:
actual dependency/tool requirements, a working entry or build when applicable,
and checks capable of verifying the first implemented behavior. Integrate a real
boundary early when the product depends on it; a stub does not establish that
an external dependency works. Missing credentials, binaries or services remain
explicit blockers for their integration, not reasons to invent successful tests.

Establish applicable lint/type/build/test gates before the dependent work relies
on them. Introduce CI when the request or repository requires it; distinguish a
configured workflow from its actual run. Do not demand empty tests, artificial
coverage targets, deployment infrastructure or every possible gate at startup.
A required missing gate still blocks the acceptance that depends on it.

## Plan and execute increments

Maintain current design and the implementation plan as the durable basis for
continued development. An increment is a coherent result inside the authorized
scope, not automatically an independent Phase or a new file. Select the next
work by real dependencies, user value and unresolved risk. Use planning rules
for plan units, work, acceptance and state; reuse adequate existing records.

Before an increment, confirm its design inputs, expected result and verification
entry. Resolve only the design decisions it needs. Then implement, test, review,
fix and recheck through the verification reference. Update plan status with the
observed evidence; synchronize changed technical contracts and affected usage
information. If the design remains valid, do not rewrite it merely to log code.

After each increment, continue dependency-ready work until the requested target
is accepted or genuinely blocked. Initialization is an intermediate checkpoint
when the request includes the product. Multiple modules may be at different
stages; do not restart the whole project because one subsystem needs redesign.

## Change direction without losing the baseline

A new product requirement changes the owning requirement and acceptance first;
a technical contract change updates the affected design and dependent plan.
A discovered implementation defect follows the existing contract unless evidence
shows that contract itself needs revision. Keep unresolved product alternatives
explicit rather than silently accepting one or weakening completion criteria.

Reassess affected dependents and invalidate only evidence no longer applicable.
Preserve unchanged work and historical acceptance. Do not move failed current
requirements into a future release without the corresponding scope authority.

## Accept the requested release

Reconcile all scoped capabilities, integrated behavior and required quality
results, not merely the sum of local tests. Verify the applicable installation,
packaging, compatibility, configuration, migration or operational path required
by that deliverable. Use safe supported environments; unavailable mandatory
acceptance remains blocked rather than waived.

Apply authorized delivery through the Git/delivery route. Finishing this release
ends the current target; later feedback or a new authorized goal starts another
incremental cycle. Do not initiate unrequested ongoing or background development.
