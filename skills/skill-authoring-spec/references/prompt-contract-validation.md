# Prompt Contract Validation

Use this reference when evaluating a Skill draft, deriving review scenarios, or deciding what evidence a quality claim requires.

## Contents

- [Separate the Claim from the Evidence](#separate-the-claim-from-the-evidence)
- [Verify Content Grounding](#verify-content-grounding)
- [Review a Closed Contract](#review-a-closed-contract)
- [Use Counterexamples Instead of Scores](#use-counterexamples-instead-of-scores)
- [Derive Scenarios from Decision Edges](#derive-scenarios-from-decision-edges)
- [Review Responsibility Cohesion](#review-responsibility-cohesion)
- [Review Capability Contracts](#review-capability-contracts)
- [Review Workflow Contracts](#review-workflow-contracts)
- [Review Guidance Contracts](#review-guidance-contracts)
- [Review Router Contracts](#review-router-contracts)
- [Evaluate Selection at Collection Scope](#evaluate-selection-at-collection-scope)
- [Escalate Evidence by Claim](#escalate-evidence-by-claim)
- [Reduce Content without False Ablation Claims](#reduce-content-without-false-ablation-claims)
- [Report the Proven Scope](#report-the-proven-scope)

## Separate the Claim from the Evidence

Do not treat prompt quality, model behavior, and runtime correctness as one validation result. Use the least expensive evidence that can actually support the conclusion:

| Evidence | What it can establish | What it cannot establish |
| --- | --- | --- |
| Text review | Format facts, responsibility, explicit rules, visible ambiguity, contradiction, reachability, and stopping boundaries | That a target model will trigger, comply, or generalize |
| Source review | That a non-obvious claim is supported by an inspected source with applicable authority, scope, and freshness | That the claim remains true outside that scope or after the source changes |
| Scenario walkthrough | That an ideal executor can derive one coherent route for the stated facts | That a target model will take that route |
| Model evaluation | Observed selection, instruction following, handoff, or output behavior for a named model, host, Skill set, and case set | That real tools, permissions, assets, or external systems work |
| Runtime validation | Actual script behavior, asset usability, integration state, permissions, side effects, or final artifacts in a named environment | Reliability outside the tested environment or future versions |

These are evidence levels, not mandatory phases for every Skill. A pure instruction Skill can be authoring-complete after text review and sufficient scenario walkthroughs. A claim about actual model behavior or a runtime resource requires stronger evidence. Mark a conclusion unverified when its required evidence cannot be obtained safely.

## Verify Content Grounding

Review factual and normative grounding before prompt coherence. A Skill can be internally consistent while enforcing a false, obsolete, or inapplicable premise.

For every non-obvious mandatory rule, domain claim, procedure, or example presented as representative:

- identify the inspected project source, authoritative documentation or policy, representative artifact or task trace, failure record, or explicit user decision that supports it;
- match the evidence to the claim: local decisions establish local policy, authoritative sources establish their stated contract, and artifacts or traces establish observed behavior rather than universal guarantees;
- verify that the source applies to the named product, version, environment, lifecycle state, and responsibility;
- distinguish binding requirements and observed facts from contextual heuristics;
- resolve material conflicts by authority and scope, or preserve the uncertainty instead of selecting a convenient source;
- omit an unsupported claim or rewrite it as a conditional heuristic whose limits are explicit.

Model recall, search-result repetition, and popularity do not establish authority. Grounding evidence does not need a fixed field or citation section. Include source, version, or freshness in the runtime Skill only when the executor needs it to choose correctly; otherwise retain only the resulting supported instruction.

## Review a Closed Contract

Judge only the instructions available to the executor in the reviewed situation:

```text
contract =
  name and description
  + loaded body
  + references reachable on the selected path
  + mandatory companion Skills
  + explicit host guarantees
```

Do not silently add a missing default, permission, tool capability, domain rule, target Skill, or recovery path from general knowledge. The purpose of the review is to find what the prompt leaves unresolved, not to demonstrate that a capable reviewer can repair it mentally.

Closed-contract coherence assumes the supplied premises. Report content grounding separately; do not treat a coherent walkthrough as evidence that its domain rules are true.

Apply these boundaries:

- The body cannot repair missing selection information because it is unavailable before triggering.
- An unlinked reference is not part of an execution path merely because it exists in the directory.
- A script or asset declaration proves only the intended interface until runtime evidence verifies its behavior.
- A mandatory companion affects the contract only when the relationship is selection-relevant and explicitly stated.
- A host capability may be assumed only when the target host actually guarantees it or the Skill handles its absence.

## Use Counterexamples Instead of Scores

Search for a concrete request and state that exposes one of these defects:

- **Ambiguity**: two materially different behaviors both satisfy the text.
- **Contradiction**: no behavior can satisfy all applicable instructions.
- **Dead path**: a required action or terminal branch cannot be reached from its stated conditions.
- **Missing premise**: the path requires an input, permission, resource, or fact that the contract neither supplies nor handles.
- **Unsound premise**: a mandatory rule or domain claim lacks applicable support or conflicts with the governing source.
- **Responsibility collage**: independently triggered and stopped responsibilities are grouped only because they share a domain, product, tool, resource, or body of knowledge.
- **Responsibility drift**: the path performs work beyond the declared result or stopping point.
- **Evidence inflation**: the completion claim is stronger than the evidence the path can obtain.
- **Resource mismatch**: the route loads irrelevant material, omits required material, or conflicts with the referenced content.

One realistic counterexample is enough to require revision. The absence of a found counterexample supports only this conclusion:

> No contract defect was found in the reviewed scope.

It does not prove that a target model will comply or that a runtime integration works. Do not combine unrelated findings into a total score that allows a boundary or safety defect to be offset by style, completeness, or documentation quality.

## Derive Scenarios from Decision Edges

Do not trigger scenario review with vague labels such as `complex`, a line threshold, a resource count, or the primary type alone. Derive scenarios whenever behavior changes with an observable condition, including:

- requested operation or deliverable;
- input presence, validity, or conflict;
- current state or prior side effect;
- authorization or user choice;
- rule precedence or an applicable exception;
- resource, tool, or downstream Skill availability;
- success, partial result, failed validation, or recovery state.

Give each walkthrough a natural request and only the facts needed to select a path. Trace every distinct decision edge and every realistic overlap between conditions; do not target a universal case count.

For a text walkthrough, state the simulated observations directly and inspect what the contract permits. For an independent model evaluation, give the executor the natural request, raw material, and environment facts without the expected answer, suspected defect, or proposed fix. Freeze the expected decision and observable evidence before inspecting the result.

## Review Responsibility Cohesion

Primary type agreement is necessary but not sufficient. Try to write a natural request and stopping point for each proposed responsibility without referring to the others.

- Split responsibilities when each can trigger and stop independently and their only shared property is a domain, product, tool, resource, or body of knowledge.
- Keep conditional branches or variants together when they advance one owned result.
- Keep capability operations together when they act on one canonical subject and share user-visible invariants; independent requestability alone does not require one Skill per operation.
- Merge separate Skills when realistic requests cannot distinguish their selection boundary or owned result.

Shared implementation lowers duplication but does not establish a shared responsibility. Conversely, different providers, formats, or internal paths do not require separate Skills when they remain variants of one result or operation boundary.

## Review Capability Contracts

Temporarily trace the capability as:

```text
request and state
  -> selected operation or operations
  -> operation-specific inputs and resource routes
  -> independent results or failures
  -> operation-specific stopping points
```

Check that:

- every declared operation can be requested, completed, and stopped independently rather than serving as a mandatory stage, check, artifact, or recovery action for one result;
- the operations share one canonical subject and user-visible invariants rather than only a vendor, tool, or broad domain label;
- each operation can run without unrelated operations or their resources;
- missing, invalid, conflicting, or authorization-sensitive inputs lead to one defined decision;
- each operation owns a distinct result and evidence proportionate to that result;
- a combined request composes only requested operations in an order justified by dependency, safety, or authorization;
- partial failure does not erase completed independent results or falsely claim the whole request succeeded;
- freedom remains only where alternatives are materially equivalent, not around permissions, destructive effects, or success criteria.

Reject this contract:

```text
For every PDF request, load all references and run extraction, merge, form
filling, and upload in order. Return success when processing finishes.
```

It destroys operation independence, loads irrelevant resources, performs unrequested work, and leaves each result undefined.

## Review Workflow Contracts

Temporarily trace each meaningful instruction as a state transition:

```text
transition =
  current state + condition + required authorization
  -> action + obtainable evidence + next state

terminal =
  claimed state + supporting evidence + stopping boundary
```

Check that:

- the entry state and first admissible action are unambiguous;
- order is imposed only where correctness, safety, authorization, or recovery requires it;
- every real branch is reachable and ends in the owned result or a genuine blocker;
- protected actions occur only after the required authorization;
- a blocker names the missing condition, observed state, unperformed verification, and re-entry requirement;
- every completion statement is no stronger than its obtainable evidence;
- the workflow stops at its result instead of adding commits, messages, releases, deployments, or other downstream work;
- recovery reads current state and avoids repeating completed side effects blindly.

A returned URL proves that a URL was returned. It does not by itself prove service health. A local commit does not prove a remote push. A command exit code does not prove an expected artifact exists unless the contract checks that artifact.

For a gate, preserve the assessment-only subtype:

- `pass` requires current evidence for every mandatory criterion;
- `fail` requires evidence that at least one criterion is not satisfied;
- missing evidence remains indeterminate unless the governing policy explicitly defines unknown as failure;
- the gate may collect evidence but must not repair the subject or continue into the gated action.

## Review Guidance Contracts

Temporarily trace guidance as:

```text
host task and applicable condition
  -> rule, knowledge, or method
  -> observable host decision change
  -> host retains execution and completion
```

Check that:

- deleting the guidance would change at least one concrete host decision;
- rules state applicable conditions, decisions or constraints, and real exceptions;
- non-obvious mandatory rules and domain facts have applicable grounding at the claimed authority, scope, version, and freshness;
- knowledge changes interpretation, risk, or option selection rather than merely introducing the subject;
- methods narrow decisions more than generic phrases such as `use best judgment`;
- every reachable conflict has a winner, a documented exception, a request for evidence, or an explicit return of the unresolved decision to the host;
- the description identifies the host task and distinguishable applicability signals;
- authoring, review, and execution modes remain separate where their permissions differ;
- final artifacts, commands, remediation, and completion remain owned by the host task.

Guidance may constrain what evidence the host must obtain without taking ownership of obtaining it. If the Skill authors, executes, repairs, and completes the host result itself, reclassify it as a workflow.

## Review Router Contracts

Temporarily trace the router as:

```text
request signals
  -> target Skill or intentional co-use
  -> resolved intent and minimum handoff context
  -> host-accepted activation or dispatch
  -> stop
```

Check that:

- mappings use observable intent, artifact, state, audience, or desired result rather than keyword counts;
- the target host actually supports downstream Skill activation or dispatch;
- each target is a canonical Skill that actually owns the stated leaf result;
- tie-breaking resolves candidates competing for the same result, while intentional co-use handles requests with multiple independent results;
- ordering exists only when one leaf result supplies state or data required by another;
- insufficient intent leads to one decisive clarification, while a clear unsupported intent reports no match;
- an unavailable target is reported as unavailable rather than treated as no match or executed by the router;
- handoff context is sufficient for the selected target without forwarding irrelevant conversation history;
- the router treats handoff as complete only after the host accepts activation or dispatch, then stops without executing leaf work or combining leaf results.

Target existence, ownership, sibling overlap, and required handoff inputs are collection-level facts. A single router file cannot establish them in isolation.

Returning, printing, or recommending a target name is a routing decision, not evidence that handoff occurred. When the host cannot activate downstream Skills, reclassify selection advice as `guidance` or an owned routing decision as `workflow`.

## Evaluate Selection at Collection Scope

Keep expected selection cases separate from observed selection behavior:

- A `should trigger` case defines intended coverage.
- A `should not trigger` case defines a nearest-sibling or unrelated boundary.
- An `ambiguous` case defines one target, clarification, ordered use, or intentional co-use.

When the target host may shorten metadata, verify that the description's opening still identifies the responsibility and applicability before optional detail is lost. Do not assume or optimize for a fixed truncation length.

Text review can find overlap and missing distinctions in the available metadata. Only a model evaluation in the target Skill collection can support a claim that implicit selection actually works. Do not explicitly name the Skill in a selection evaluation; doing so bypasses the mechanism being tested.

For router collections, distinguish a direct leaf request from a broad unresolved request. Whether the leaf, router, or an ordered pair should be selected is a collection policy, not something the router body can decide after loading.

## Escalate Evidence by Claim

Use these minimum evidence boundaries:

| Claim | Minimum evidence |
| --- | --- |
| Required files, fields, names, and paths are present | Text and filesystem review |
| A non-obvious rule or domain claim is grounded for its stated scope | Inspection of the applicable source and any material conflicts |
| The written contract covers the reviewed scenarios coherently | Text review and scenario walkthrough |
| The target model selects the Skill correctly | Independent model evaluation in the target collection |
| The target model follows the body or reads a routed reference | Model evaluation with observable output or trace |
| A paragraph or resource causally improves behavior | Repeated baseline and ablation model evaluations |
| A script produces the declared result and failure behavior | Actual script execution and artifact or state inspection |
| An asset works in its intended consumer | Open, render, or consume it through the documented path |
| A tool, permission, client, or external integration works | Runtime validation in the named target environment |
| A production workflow is reliable | Authorized representative execution, final-state evidence, repetition, and ongoing observation |

Test added or modified scripts by actual execution as required by `skill-creator`. Run each materially distinct implementation on representative success and failure cases. When many scripts are substantially equivalent, a justified representative sample is sufficient; identify what was not run and do not generalize beyond the shared implementation evidence. If the required runtime is unavailable, report the script as unverified and do not present the resource set as fully validated. Do not exercise live or production side effects without explicit authorization.

## Reduce Content without False Ablation Claims

Use two different operations:

1. **Text reduction review**: Remove a phrase, paragraph, example, or reference route and repeat the contract walkthrough. Delete it when the written contract and reviewed scenarios remain equally clear and complete.
2. **Behavioral ablation**: Run the same target model, host, Skill collection, cases, and environment with and without the content. Use repeated observed regressions before claiming causal necessity.

Text reduction can expose obvious redundancy. It cannot prove that model behavior is unchanged. Conversely, one successful run cannot prove a paragraph is unnecessary. Add or retain content for a named contract obligation or repeatable behavior failure, not to satisfy a preferred document shape.

## Report the Proven Scope

Attach evidence to each conclusion instead of declaring the entire Skill simply `validated`:

```text
Content grounding: mandatory migration rules match the inspected repository
policy and PostgreSQL version used by the project.

Prompt contract: coherent for the reviewed capability operations and failure
branches (text review and scenario walkthrough).

Implicit selection: not evaluated in the target Skill collection.

scripts/convert.py: verified for the stated success and malformed-input cases
on the named runtime.

External write path: unverified because no authorized test environment was
available.
```

Use any reporting form that communicates the proven scope. Do not require these labels as frontmatter, a serialized schema, fixed headings, a universal scenario count, or a total score.
