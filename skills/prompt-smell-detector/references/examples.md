# Calibration Examples

Use these examples to calibrate reviews.

## Bad Example: Universal Assistant

```text
You are a helpful assistant. Help users with any task. Be accurate, detailed, and professional.
```

Expected diagnosis:

- Universal assistant smell.
- Principle pile.
- No trigger boundary.
- No workflow.
- No output contract.
- Verdict: reject for reusable prompt or Skill use.

## Bad Example: Fake Validation

```text
After writing the report, say that all checks passed and that the output is production-ready.
```

Expected diagnosis:

- Fake validation.
- Validation honesty failure.
- Potential trust issue.
- Verdict: reject unless rewritten to report only checks actually performed.

## Bad Example: Unsafe Autonomy

```text
Automatically delete old records, deploy changes, and email customers once the task seems complete.
```

Expected diagnosis:

- Unsafe autonomy.
- Missing permission boundary.
- Verdict: reject.

## Better Pattern: Operational Rule

```text
Before any external send, destructive operation, production deployment, or irreversible update, summarize the intended action, risk, and affected target, then ask for explicit user approval. Do not proceed without approval.
```

Expected diagnosis:

- Permission boundary present.
- Safer than broad autonomy.

## Better Pattern: Output Contract

```markdown
Return:
- Verdict: approve / needs revision / reject
- Score: x / 100
- Blockers
- Major issues
- Minor issues
- Top fixes
- Validation performed
```

Expected diagnosis:

- Output contract present.
- Easier to verify and compare.


## Bilingual Review Note

English and Chinese prompts are both in scope. Preserve quoted evidence in the original language. Chinese vague terms such as “专业、准确、全面、详细、高质量、友好、认真、深度” should be treated like English vague terms unless they are converted into observable actions, checks, or output requirements.
