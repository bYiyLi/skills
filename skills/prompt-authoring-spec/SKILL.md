---
name: prompt-authoring-spec
description: Guide the design, writing and review of prompts, AGENTS and Skill instructions. Covers necessity, ownership, executable wording and validation; the host owns delivery.
---

# Prompt Authoring Spec

Guide decisions within the requested task; the host owns edits, tests and delivery.
Discussion returns analysis, review-only returns findings, and revision permits
in-scope fixes. Selecting this Skill grants no additional authority.

## Decide what belongs

For a concrete instruction task, establish purpose, requirements and executor
context from the request and authorized sources. An existing draft is material
to assess, not authority for its own rules. Do not demand a draft or separate
requirements document when the request supplies what is needed. For discussion,
resolve only details needed for the question. Investigate consequential unknowns
before asking; missing evidence blocks only dependent work.

Before polishing a candidate rule, decide:

- **Need:** What required decision or result would be lost without it? Delete it
  if its removal permits no concrete in-scope error and loses no requirement.
- **Owner:** Does this instruction unit own that decision? Use the target's actual
  responsibilities, not its filename, an analogy or where a symptom appeared.
  Relocate misplaced guidance within authorized scope; otherwise propose the move.
- **Basis:** What supports the requirement or suspected cause? A failed outcome
  does not establish its cause; a useful remedy does not establish a mandatory
  method. Keep unverified causal explanations as hypotheses.
- **Action:** Can the executor identify the condition and use the required inputs
  and capabilities at that point? Handle a missing dependency without inventing
  an alternative or silently discarding the required boundary.

## Write, then remove what adds no decision

State outcomes and boundaries directly. Require a method or order only when the
task selects it or a supported failure mechanism makes it necessary. Preserve
other valid approaches; one failure does not justify a whole new workflow.

Use familiar words and precise verbs. Replace vague exhortations with the actual
condition or action. Remove repeated rules, ornamental roles and explanations
that leave the required decision unchanged. Do not shorten away conditions,
exceptions or needed context. Useful density is not minimum word count.

## Load the applicable checks

Read these references before the corresponding work; paths are relative to this Skill.

| Work | Reference |
| --- | --- |
| Wording, terms, strength, prohibitions, sets or branches | [references/executable-language.md](references/executable-language.md) |
| Context, explanations, examples or variables | [references/context-and-examples.md](references/context-and-examples.md) |
| Instruction priority, permissions or untrusted data | [references/instruction-authority.md](references/instruction-authority.md) |
| Source claims, causal reasoning or runtime guarantees | [references/evidence-and-enforcement.md](references/evidence-and-enforcement.md) |
| Reviewing or delivering instructions, self-review or behavior claims | [references/prompt-contract-validation.md](references/prompt-contract-validation.md) |

If a required reference is unreadable, report its path and the uncovered check.
Before delivering instructions, apply the validation reference to the text the
executor will actually receive. Return the requested result; include an authoring
checklist only when requested. When this Skill is revised, apply that reference's
self-review to the whole package, including its invocation text.
