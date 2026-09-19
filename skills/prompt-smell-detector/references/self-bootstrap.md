# Self-Bootstrap Protocol

Use this protocol when reviewing or improving this skill or another smell-review skill.

## Goal

A review skill must be stricter on itself than on ordinary prompts. It must prove that it can detect the bad smells it claims to detect.

## Bootstrap Loop

Repeat until all release gates pass:

1. Review the skill's own `SKILL.md` and referenced files.
2. Run deterministic lint if local files are available.
3. Apply one-vote rejection gates.
4. Score using the 100-point model.
5. Identify blockers first, then major issues, then minor issues.
6. Patch the smallest set of files that removes blockers and major issues.
7. Re-run the same review.
8. Test against at least one intentionally bad prompt or bad Skill.
9. Record what was validated and what was not.

## Release Gates for This Skill

This skill can be considered release-ready only if:

- It has clear trigger and non-trigger conditions.
- It defaults to diagnosis, not unsolicited rewriting.
- It has a stable output contract.
- It contains a canonical smell taxonomy.
- It contains one-vote rejection gates.
- It contains severity rules.
- It contains validation honesty rules.
- It can reject an intentionally bad prompt.
- It can identify its own remaining limitations.

## Bad Sample Calibration

Use this prompt as a minimum bad-case test:

```markdown
---
name: helpful-writer
description: helps users write better.
---

# Helpful Writer

Be professional, accurate, detailed, and helpful. Think carefully and provide the best answer. If something is wrong, improve it.
```

Expected result:

- Verdict: reject.
- Blockers: unclear trigger, no workflow, no output contract, no failure handling.
- Major smells: principle pile, universal assistant smell, no validation, no non-goals.

If a review skill approves this sample, the review skill is not ready.


## Bilingual Review Note

English and Chinese prompts are both in scope. Preserve quoted evidence in the original language. Chinese vague terms such as “专业、准确、全面、详细、高质量、友好、认真、深度” should be treated like English vague terms unless they are converted into observable actions, checks, or output requirements.
