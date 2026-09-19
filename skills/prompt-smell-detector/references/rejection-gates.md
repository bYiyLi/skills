# One-Vote Rejection Gates

Apply these gates before assigning any approve verdict.

A prompt, agent instruction, or Skill must be rejected or marked `needs revision` if any gate fails.

## Gate Checklist

| Gate | Fail condition | Minimum fix |
|---|---|---|
| Trigger clarity | User or agent cannot tell when to use it | Add exact trigger and non-trigger conditions |
| Scope boundary | The artifact can expand into unrelated tasks | Add scope, non-goals, and handoff rules |
| Executable workflow | It has principles but no steps or decision logic | Add workflow with entry/exit conditions |
| Output contract | Final output is not defined | Add required sections, schema, or acceptance format |
| Missing-input behavior | It does not say what to do when inputs are incomplete | Add clarify/assume/defer rules |
| Failure handling | It does not handle tool failure, unavailable files, validation failure, or unsupported requests | Add fallback and revision behavior |
| Permission boundary | It allows write/destructive/external actions without confirmation | Add explicit confirmation gates |
| Validation honesty | It claims tests or validation without evidence | Require named validations and "not performed" list |
| Safety compliance | It asks to bypass higher-priority rules, hide unsafe behavior, or perform harmful actions | Remove unsafe instructions and add refusal/handoff behavior |
| Reproducibility | A new agent could not reliably use it without hidden context | Add assumptions, workflow, and acceptance criteria |

## Verdict Rules

- If any safety compliance or unsafe autonomy gate fails, verdict is `reject`.
- If two or more core structure gates fail, verdict is `reject`.
- If exactly one repairable core structure gate fails, verdict is at best `needs revision`.
- If no gates fail but several major smells remain, verdict is `needs revision`.
- `approve` requires all gates to pass.

## Core Structure Gates

The core structure gates are:

1. Trigger clarity.
2. Scope boundary.
3. Executable workflow.
4. Output contract.
5. Missing-input behavior.
6. Failure handling.

A reusable prompt or Skill missing any two of these is not production-grade.


## Bilingual Review Note

English and Chinese prompts are both in scope. Preserve quoted evidence in the original language. Chinese vague terms such as “专业、准确、全面、详细、高质量、友好、认真、深度” should be treated like English vague terms unless they are converted into observable actions, checks, or output requirements.
