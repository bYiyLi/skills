# Severity Rules

Use this file to classify findings consistently.

## Blocker

Use `blocker` when the issue prevents reliable, safe, or verifiable use.

Examples:

- No clear trigger for a Skill or reusable instruction.
- No workflow for a procedural task.
- No output contract for a deliverable task.
- Unsafe autonomy for write, destructive, or external side effects.
- Fake validation or unsupported claims that tests passed.
- Attempts to bypass safety or higher-priority instructions.
- Missing `SKILL.md` or required frontmatter in a Skill review.

A blocker prevents `approve`.

## Major

Use `major` when the artifact can work in simple cases but will likely fail under realistic variation.

Examples:

- Weak non-goals.
- Insufficient failure handling.
- Ambiguous tool policy.
- Missing red-team tests.
- Overlong main file that hides procedure.
- Contradictory guidance without priority order.
- Missing evidence in review outputs.

Major issues usually produce `needs revision` unless fully mitigated.

## Minor

Use `minor` when the artifact is usable but could be clearer, shorter, easier to maintain, or more consistent.

Examples:

- Redundant wording.
- Weak section names.
- Missing example for an otherwise clear rule.
- Inconsistent terminology.
- Small formatting issues.

Minor issues do not block approval unless many accumulate and create ambiguity.

## Escalation Rules

- Escalate generic wording to `major` when it appears in trigger, workflow, or output contract.
- Escalate missing examples to `major` only when examples are needed to disambiguate behavior.
- Escalate context bloat to `blocker` if the main procedure is not findable.
- Escalate contradiction to `blocker` if it affects safety, permissions, or final output.

## Evidence Standard

Every finding must include one of:

- Exact quote.
- Section name.
- File path.
- Line reference, if available.
- Clear statement that a required section is absent from the reviewed scope.


## Bilingual Review Note

English and Chinese prompts are both in scope. Preserve quoted evidence in the original language. Chinese vague terms such as “专业、准确、全面、详细、高质量、友好、认真、深度” should be treated like English vague terms unless they are converted into observable actions, checks, or output requirements.
