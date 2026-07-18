---
name: skill-authoring-spec
description: >
  Use with skill-creator when authoring, revising, or evaluating an Agent Skill
  in this repository. Apply the repository-specific rules for grounding
  non-obvious content, defining a cohesive responsibility, assigning a primary
  type, choosing a canonical name, writing a discriminative description, and
  designing and validating the body and resource set.
---

# Skill Authoring Spec

Use this Skill as the canonical source for this repository's Skill authoring rules. Use it together with `skill-creator`. Let `skill-creator` govern the non-overridable official format, initialization process, product metadata, and baseline validation. Within those constraints, apply this specification to every authoring decision it explicitly covers; where it is silent, follow `skill-creator`.

Add only confirmed rules that change an authoring decision. Do not preserve research history, unvalidated ideas, or empty structure for hypothetical future rules.

## Ground Non-Obvious Content

A coherent Skill can still be factually wrong. Ground every non-obvious mandatory rule, domain fact, procedure, and representative example in inspectable evidence. Valid evidence includes current project sources, authoritative documentation or policy, representative artifacts or task traces, failure records, and explicit user decisions or corrections.

Before turning evidence into instructions:

- verify its authority, scope, version, freshness, and applicability to the target environment;
- distinguish a fact or requirement from a contextual heuristic;
- resolve material source conflicts through an explicit precedence rule or preserve the uncertainty;
- omit unsupported claims, or state them as conditional heuristics with the condition that makes them useful.

Model recall, repeated unsourced claims, and popularity are not sufficient grounding for a mandatory rule. Do not require a fixed citation field or preserve research history. Keep source, version, or freshness information in the Skill only when a future executor needs it to choose correctly.

Use evidence only for the claim it can support. An explicit decision can establish local policy, not an external technical fact; an artifact or task trace can establish observed behavior, not a universal guarantee.

## Define the Primary Responsibility

Before choosing a name, complete this sentence:

> When triggered, this Skill owns ___, and its responsibility ends when ___.

Assign exactly one primary type according to that completion responsibility:

| Type | Deciding responsibility |
| --- | --- |
| `router` | Select and dispatch leaf work to downstream Skills through a host-supported handoff without owning the leaf result |
| `guidance` | Add rules, knowledge, or methods to a host task without owning the host result |
| `workflow` | Advance one responsibility through interdependent actions, decisions, or states to a verifiable terminal result |
| `capability` | Expose one or more independently invocable operations around one subject, each ending in its own result |

Classify in this order:

1. Choose `router` when a downstream Skill owns the leaf result and the target host can activate or dispatch that Skill.
2. Choose `guidance` when the primary value is changing how another task should be performed.
3. Choose `workflow` when the Skill owns progression through dependent actions or decisions toward one terminal result.
4. Choose `capability` when the Skill owns one or more operations that can each be requested, completed, and stopped independently.
5. If more than one type still applies, treat the responsibility as incoherent. Split the Skill or redefine its boundary instead of assigning multiple primary types.

Do not count operations, entry points, tools, output files, or implementation steps. A check, artifact, or recovery action that helps produce the same user result is part of that workflow, not another peer operation. Multiple entry points can still feed one workflow; one independently invocable operation can still form a capability.

Primary type agreement does not prove cohesion. Split same-type responsibilities when each has its own natural trigger and stopping point and their only commonality is a domain, product, tool, resource, or body of knowledge. Keep conditional variants of one owned result together. Keep capability operations together when they act on one canonical subject and share user-visible invariants. Merge separate Skills when real requests cannot distinguish their selection boundary or owned result.

A workflow may have alternative terminal branches such as success, missing input, denied authorization, or failed validation. Define only branches that are reachable in the actual responsibility. Each included branch must state where responsibility ends and what evidence is returned.

Do not classify by implementation or distribution. `scripts/`, `references/`, `assets/`, CLI, API, MCP, plugins, installation scope, and source provenance are not primary types.

Do not classify by orchestration style. An orchestrator that owns the final combined result is a `workflow`; one that primarily selects and hands off leaf work is a `router`. A mandatory prerequisite is a trigger constraint, not a type.

