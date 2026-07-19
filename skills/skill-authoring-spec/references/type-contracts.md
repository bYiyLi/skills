# Responsibility and Type Contracts

Use this reference when defining or reviewing a Skill's responsibility,
primary type, stopping point, or type-specific body contract.

## Define One Responsibility

Complete this sentence before assigning a type:

> When triggered, this Skill owns ___, and its responsibility ends when ___.

Use exactly one primary type:

| Type | Deciding responsibility |
| --- | --- |
| `router` | Select and dispatch leaf work through a host-supported handoff without owning the leaf result. |
| `guidance` | Change decisions inside a host task through rules, knowledge, or methods without owning the host result. |
| `workflow` | Advance one responsibility through interdependent actions, decisions, or states to a verifiable terminal result. |
| `capability` | Expose independently invocable operations around one subject, each ending in its own result. |

Classify in this order:

1. Choose `router` when a downstream Skill owns the leaf result and the target
   host explicitly guarantees activation or dispatch.
2. Choose `guidance` when the primary value is changing how another task is
   performed.
3. Choose `workflow` when the Skill owns progression through dependent actions
   or decisions toward one terminal result.
4. Choose `capability` when the Skill owns operations that can each be requested,
   completed, and stopped independently.
5. If more than one type still applies, split the Skill or redefine its
   responsibility instead of assigning multiple types.

Do not classify by tools, entry points, output files, resource directories,
distribution method, or implementation. A check, artifact, or recovery action
that helps produce the same result remains part of that result's workflow.

## Separate Capability from Workflow

Use the written contract, not hidden implementation steps. Input checks,
deterministic implementation branches, failure returns, and final-result
validation remain inside one operation and do not by themselves create a
workflow.

Classify a one-operation Skill as `workflow` only when reaching its result
requires an intermediate boundary that:

- has its own authorization;
- uses newly observed evidence to determine which continuation is allowed;
- must persist for recovery or re-entry; or
- supports an intermediate completion claim.

Otherwise classify it as `capability` when the operation has its own inputs and
result.

Primary type agreement does not prove cohesion. Split same-type responsibilities
when each has its own natural trigger and stopping point and their only shared
property is a domain, product, tool, resource, or body of knowledge. Keep
conditional variants of one result together. Keep capability operations together
when they act on one canonical subject and share user-visible invariants. Merge
separate Skills when requests in the target collection cannot distinguish their
selection boundary or owned result.

## Handle Special Cases

Treat `gate` as a `workflow` subtype. A gate assesses declared criteria and ends
with a decision about whether work may continue or a state is trustworthy. It may
collect evidence but must not repair the subject or continue into the gated
action. Missing evidence remains unresolved unless the governing policy defines
it as failure.

Treat a source-to-target transformation as a workflow naming variant when the
Skill owns progression to one transformed result. It is not a fifth primary
type.

Treat an orchestrator that owns the combined result as `workflow`. Treat it as
`router` only when it selects downstream Skills, obtains host-accepted activation
or dispatch, and stops without owning leaf work or the combined result.

A router is valid only when the intended host explicitly guarantees downstream
Skill activation or dispatch. Returning or recommending a target name is a
routing decision, not a completed handoff. If host support is unknown, leave the
type unresolved. If the host lacks support, classify selection advice as
`guidance` or an owned routing decision as `workflow`.

## Preserve the Type in the Body

The primary type changes behavior, not Markdown structure. Do not require
type-named headings in an authored Skill.

### Capability

- Distinguish the requested operation when the Skill supports more than one.
- State shared invariants once and keep operation-specific inputs, actions,
  resource routes, results, and validation with their operation.
- Execute only requested operations. Compose combined requests only in an order
  justified by dependency, authorization, side effects, or recovery.
- Validate a result when the immediately available action evidence does not
  directly prove the claimed result.
- Preserve completed independent results when another requested operation fails.

### Workflow

- Define the entry state and first allowed action.
- Encode order only when changing it can alter the result, authorization, side
  effects, or recovery.
- Define the condition selecting each reachable branch.
- End every path at the owned result or a real blocker.
- Match completion claims to obtainable evidence.
- Stop at the declared result instead of appending downstream work.
- On recovery, inspect current state instead of repeating completed side effects.

### Guidance

- Supply rules, knowledge, methods, priorities, or exceptions that change a
  concrete host decision.
- Resolve reachable precedence conflicts or leave the decision explicitly
  unresolved.
- Explain a rule's decision effect when it is not evident from the rule itself.
- Leave execution, output production, remediation, and completion with the host
  task.
- Do not invent an independent deliverable merely to make guidance look
  actionable.

### Router

- Map observable request signals to canonical downstream Skills.
- Define clarification, tie-breaking, intentional co-use, no-match, and
  unavailable-target behavior only for reachable cases.
- Impose ordering only when one leaf result supplies input required by another.
- Pass the resolved intent and only the context required by each selected target.
- Treat handoff as complete only after the host accepts activation or dispatch.
- Stop after handoff without repeating downstream procedures or executing leaf
  work.

Routing among a Skill's own operations or resources does not make it a router
when that Skill still owns the result.
