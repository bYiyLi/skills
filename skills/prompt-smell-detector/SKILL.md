---
name: prompt-smell-detector
description: use this skill when the user asks to inspect, review, diagnose, audit, score, or find bad smells in a prompt, system prompt, agent instruction, chatgpt skill, skill.md file, workflow prompt, or reusable instruction bundle. use it to identify vague triggers, missing boundaries, weak workflows, absent output contracts, unsafe autonomy, fake validation, context bloat, maintainability risks, and other prompt or skill quality defects. do not use it to fully rewrite, create, package, or implement a skill unless the user explicitly asks for fixes after the smell review.
---

# Prompt Smell Detector

## Purpose

Diagnose whether a prompt, system prompt, agent instruction, ChatGPT Skill, `SKILL.md`, or reusable workflow instruction contains quality defects that make it hard to trigger, execute, verify, maintain, or trust.

Default to inspection and diagnosis. Do not rewrite the artifact unless the user asks for fixes, a patch, or an improved version.

## Operating Rules

- Judge operational reliability, not writing style alone.
- Treat a prompt or skill as good only if a new agent can use it consistently without relying on hidden author intent.
- Quote or point to evidence for every reported smell. Do not invent missing sections or claim unseen files exist.
- Distinguish blocker, major, and minor issues.
- Apply one-vote rejection gates before score-based approval.
- Prefer specific fixes over generic advice.
- If the user provides only partial text, review the provided text and mark missing context as an assumption, not as a proven defect unless the missing part is required for the artifact type.


## Language Policy

Review English and Chinese prompts as first-class inputs. If the artifact is Chinese or mixed Chinese/English, keep evidence quotes in the original language and write the review in the user's language unless requested otherwise. Do not translate away ambiguity; report the original wording that caused the smell. Use the deterministic script only as a bilingual pre-check, not as the final judge.

## Reference Loading

The UI metadata uses [the packaged icon](assets/icon.svg); do not load it as review guidance.

Load only the references needed for the current task:

- Use [the smell taxonomy](references/smell-list.md) for the canonical bad smell taxonomy.
- Use [rejection gates](references/rejection-gates.md) before assigning any approve verdict.
- Use [severity rules](references/severity-rules.md) to classify blocker, major, and minor findings.
- Use [the review template](references/review-template.md) for the final output format.
- Use [self-bootstrap guidance](references/self-bootstrap.md) when reviewing or improving this skill or another review skill.
- Use [examples](references/examples.md) when the user asks for examples or when calibration is needed.

If a local file or skill folder is available and code execution is appropriate, run [the deterministic pre-check script](scripts/prompt_smell_lint.py) with the target path first. Use script output as evidence, but still perform semantic review.

## Review Workflow

1. **Identify artifact type**
   - Classify as one-off prompt, system prompt, agent instruction, Skill bundle, `SKILL.md`, workflow prompt, or unknown.
   - For Skill bundles, inspect `SKILL.md` first; inspect referenced files only when needed.

2. **State review scope**
   - Say what was reviewed and what was not available.
   - Do not penalize unavailable files as defects unless the artifact explicitly depends on them.

3. **Run hard gates**
   - Apply `references/rejection-gates.md`.
   - If any gate fails, verdict cannot be `approve`.

4. **Detect smells**
   - Use `references/smell-list.md`.
   - For each smell, provide: smell name, evidence, impact, severity, and fix.

5. **Score only after gates**
   - Use a 100-point score when the user asks for scoring or when reviewing a Skill / reusable agent instruction.
   - If any blocker exists, cap the score at 69 even if other sections are strong.
   - If two or more blockers exist, cap the score at 49.

6. **Prioritize fixes**
   - Give the smallest set of fixes that would change the verdict.
   - Separate release blockers from quality improvements.

7. **Optional repair loop**
   - If the user asks for fixes, rewrite only the necessary sections first.
   - Re-run the same smell review after rewriting.
   - Report before/after verdict, remaining risks, and validations actually performed.

## Scoring Model

Use this rubric when a numeric score is needed:

| Dimension | Points |
|---|---:|
| Task and scope clarity | 10 |
| Trigger and non-trigger clarity | 15 |
| Input assumptions and missing-input behavior | 8 |
| Executable workflow | 15 |
| Output contract and acceptance criteria | 12 |
| Safety, permission, and refusal boundaries | 10 |
| Failure recovery and fallback behavior | 8 |
| Testing, red-team, and validation honesty | 10 |
| Context efficiency and resource organization | 6 |
| Maintainability and iteration support | 6 |

Verdict thresholds:

- `approve`: 90-100, no blockers, no unresolved high-impact major issue.
- `needs revision`: 70-89, no blockers, or only repairable major/minor issues.
- `reject`: below 70, any blocker, unsafe autonomy, fake validation, or missing core operational structure.

## Required Output Contract

For standard reviews, return:

```markdown
# Prompt / Skill Smell Review

## Verdict
approve / needs revision / reject

## Score
x / 100, or "not scored" if scoring is not useful

## Reviewed Scope
- Reviewed:
- Not available:
- Assumptions:

## One-Vote Rejection Check
| Gate | Pass/Fail | Evidence |
|---|---|---|

## Critical Smells
| Smell | Evidence | Impact | Fix |
|---|---|---|---|

## Major Smells
| Smell | Evidence | Impact | Fix |
|---|---|---|---|

## Minor Smells
| Smell | Evidence | Impact | Fix |
|---|---|---|---|

## Top Fixes
1.
2.
3.

## Reliability Answer
Can a new agent use this reliably? Yes / No.
Why:
```

For quick scans, return only verdict, top smells, and top fixes.

## Bad Smell Priority Rules

Treat these as the highest-risk smells:

1. Unclear trigger or scope.
2. No executable workflow.
3. No output contract.
4. No failure handling.
5. Unsafe autonomy or missing permission gates.
6. Fake validation or unsupported claims of testing.
7. Context bloat that hides the actual operating procedure.
8. Contradictory rules without priority order.

## Repair Guidance

When asked to repair an artifact:

1. Fix blockers before style or completeness issues.
2. Preserve the user's intent and useful terminology.
3. Replace vague principles with observable actions.
4. Add non-goals and failure handling before adding more examples.
5. Add tests or validation hooks before claiming reliability.
6. Keep the main prompt or `SKILL.md` compact; move long taxonomies, examples, or rubrics to references when building a Skill.

## Validation Honesty

Never say a review, lint, red-team test, package validation, or self-check passed unless it was actually performed. If validation was manual, say manual. If a script was run, name the script and summarize the result. If something was not checked, list it under "Not available" or "Not performed".