A router is valid only when the target host can accept downstream Skill activation or dispatch. Naming, returning, or recommending a target Skill is not a completed handoff. If the Skill only advises the host which target to use, classify it as `guidance`; if it owns and returns the routing decision as its result, classify it as `workflow`.

Treat a gate as a `workflow` subtype, not a primary type. A gate validates without repairing and ends with a decision about whether work may continue, whether a state is trustworthy, or whether criteria passed. A check that also produces revisions or owns remediation is an ordinary `workflow`, not a gate.

## Name by Type

| Type | Preferred form | Examples |
| --- | --- | --- |
| `capability` | `<canonical-subject>` or `<domain>-<subject>` | `linear`, `agent-browser` |
| `workflow` | `[<scope>-]<verb>-<object>` | `gh-fix-ci`, `sync-software-doc-suite` |
| Transformation workflow | `[<scope>-]<source>-to-<target>` | `spec-to-backlog`, `figma-design-to-code` |
| `guidance` | `<scope>-spec`, `<scope>-standards`, or `<scope>-guidelines` | `skill-authoring-spec`, `react-performance-guidelines` |
| `router` | `<domain>-router` | `slack-router` |

Use guidance suffixes deliberately:

- Use `-spec` for the complete authoritative contract for a scope.
- Use `-standards` for mandatory, auditable constraints within a scope.
- Use `-guidelines` for recommendations that require contextual judgment.

Lead workflow names with a base-form verb. For validation workflows, choose a verb that states the validation target, such as `validate-skill`, `check-release-readiness`, or `verify-deployment`.

## Validate the Name

Check every candidate name against all of these rules:

1. Use only lowercase letters, digits, and single hyphens, with at most 64 characters.
2. Do not start or end with a hyphen or use consecutive hyphens. Match the Skill directory name exactly.
3. Use domain terms that users and agents are likely to include in real requests.
4. Use the shortest name that still identifies the primary responsibility unambiguously.
5. Add a product, domain, or tool prefix only to remove ambiguity, prevent a collision, or improve triggering.
6. Search the target collection for an existing name before accepting the candidate.
7. Keep selection-relevant trigger conditions, prerequisites, scope boundaries, and exclusions in `description`, not in the name.
8. Do not add `skill-type` metadata merely to persist this classification. Express it through the responsibility, name, and `description`.

Avoid generic role or container suffixes such as `-skill`, `-agent`, `-assistant`, `-helper`, `-manager`, `-workflow`, `-process`, and `-toolkit`. Retain one only when it is part of the canonical subject or product identity; in `skill-authoring-spec`, `skill` is the subject rather than a suffix.

Avoid vague modifiers such as `advanced`, `smart`, `ultimate`, `best`, and `pro`. Do not encode `cli`, `api`, `mcp`, `script`, `plugin`, `local`, or `remote` unless that implementation distinction materially changes user intent or the trigger boundary.

## Write the Description as a Trigger Contract

Treat `description` as the Skill's selection contract, not as a promotional summary or a compressed copy of the body. An agent sees the name and description before deciding whether to load the body, so the description must contain the information needed to make that decision.

Build the description from this semantic contract:

```text
description =
  responsibility
  + applicability
  + [hard prerequisite]
  + [nearest-sibling boundary]
```

The contract does not impose a fixed prose template. Front-load responsibility and applicability because hosts may shorten descriptions in large collections. Put optional prerequisites and sibling boundaries afterward unless a prerequisite must be understood first to determine eligibility.

### Include the Required Information

Always include both of these elements:

1. **Responsibility**: State the concrete result, capability, routing decision, or guidance the Skill contributes. Describe user-visible responsibility rather than internal implementation.
2. **Applicability**: State when to invoke the Skill using representative signals that can be observed in a real request, such as user intent, subject, artifact, current state, or desired deliverable.

Use the primary type to decide what responsibility and applicability mean:

