---
name: skill-authoring-spec
description: >
  Use when authoring, revising, or reviewing an Agent Skill. Apply this
  specification's rules for defining a cohesive responsibility, assigning a
  primary type, choosing a canonical name, writing a discriminative description,
  and designing and validating the body and resource set. This specification
  evaluates the Skill-specific contract, not general instruction-writing quality.
---

# Skill Authoring Spec

Use this Skill as the canonical source for Skill-specific authoring rules.
Preserve the host task's mode. A read-only review reports findings without
changing the reviewed Skill. Author or revise only when the user requests that
result.

Naming this Skill or a target Skill does not select a mode. If the requested
result does not distinguish authoring, revision, or read-only review, ask which
result the user wants before assessing or changing the target.

Add only confirmed rules that change an authoring decision. Do not preserve
research history, unvalidated ideas, or empty structure for hypothetical rules.

## Establish the Portable Contract

Ground source-dependent rules, facts, procedures, and examples in applicable
project sources, authoritative documentation or policy, representative artifacts
or task traces, failure records, or explicit user decisions.

- A user decision establishes policy only within that user's authority and the
  stated task scope.
- An artifact or trace establishes only the behavior observed in it.
- A claim about an external format, host, or runtime guarantee requires an
  authoritative source or applicable runtime evidence.
- Resolve conflicts by instruction authority, source authority, and scope. If
  those factors do not determine a winner, preserve the conflict and do not turn
  either claim into a mandatory rule.

Treat this specification's normative rules as policy defined here, not as
evidence for external formats, runtimes, or tools.

Require every Skill to provide a stable non-empty name, a selection description,
and post-selection instructions. Let the native format supplied by the task or
exposed by the intended host govern serialization, paths, and additional
metadata. If no native format can be inspected, apply only this semantic core and
mark serialization, path, and additional-metadata conclusions unverified. Report
an unresolved format-source conflict instead of choosing a format.

Treat invocation and authorization as runtime contracts, not portable metadata
fields. When a Skill can write, delete, execute commands, send messages, commit,
push, deploy, or cause another external side effect, state the authorization
boundary needed before that action. Use a verified runtime control when one
exists. Do not claim that model-visible text alone enforces authorization.

## Define the Skill

Before choosing a name, complete:

> When triggered, this Skill owns ___, and its responsibility ends when ___.

Use exactly one primary type:

| Type | Responsibility |
| --- | --- |
| router | Select and dispatch leaf work without owning the leaf result. |
| guidance | Change decisions inside a host task without owning its result. |
| workflow | Advance one responsibility to a verifiable terminal result. |
| capability | Expose independently invocable operations around one subject. |

When defining or reviewing responsibility, type, stopping point, or body
behavior, read [Responsibility and Type Contracts](references/type-contracts.md).
Apply its general classification rules and only the type-specific body section
for the selected or candidate type.

When choosing or reviewing a name, description, prerequisite, sibling boundary,
or collection-level selection contract, read
[Naming and Selection Contracts](references/naming-and-selection.md).

Treat the description as a selection contract:

~~~text
description =
  responsibility
  + applicability
  + [hard prerequisite]
  + [nearest-sibling boundary]
~~~

Put initial selection conditions in the description because the body loads only
after selection. Keep operation-specific state, authorization, output detail,
and validation in the body unless they determine whether the whole Skill can
serve the request.

Design the body from:

~~~text
body =
  non-obvious decisions and instructions
  + [conditional resource routing]
  + [failure-preventing boundaries or evidence]
~~~

Keep an element only when removing it can cause a wrong decision, an action
outside declared permission or side-effect boundaries, an incomplete result,
false success, or an unnecessary resource load within the declared
responsibility. Do not add side effects that the responsibility does not require.
Do not prescribe type-named headings or a universal Markdown structure.

## Place Resources by Runtime Role

Create no resource by default. Add one only for a concrete runtime role. Apply
the native format's paths and layout after inspecting that format.

When placing or auditing any instruction document, agent-readable reference,
executable resource, output asset, or integration metadata, read
[Resource Layering](references/resource-layering.md). Route every required
resource from the body with its exact native path and use condition.

## Validate the Skill Contract

Review the Skill as a closed contract using only its name, description, body,
resources reachable on the selected path, explicitly declared dependencies,
verified invocation and authorization behavior affecting that path, and explicit
runtime guarantees. Do not supply missing rules, resources, permissions, or host
capabilities from general knowledge or author intent.

When reviewing a Skill or before calling an authored or revised Skill complete,
read [Skill Contract Validation](references/skill-contract-validation.md). Derive
cases from actual responsibility, selection, branch, resource, and stopping
edges. A walkthrough proves only that an ideal executor can derive a coherent
route. Claim model selection, model behavior, or runtime correctness only from
evidence collected on the named surface, model, or runtime.

If a reference required by the current path is missing, unreadable, or
case-mismatched, stop that path and report the exact blocker. An authoring or
revision task may return a draft only when it labels the affected review
incomplete.

## Report the Result

Before calling an authored or revised Skill complete, or closing a review,
resolve:

- grounding and evidence for source-dependent decisions;
- responsibility, stopping point, primary type, and cohesion boundary;
- canonical or explicitly provisional name and written selection contract;
- type-specific body behavior;
- each resource's runtime role and route;
- selection and contract cases that expose distinct decision edges; and
- the strongest conclusions supported by available evidence.

In read-only review, report each finding with the affected contract element, a
reachable request and state, the conflicting or unsupported behavior it permits,
the smallest correction boundary, and the evidence level. If no finding is
identified, state that result for the inspected scope and list conclusions that
remain unverified.

Record confirmed decisions in the artifact or review result owned by the host
task. Do not require fixed headings, serialized review fields, a universal case
count, or a total quality score.
