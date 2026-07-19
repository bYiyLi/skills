# Skill Contract Validation

Use this reference when reviewing Agent Skill responsibility, type, selection,
resource reachability, and stopping boundaries. It evaluates the Skill-specific
contract and does not claim to evaluate general instruction-writing quality.

## Contents

- [Review a Closed Skill Contract](#review-a-closed-skill-contract)
- [Derive Skill-Specific Scenarios](#derive-skill-specific-scenarios)
- [Review Responsibility Cohesion](#review-responsibility-cohesion)
- [Review Capability Contracts](#review-capability-contracts)
- [Review Workflow Contracts](#review-workflow-contracts)
- [Review Guidance Contracts](#review-guidance-contracts)
- [Review Router Contracts](#review-router-contracts)
- [Evaluate Selection at Collection Scope](#evaluate-selection-at-collection-scope)

## Review a Closed Skill Contract

Judge only the Skill material and verified host behavior that govern the
reviewed path:

```text
contract =
  name and description
  + loaded body
  + resources reachable on the selected path
  + explicitly declared dependencies
  + verified invocation and authorization behavior for the selected path
  + explicit runtime guarantees
```

Do not silently add a missing default, permission, tool capability, domain rule,
target Skill, or recovery path from general knowledge. Apply these Skill-specific
boundaries:

- The body cannot repair missing selection information because it is unavailable
  before triggering.
- An unlinked reference is not part of an execution path merely because it
  exists in the directory.
- A script or asset declaration proves only the intended interface until the
  applicable runtime evidence verifies its behavior.
- A dependency affects the contract only when the relationship is explicitly
  declared and reachable on the reviewed path.
- If invocation or authorization behavior changes the reviewed path and cannot
  be verified, keep that behavior unverified. Do not infer enforcement from the
  body alone.
- A host capability may be assumed only when the target host guarantees it or
  the Skill handles its absence.
- A required reference, script, or asset that is missing, unreadable, or
  case-mismatched blocks the selected path. Do not treat it as reachable or
  claim a complete contract; a resource outside the selected path may remain
  unverified.

## Derive Skill-Specific Scenarios

Derive counterexamples from observable decision edges and cover the paths implied
by the Skill's primary type:

| Type | Skill-contract walkthrough |
| --- | --- |
| `capability` | Trace each supported operation and real combination from request through inputs, resource routes, distinct result or failure, and stopping point. |
| `workflow` | Trace each real path through state, ordering, authorization, evidence, terminal result or blocker, and stopping point. |
| `guidance` | Trace applicable host tasks and real precedence conflicts from rule or knowledge to a decision change while preserving host ownership. |
| `router` | Trace direct leaf, ambiguity, intentional co-use, no match, and unavailable target through selection, handoff context, and post-handoff stop. |

Include a natural request within the declared scope and only the state needed to expose each decision.
Cover each distinct reachable edge and each collection overlap that can change the route; stop when another case
would follow the same route and require the same evidence rather than targeting a
fixed number of cases. A scenario walkthrough supports only the conclusion that
an ideal executor can derive a coherent route from the reviewed contract.

## Review Responsibility Cohesion

Write a natural request and stopping point for each proposed
responsibility without referring to the others.

- Split responsibilities when each can trigger and stop independently and their
  only shared property is a domain, product, tool, resource, or body of
  knowledge.
- Keep conditional branches or variants together when they advance one owned
  result.
- Keep capability operations together when they act on one canonical subject
  and share user-visible invariants; independent requestability alone does not
  require one Skill per operation.
- Merge separate Skills when requests within the declared collection cannot distinguish their
  selection boundary or owned result.

Shared implementation lowers duplication but does not establish a shared
responsibility. Different providers, formats, or internal paths do not require
separate Skills when they remain variants of one result or operation boundary.

## Review Capability Contracts

Trace the capability as:

```text
request and state
  -> selected operation or operations
  -> operation-specific inputs and resource routes
  -> independent results or failures
  -> operation-specific stopping points
```

Check that:

- every declared operation can be requested, completed, and stopped
  independently rather than serving as a mandatory stage, check, artifact, or
  recovery action for one result;
- the operations share one canonical subject and user-visible invariants rather
  than only a vendor, tool, or broad domain label;
- each operation can run without unrelated operations or their resources;
- missing, invalid, conflicting, or authorization-sensitive inputs lead to one
  defined decision;
- each operation owns a distinct result and evidence proportionate to that
  result;
- a combined request composes only requested operations in an order justified
  by dependency, authorization, side effects, or recovery;
- partial failure does not erase completed independent results or falsely claim
  the whole request succeeded;
- freedom remains only where alternatives preserve required permissions, side
  effects, success criteria, and evidence.

Reject this contract:

```text
For every PDF request, load all references and run extraction, merge, form
filling, and upload in order. Return success when processing finishes.
```

It destroys operation independence, loads irrelevant resources, performs
unrequested work, and leaves each result undefined.

## Review Workflow Contracts

Trace each meaningful instruction as a Skill-owned state transition:

```text
transition =
  current state + condition + required authorization
  -> action + obtainable evidence + next state

terminal =
  claimed state + supporting evidence + stopping boundary
```

Check that:

- the entry state and first admissible action are unambiguous;
- order is imposed only when reordering can change the required result,
  authorization, side effects, or recovery;
- every branch reachable under supported inputs and states ends in the owned
  result or a genuine blocker;
- protected actions occur only after the required authorization;
- a blocker names the missing condition, observed state, unperformed
  verification, and re-entry requirement;
- every completion statement is no stronger than its obtainable evidence;
- the workflow stops at its result instead of adding commits, messages,
  releases, deployments, or other downstream work;
- recovery reads current state and avoids repeating completed side effects
  blindly.

For a gate, preserve the assessment-only subtype:

- `pass` requires current evidence for every mandatory criterion;
- `fail` requires evidence that at least one criterion is not satisfied;
- missing evidence remains indeterminate unless the governing policy explicitly
  defines unknown as failure;
- the gate may collect evidence but must not repair the subject or continue into
  the gated action.

## Review Guidance Contracts

Trace guidance as:

```text
host task and applicable condition
  -> rule, knowledge, or method
  -> observable host decision change
  -> host retains execution and completion
```

Check that:

- deleting the guidance would change at least one concrete host decision;
- rules state applicable conditions, decisions or constraints, and real
  exceptions;
- knowledge changes interpretation, risk, or option selection rather than
  merely introducing the subject;
- methods narrow decisions more than generic phrases such as `use best
  judgment`;
- every reachable conflict has a winner, a documented exception, a request for
  evidence, or an explicit return of the unresolved decision to the host;
- the description identifies the host task and distinguishable applicability
  signals;
- authoring, review, and execution modes remain separate where their permissions
  differ;
- final artifacts, commands, remediation, and completion remain owned by the
  host task.

Guidance may constrain what evidence the host must obtain without taking
ownership of obtaining it. If the Skill authors, executes, repairs, and
completes the host result itself, reclassify it as a workflow.

## Review Router Contracts

Trace the router as:

```text
request signals
  -> target Skill or intentional co-use
  -> resolved intent and minimum handoff context
  -> host-accepted activation or dispatch
  -> stop
```

Check that:

- mappings use observable intent, artifact, state, audience, or desired result
  rather than keyword counts;
- the target host explicitly guarantees downstream Skill activation or dispatch;
- when that guarantee is absent or unknown, routing remains unresolved rather
  than becoming a completed handoff;
- each target is a canonical Skill that owns the stated leaf result;
- tie-breaking resolves candidates competing for the same result, while
  intentional co-use handles requests with multiple independent results;
- ordering exists only when one leaf result supplies state or data required by
  another;
- insufficient intent requests the missing observable facts needed to distinguish
  targets, while a desired result matching no available target reports no match;
- an unavailable target is reported as unavailable rather than treated as no
  match or executed by the router;
- handoff context contains all inputs and constraints required by the selected
  target without forwarding unrelated conversation history;
- the router treats handoff as complete only after the host accepts activation
  or dispatch, then stops without executing leaf work or combining leaf results.

Target existence, ownership, sibling overlap, and required handoff inputs are
collection-level facts. Returning or recommending a target name is a routing
decision, not evidence that handoff occurred. When the host cannot activate
downstream Skills, reclassify selection advice as `guidance` or an owned routing
decision as `workflow`.

## Evaluate Selection at Collection Scope

Use the target collection explicitly supplied by the task. If the task supplies
no collection, use the collection actually exposed on the intended selection
surface. If that collection cannot be inspected, keep name collision, sibling
overlap, and observed selection claims unverified.

Keep expected selection cases separate from observed selection behavior:

- A `should trigger` case defines intended coverage.
- A `should not trigger` case defines a nearest-sibling or unrelated boundary.
- An `ambiguous` case defines one target, clarification, ordered use, or
  intentional co-use.

When the selection surface may shorten metadata, verify that the description's
opening still identifies the responsibility and applicability before optional
detail is lost. Claim that a target model selects the Skill correctly only from
an independent evaluation on the named model and selection surface.

For router collections, distinguish a direct leaf request from a broad
unresolved request. Whether the leaf, router, or an ordered pair should be
selected is a collection policy, not something the router body can decide after
loading.
