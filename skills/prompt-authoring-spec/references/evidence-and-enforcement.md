# Evidence and Enforcement

Use this reference when instructions assert source-dependent rules or current
facts, depend on runtime or host behavior, govern permissions or side effects,
define completion evidence, or specify an evaluation.

## Ground Source-Dependent Claims

Ground a statement when it asserts a project rule, external contract, current
fact, required procedure, or representative behavior and an error could change
a decision. The normative writing rules in this specification are policy defined
by the specification and do not require external citation.

Valid evidence includes applicable project sources, authoritative documentation
or policy, representative artifacts or task traces, failure records, and
explicit user decisions.

Before turning evidence into an instruction or claim:

- verify authority and scope;
- verify version and freshness when the source can change;
- distinguish a fact or requirement from a contextual heuristic;
- resolve material conflicts through precedence or preserve uncertainty;
- omit an unsupported claim or condition it on the evidence that makes it
  useful.

When authority is missing, define only supported temporary behavior. Do not
invent prerequisites, approvals, fields, schemas, safeguards, runtime states, or
machine-enforced guarantees. Model recall, repetition, and popularity do not
ground a mandatory rule. A local decision establishes local policy; an observed
artifact establishes behavior only in its observed scope.

## Assign Each Requirement to Its Enforcing Layer

| Layer | Put here |
| --- | --- |
| Model-visible instruction | Semantic choices, priorities, interpretation, context use, requested behavior, and reporting boundaries. |
| Schema or protocol | Field names, types, required properties, enums, and machine-checkable structure. |
| Host implementation or policy | Authorization, permission enforcement, invariants, side-effect control, secrets, and deterministic limits. |
| Runtime context or tool result | Current state, observations, returned evidence, and actual success or failure. |
| Evaluation fixture or harness | Cases, expected outcomes, baselines, repetitions, thresholds, and comparison logic. |

Do not ask a prompt to simulate a guarantee owned by another layer. Repeat a
machine-enforced rule in model-visible text only when the model must know it
before choosing an action or interpreting a result.

## Inspect Runtime Only When It Changes the Contract

Do not require runtime or model identification by default. Inspect a runtime fact
only when it changes instruction priority, visible context, available behavior,
syntax, or the strength of a possible guarantee.

When such a dependency exists:

- identify what the model can see at the decision point;
- identify the behavior the text can affect;
- identify available authority and tools;
- inspect the authoritative source for version-sensitive claims; and
- preserve a material unknown as an assumption and limit the resulting claim.

Do not silently assume unavailable context, authority, tools, or host behavior.

## Resolve Scope and Conflict

- State a condition and scope when placement does not make them evident.
- State precedence only for conflicts reachable within the declared scope. Name
  the winner, applicable exception, or unresolved behavior.
- Do not require incompatible actions. If satisfying one priority can violate
  another, state the condition that decides between them.