| Type | Description emphasis |
| --- | --- |
| `capability` | Name the canonical subject and representative independently invocable operations or results supported around it. |
| `workflow` | Name the starting intent or state and the bounded result the Skill owns. |
| `guidance` | Name the host task and the rules, knowledge, or method injected into that task. Do not imply ownership of the host result. |
| `router` | Name the broad or unresolved intent that needs routing and the point at which responsibility passes to a leaf Skill. |

For a gate, describe the state being assessed and the decision or evidence returned. State the no-remediation boundary when a nearby workflow could otherwise appear to own both checking and repair.

### Add Optional Information Only When It Changes Selection

Add a **hard prerequisite** when the Skill is ineligible, unsafe, or out of order without it. For example, `skill-authoring-spec` requires `skill-creator`; that relationship belongs in its description because selecting the specification alone would produce the wrong authoring flow.

Add a **nearest-sibling boundary** when a realistic request could plausibly select the wrong Skill. State the one distinction that resolves that confusion. Do not list every non-goal or every Skill that should not trigger.

Express a boundary as a positive responsibility split when possible. If several exclusions have the same cause, collapse them into one ownership statement instead of listing negative verbs.

Prefer:

```text
Apply migration safety rules while another task authors or reviews the
migration; the host task retains ownership of execution and remediation.
```

Avoid:

```text
Does not create, execute, apply, repair, rerun, or roll back migrations and
does not read or change databases.
```

The positive version exposes the deciding responsibility boundary. The negative version overfits to a list that will remain incomplete.

A boundary may distinguish:

- the artifact, product, audience, or lifecycle state;
- guidance from ownership of the host result;
- routing from execution of leaf work;
- assessment from remediation;
- a mandatory predecessor from an optional companion.

Do not add prerequisites or exclusions merely to make the description look complete. If deleting the phrase would not change an expected selection, omit it.

### Use Discriminative Language

- Prefer terms users naturally express in requests over internal architecture vocabulary.
- Use a small representative set of intents, artifacts, states, or deliverables. Do not enumerate every command or paraphrase.
- Mention a tool, file format, product, protocol, or execution surface only when it changes which Skill should be selected.
- Keep detailed steps, runtime dependencies, output schemas, completion branches, and validation procedures in the body unless one of them changes selection.
- Avoid generic quality claims such as `best`, `comprehensive`, `powerful`, or `production-ready`; they consume metadata context without distinguishing the Skill.
- Do not repeat the same meaning in multiple languages solely to add trigger keywords.
- Use the shortest description that preserves correct selection. Do not optimize toward a fixed sentence, word, or character count.

### Compare Positive and Negative Examples

#### Repository Guidance

Positive:

```text
Use with skill-creator when authoring, revising, or evaluating an Agent Skill
in this repository. Apply repository-specific rules for grounding non-obvious
content, defining a cohesive responsibility, assigning a primary type, choosing
a canonical name, and designing and validating the body and resource set.
```

This states the host task, repository scope, mandatory companion, and the rules contributed by the guidance Skill.

Negative:

```text
The ultimate guide to building excellent Agent Skills with accumulated best
practices for any authoring task.
```

This uses promotional claims, provides no observable trigger boundary, omits the required companion, and says nothing that distinguishes this repository's specification from generic authoring guidance.

#### Capability

Positive:

```text
Work with Linear issues, projects, and team workflows. Use when reading,
creating, or updating Linear work items or project state.
```

This identifies one canonical subject and representative independently invocable operations without pretending to enumerate every Linear action.

Negative:

```text
Use for project management, planning, issues, tasks, teams, roadmaps, updates,
tracking, and collaboration.
```

This is a keyword list with no product boundary and would compete with many unrelated project-management Skills.

#### Workflow with a Sibling Boundary

Positive:

```text
Diagnose and fix failing GitHub Actions checks on a pull request. Use when a
user asks why PR checks failed or wants those failures repaired; do not use for
local test failures without a GitHub Actions run.
```

The final clause is justified because local test repair is a plausible neighboring workflow.

Negative:

```text
Use for CI, GitHub, tests, logs, Actions, pipelines, failures, debugging, and
fixes.
```

