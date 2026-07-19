---
name: prompt-authoring-spec
description: >
  Use when authoring, revising, or reviewing text that a model will interpret as
  instructions, regardless of where the text is stored or delivered. Apply this
  specification's rules for necessary, scoped, executable, and evidence-grounded
  instructions while the host task retains ownership of the artifact, execution,
  and delivery.
---

# Prompt Authoring Spec

Use this Skill as the canonical source for model-visible instruction design. A
prompt is text intended to change a model's selection, interpretation, judgment,
action, or evaluation behavior, regardless of storage or delivery.

Apply this guidance inside the host authoring, revision, or review task. Leave
the artifact, execution, runtime evaluation, and delivery with that host task.
Preserve the requested mode: a read-only review reports findings without
rewriting the artifact; revise only when the user requests revision.

Invoking this Skill does not select a mode. If the requested result does not
distinguish authoring, revision, or read-only review, ask which result the user
wants before writing, rewriting, or reviewing.

Before authoring, require requested behavior or source requirements that
determine the target instructions. Before revision or review, require the target
instructions in context or at an accessible path. If required input is missing
or unreadable, request it and stop until supplied.

Let an artifact-specific specification govern native format and semantics. Apply
this specification only to the model-visible instructions in that artifact. Do
not turn it into a universal template, fixed rewriting workflow, scenario
catalog, scoring system, registry, or deployment process.

When reviewing this Skill itself, treat its normative writing rules as the
policy under review. Verify claims about external formats, hosts, tools, and
current behavior separately.

## Define the Behavioral Contract

State the intended change before drafting prose:

~~~text
When <observable condition>, <actor> <must/should/may> <behavior>
instead of <plausible wrong behavior>, using <available evidence>.
~~~

Use this as a reasoning aid, not a required output template. Resolve only parts
that change the instruction. Delete a sentence when removing it changes no
selection, interpretation, judgment, action, evaluation, or evidence requirement.

- Specify a method only when alternatives change the required result, evidence,
  authorization, side effects, ordering, reproducibility, or recovery.
- Preserve judgment when several behaviors remain valid. Precision resolves
  ambiguity that changes a decision; it does not remove useful discretion.
- Identify the recipient or intended use only when it changes terminology,
  depth, tone, or output form.
- Identify each required input, capability, and authority. Treat it as missing
  unless supplied or guaranteed by the host contract.
- Define behavior for reachable missing, invalid, conflicting, unavailable,
  denied, and post-start failure states when they change the result.
- Add a rule only when the executor or host task owns the behavior and omission
  can cause failure within the prompt's declared scope.
- Use observable actions, choices, checks, outputs, and evidence. Do not replace
  them with hidden-effort instructions such as think deeply, be certain, or take
  your time.
- State a stopping point or completion evidence when the instruction governs
  progression or a completion claim.

## Load Only Applicable Rules

Read [Executable Language](references/executable-language.md) when authoring or
reviewing wording, terminology, requirement strength, prohibitions, sets,
quantitative bounds, branches, or structure.

Read [Context and Examples](references/context-and-examples.md) when the prompt
contains or needs source context, history, examples, placeholders, variable
input, or illustrative data.

Read [Instruction and Data Authority](references/instruction-authority.md) when
the prompt consumes user-controlled variables, quoted or retrieved content, tool
results, prior model output, or multiple instruction authority levels.

Read [Evidence and Enforcement](references/evidence-and-enforcement.md) when the
prompt asserts source-dependent rules or current facts, depends on host or
runtime behavior, governs permissions or side effects, defines completion
evidence, or specifies an evaluation.

Read [Prompt Contract Validation](references/prompt-contract-validation.md) when
reviewing instructions, deriving counterexamples, or making claims about prompt
quality, model behavior, or runtime correctness. Before the host calls authored
or revised instructions complete, apply its closed-contract review to the final
text the executor will receive.

A routed reference is required only on its stated path. If a required reference
is missing, unreadable, or case-mismatched, stop that path and report the exact
blocker. An authoring or revision task may return a draft only when it labels the
affected review incomplete; do not call the prompt complete or validated.
