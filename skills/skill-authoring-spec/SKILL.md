---
name: skill-authoring-spec
description: Apply Agent Skill authoring rules to responsibility, selection, names, resource boundaries and validation. Use when creating, revising or reviewing a Skill; general instruction quality belongs to prompt-authoring-spec.
---

# Skill Authoring Spec

Guide the host's Skill authoring or review without taking over its deliverable.
Preserve read-only requests; naming a Skill does not authorize edits. Check
available sources before asking about a material ambiguity. Add only confirmed
rules that change a real authoring decision.

## Establish sources and authority

Ground rules and examples in applicable project sources, primary documentation,
representative artifacts/task traces, failure records or explicit user decisions.
A decision establishes policy only in its authority and scope; a trace proves
only observed behavior. External format or runtime guarantees need matching
primary evidence. Resolve conflicts by authority, scope and applicable version,
or preserve the unresolved conflict instead of inventing a mandatory rule.

This specification's normative rules are policy defined here, not evidence for
external formats or hosts. Every Skill needs a stable non-empty name, selection
description and post-selection instructions. Inspect the intended native format
for serialization, paths and metadata; when unavailable, review only this
semantic core and mark those format conclusions unverified.

A Skill may explain authorization boundaries but does not itself prove a user
has delegated actions. Preserve current task authority, protected actions and
host/tool approvals. Do not turn routine choices, internal checkpoints or Skill
transitions into new approval gates. A Skill's result returns to the host, which
continues the request's remaining authorized work.

## Define responsibility and selection

Determine the owned result and where responsibility ends. Read
[references/type-contracts.md](references/type-contracts.md) for responsibility,
primary type and body behavior. Choose one primary type from guidance, capability,
workflow or router; apply only that type's body rules. Internal resource routing
does not change an owned workflow or capability into a router.

Read [references/naming-and-selection.md](references/naming-and-selection.md)
when choosing or reviewing names, descriptions, prerequisites or sibling boundaries.
Use the actual target collection. The description identifies the responsibility
and when to select it, with prerequisites or sibling distinctions only when they
change selection. Put initial selection conditions there, not only in the body;
keep operation-specific checks and output detail after selection.

Names remain stable unless a demonstrated selection or responsibility defect
requires a change. Naming patterns are preferences for expressing the result,
not a reason for cosmetic migrations of valid existing names.

## Keep the package sufficient and small

Keep core decisions, shared invariants, resource routes and completion boundaries
in `SKILL.md`. Retain text only when its removal can cause a wrong choice, excess
side effect, incomplete result, false success or unnecessary resource load.
A short self-contained Skill needs no router or extra files.

Read [references/resource-layering.md](references/resource-layering.md) when
placing or auditing instructions, references, scripts, assets or metadata.
Add a resource only for an existing runtime role. Give every required resource
an exact conditional route: first-level routes belong in the body; a routed
reference may route deeper detail when that branch is only knowable there. Move
substantial conditional detail off the ordinary path; do not repeat its rules.

## Validate the closed contract

Read [references/skill-contract-validation.md](references/skill-contract-validation.md)
for review and before calling a creation or revision complete. Use only the name,
description, body, reachable resources, declared dependencies and verified
host/runtime behavior.
Do not fill gaps from author intent or assumed permissions/capabilities.

Include independently used invocation prompts and generated instruction templates.
Derive cases from distinct selection, responsibility, branch, resource, recovery
and stopping edges. An ideal walkthrough does not prove actual model behavior;
selection and runtime claims need evidence on the named model, host or tool.

Missing or case-mismatched required resources block only their dependent path.
Report the exact blocker and continue independent work. A draft with uncovered
required rules is not a fully reviewed or validated revision.

## Report supported conclusions

Resolve source grounding, responsibility/type, selection boundaries, resource
roles and routing, and meaningful contract cases. Report each finding with the
affected element, reachable request/state, allowed wrong behavior, minimal
correction and evidence level. With no finding, state the inspected scope and
unverified conclusions. Record decisions in the host-owned artifact or result;
no universal headings, serialized review fields, total score or case quota.