This does not define the owned result or distinguish pull-request checks from local tests, other CI providers, or general debugging.

#### Gate

Positive:

```text
Assess whether a release candidate satisfies this repository's publication
criteria and return pass/fail evidence. Use before publishing; report failures
without remediating them.
```

This identifies the assessed state, decision, timing, and the boundary from a repair workflow.

Negative:

```text
Check release readiness and fix any problems before publishing.
```

This merges assessment and remediation, so it no longer describes a coherent gate responsibility.

### Validate Selection Against the Collection

Evaluate a description together with the other Skills available in the target collection. A description that looks clear in isolation can still duplicate or overlap a sibling.

Build a small selection matrix:

1. **Should trigger**: Include direct and indirect requests that need this Skill, using different natural phrasings.
2. **Should not trigger**: Include requests that share vocabulary but belong to a sibling or unrelated Skill.
3. **Ambiguous**: Include realistic requests for which multiple Skills appear plausible, and record whether the expected result is one Skill, an ordered pair, or intentional co-use.

Treat these entries as **selection cases**, not evidence that the target agent will select correctly. Review them against the name and description first. When claiming actual selection behavior, run an independent model evaluation without explicitly naming the Skill or showing the evaluator the intended answer or rationale. Keep expected cases separate from observed results.

Delete or shorten each phrase and review the cases again. Keep a phrase only when its removal leaves a missed trigger, false trigger, incorrect order, or unresolved sibling ambiguity in the written contract. Call a phrase causally necessary only after a repeated model evaluation shows the regression. Add phrases in response to concrete failures, not by accumulating keywords.

## Design the Body as a Behavioral Delta

Treat the body as the post-trigger behavioral delta: the instructions an agent would not otherwise know but needs to fulfill the declared responsibility reliably. Do not use it as an introduction to the subject, a second description, or a record of the authoring taxonomy.

Build the body from this semantic contract:

```text
body =
  non-obvious decisions and instructions
  + [conditional resource routing]
  + [failure-preventing boundaries or evidence]
```

Every element is conditional on concrete behavioral value. Keep a sentence, example, or section only when removing it makes a realistic task more likely to produce a wrong decision, unsafe action, incomplete result, false success, or unnecessary resource load.

### Apply the Universal Rules

- Write direct instructions in imperative or infinitive form.
- Ground non-obvious mandatory rules and domain claims in inspectable evidence; do not convert uncertainty into an unconditional instruction.
- Put initial selection conditions in `description`; the body loads only after selection. Repeat a condition only when it also controls a post-trigger decision or protects a concrete boundary.
- Do not explain the primary type or require type-named headings. The operational instructions must remain sufficient if every taxonomy label is removed.
- State priorities, invariants, authorization boundaries, recovery behavior, or evidence only when they prevent a realistic failure.
- Do not add writes, installations, commits, external messages, deployments, or other side effects that are not required by the declared responsibility.
- Route to a bundled resource only when the current operation needs it. State the condition and exact resource path; do not duplicate the resource in the body.
- Keep instructions internally consistent and reachable. Do not declare two incompatible first actions or require a mandatory next action beyond the Skill's stopping point.
- Use examples to resolve a decision edge, not to restate an obvious rule.

This specification adds no fixed heading, section order, line count, step count, example count, or resource layout. Apply `skill-creator`'s progressive-disclosure guidance instead of treating any count as a quality target.

### Preserve the Type-Specific Responsibility

The primary type changes the behavior the body must preserve. It does not prescribe a Markdown template.

| Type | Body contract |
| --- | --- |
| `capability` | Expose independently invocable operations and execute only those requested, with operation-specific results. |
| `workflow` | Advance one owned result through its dependent actions and decisions to truthful completion or a real blocker. |
| `guidance` | Change decisions inside a host task through rules, priorities, or methods without taking over the host result. |
| `router` | Resolve intent, obtain host-accepted downstream activation or dispatch, and stop without performing leaf work. |

#### Capability Body

Preserve the independence of supported operations:

