---
name: prompt-authoring-spec
description: Apply instruction-writing rules when authoring, revising or reviewing text intended to instruct a model. Covers semantic clarity, scope, authority and evidence; the host retains artifact delivery.
---

# Prompt Authoring Spec

Guide decisions inside the host task. A prompt is text intended to change model
selection, interpretation, action or evaluation, regardless of storage. Preserve
the requested mode: review reports findings; revision needs task authorization.
Naming this Skill alone does not authorize rewriting.

## Establish the behavioral contract

Locate the target and source requirements through current context and authorized
sources. Missing material blocks only dependent judgments; report the exact gap
rather than inventing text, facts or resources. A source-limited text review can
still proceed. Let the artifact's own specification govern its native semantics
and format; this Skill governs its model-visible instructions.

Resolve the observable condition, actor, action, available evidence and intended
result before drafting. This is a reasoning aid, not a required output schema.
Keep a sentence only when removing it changes a decision, action, permission,
output, recovery or evidence requirement.

- Specify a method or ordering only when alternatives change the required result
  or its evidence, authority, side effects or recovery. Preserve useful judgment.
- Distinguish requested output constraints from heuristics used to organize work.
  A part's label or local check does not by itself make it a separately governed
  result. Define units and precedence when confusing them changes the outcome.
- Identify necessary inputs and authority from available sources before asking.
  Only unresolved choices that materially affect the result need clarification;
  routine details and existing decisions do not need approval again.
- Handle reachable missing, invalid, conflicting, denied and post-start failure
  states when they change the result. Use observable behavior instead of demands
  for hidden effort, certainty or private reasoning.
- Define completion evidence and distinguish checkpoints from approval or task
  completion. Continue the authorized goal across progress questions and context
  recovery; revise it when the user changes scope or rejects an assumption.

When reviewing this specification itself, treat its normative rules as policy
under review, not proof of external host, format or runtime guarantees.

## Read only applicable references

| Decision being written or reviewed | Required reference |
| --- | --- |
| Wording, terms, requirement strength, prohibitions, bounds or branches | [references/executable-language.md](references/executable-language.md) |
| Context, history, examples, placeholders or variable data | [references/context-and-examples.md](references/context-and-examples.md) |
| Retrieved/quoted content, user variables or instruction precedence | [references/instruction-authority.md](references/instruction-authority.md) |
| Source-dependent claims, permissions, runtime behavior or completion evidence | [references/evidence-and-enforcement.md](references/evidence-and-enforcement.md) |
| Review, counterexamples, evaluation or final instruction validation | [references/prompt-contract-validation.md](references/prompt-contract-validation.md) |

A missing required reference blocks its path, not independent work. Report exact
paths and uncovered rules; do not call affected instructions complete or validated.

## Review the actual executor-facing text

Apply the closed-contract checks before completion. Include independently used
invocation prompts and output instruction templates; review notes cannot supply
rules absent from the text the executor receives. Resolve a demonstrated defect
with the smallest correction that preserves other valid behavior. Do not turn
this guidance into a mandatory template, scenario quota, score or new workflow.

Report findings with location, reachable request/state, permitted wrong behavior,
minimal correction and evidence level. Keep source checks, text review, scenario
walkthrough, independent model evaluation and runtime validation distinct.
Fewer words alone do not demonstrate better model behavior; require controlled
evaluation before claiming a phrase causally improves it. The host owns artifact
changes, validation execution and final delivery.