- Distinguish the requested operation when the Skill supports more than one and the choice is not already obvious.
- State shared constraints and invariants once, then keep operation-specific instructions with the operation they govern.
- Give every instructed operation its own necessary inputs or state, actions or resource route, result, and validation when false success is plausible.
- Execute only the requested operations. When a request combines operations, compose only those operations in a valid order.
- Allow a complex operation to contain an internal sequence without turning all supported operations into one global workflow.

Positive:

```text
Perform only the requested PDF operation. For form filling, read
references/forms.md; text extraction does not require it. Validate the output
of each write operation before returning it.
```

Negative:

```text
Run merge, split, extraction, and form filling in order. The capability is
complete when all operations finish.
```

The negative version destroys operation independence and performs unrequested work.

#### Workflow Body

Preserve one bounded result:

- Encode order only where order changes correctness, safety, authorization, or recoverability.
- State the decisions that select a branch and keep every mandatory sequence consistent and reachable.
- Define completion evidence that proves the result actually claimed. A returned URL proves that a URL exists; it does not prove that the deployed application is healthy.
- Cover only real blockers and alternative endings. Do not invent branches merely to fill a completion template.
- Stop at the declared result. Do not append a mandatory downstream action that belongs to another responsibility.

Positive:

```text
Inspect the failed checks, patch the smallest supported cause, and rerun the
affected check. If rerunning is unavailable, return the observed evidence, the
exact unrun verification, and the blocker.
```

Negative:

```text
Always emit separate success, missing-input, denied-authorization,
failed-validation, handoff, and next-step reports.
```

The negative version manufactures branches regardless of whether the workflow can reach them.

For a gate, define the assessed state, criteria, evidence, and decision. Report failed criteria without repairing them. If the body repairs failures or continues into the gated action, it describes an ordinary workflow rather than a gate.

#### Guidance Body

Preserve host-task ownership:

- Supply the actual rules, heuristics, methods, exceptions, or domain facts that change the host task.
- State precedence when repository rules, user instructions, external standards, or heuristics can conflict.
- Explain how a rule affects a decision when the implication is not obvious; prefer a focused contrast or example over generic background.
- Leave execution, output production, remediation, and completion with the host task unless the responsibility is reclassified.
- Do not turn guidance into an end-to-end procedure or require an independent deliverable merely to make it look actionable.

Positive:

```text
While the host task authors a schema migration, require
expand-migrate-contract ordering. Repository rules take precedence over the
general heuristic. Leave execution and remediation to the host task.
```

Negative:

```text
Author the migration, deploy it, repair failures, and finish only when
production succeeds.
```

The negative version takes ownership of the host result and is no longer guidance.

#### Router Body

Preserve the handoff boundary:

- Confirm that the target host supports downstream Skill activation or dispatch before defining the responsibility as routing.
- Map discriminating request signals to concrete downstream Skills.
- Define tie-breaking, intentional multi-Skill ordering, or clarification only for realistic ambiguity.
- Define what to do when no downstream Skill matches or a required target is unavailable.
- Pass only the context the downstream Skill needs, including any resolved intent, selected target, relevant inputs, and ordering constraints.
- Treat handoff as complete only after the host accepts activation or dispatch of the available target, then stop. Do not repeat downstream procedures or execute leaf work.

Dispatching among bundled references, scripts, or operations does not make a Skill a router when the same Skill still owns the result.

Positive:

```text
Route GitHub Actions failures to gh-fix-ci and unresolved review threads to
gh-address-comments. When both apply, hand off CI repair first, then review
work. Treat each handoff as complete only after the host accepts activation,
then stop after the ordered dispatch.
```

Negative:

```text
Choose the closest downstream Skill, then inspect logs, edit files, run tests,
and implement the repair yourself.
```

The negative version selects a leaf and then violates the handoff boundary by owning its work.

Returning or recommending the target name without accepted activation is a routing decision, not a completed handoff.

### Scale Precision by Risk, Not Type

Use high freedom when multiple approaches are valid and contextual judgment is the Skill's value. Use lower freedom when order, reproducibility, permissions, or irreversible effects make variation dangerous. A workflow can be one short instruction; guidance can require strict rules and precedence. Do not infer instruction strictness from the primary type.

Likewise, choose an operation map, ordered procedure, rule set, decision table, checklist, or example because the execution problem needs it, not because a type requires that presentation.

### Validate the Prompt Contract

Verify content grounding before reviewing prompt coherence; a closed contract can consistently enforce a false premise. Treat prompt quality and runtime effectiveness as separate claims. Review every Skill as a closed contract using only its `description`, body, conditionally reachable references, mandatory companion Skills, and explicit host guarantees. Do not let the reviewer supply missing rules from general knowledge or the author's intent.

Use a counterexample gate rather than a score. Revise the Skill when one realistic request and state can produce two materially conflicting behaviors, no behavior can satisfy all applicable instructions, a branch has no reachable result, or the text permits responsibility drift, unauthorized effects, or unsupported success claims.

Derive scenario walkthroughs from actual decision edges, not from line count, type, or a fixed case quota:

| Type | Prompt-contract walkthrough |
| --- | --- |
| `capability` | Trace each supported operation and real combination from request through inputs, resource routes, distinct result or failure, and stopping point. |
| `workflow` | Trace each real path through state, ordering, authorization, evidence, terminal result or blocker, and stopping point. |
| `guidance` | Trace applicable host tasks and real precedence conflicts from rule or knowledge to a decision change while preserving host ownership. |
| `router` | Trace direct leaf, ambiguity, intentional co-use, no match, and unavailable target through selection, handoff context, and post-handoff stop. |

A walkthrough proves only that an ideal executor can derive a coherent route from the reviewed text. Use an independent model evaluation before claiming that a target model selects or follows the Skill. Use actual execution before claiming that a script, asset, tool, permission, client, or external state works. If required evidence cannot be obtained safely, mark that claim unverified instead of weakening the evidence requirement or calling the whole Skill validated.

Read [Prompt Contract Validation](references/prompt-contract-validation.md) when reviewing a draft, deriving type-specific scenarios, or deciding whether a conclusion needs text, model, or runtime evidence.

## Place Resources by Runtime Role

Create no bundled resource by default. Add one only for a concrete runtime role.

Classify proposed content by how it is consumed at runtime:

| Destination | Runtime responsibility |
| --- | --- |
| `SKILL.md` | Core behavioral instructions needed whenever the Skill triggers. |
| `references/` | Agent-readable knowledge needed only for a particular operation, branch, domain, or variant. |
| `scripts/` | Executable logic that needs deterministic behavior, is easy to implement incorrectly, or would otherwise be rewritten repeatedly. |
| `assets/` | Material copied, filled, transformed, or embedded in the final output rather than read as instructions. |
| Omit | Content whose removal does not create a concrete behavioral or output failure. |

Classify by runtime consumer, not extension or primary type. Route each resource from the body with its exact path and use condition; never preload all resources or duplicate their content.

Read [Resource Layering](references/resource-layering.md) when placing or auditing Skill content and resources.

## State the Decision

Before writing the Skill body or bundled resources, resolve these decisions:

- the evidence, authority, scope, and uncertainty behind non-obvious content;
- the owned responsibility and stopping point;
- the primary type, same-type cohesion boundary, canonical name, and selection contract;
- the non-obvious behavioral delta and the minimal form that expresses it;
- the should-trigger, should-not-trigger, and ambiguous selection cases;
- the type-specific contract scenarios that could expose ambiguity, contradiction, responsibility drift, or false success;
- each resource's runtime role and conditional route;
- which conclusions are supported by text, model evaluation, or runtime evidence, and which remain unverified.

Record the decisions in the form best suited to the task. Do not require fixed headings, serialized fields, a universal case count, or a total quality score.

If the content is not grounded, or the responsibility does not produce one stable type, one cohesive boundary, one concise name, a description that passes the selection matrix, a body that preserves the type-specific responsibility, and only necessary resources, return to the unresolved decision. Do not hide unsupported content or an incoherent Skill behind a vague name, keyword-heavy description, generic body, or decorative resource tree.
