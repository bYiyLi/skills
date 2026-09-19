# Review Templates

Use these templates to keep review output stable and actionable.

## Full Review

```markdown
# Prompt / Skill Smell Review

## Verdict
approve / needs revision / reject

## Score
x / 100

## Reviewed Scope
- Reviewed:
- Not available:
- Assumptions:

## One-Vote Rejection Check
| Gate | Pass/Fail | Evidence |
|---|---|---|
| Trigger clarity |  |  |
| Scope boundary |  |  |
| Executable workflow |  |  |
| Output contract |  |  |
| Missing-input behavior |  |  |
| Failure handling |  |  |
| Permission boundary |  |  |
| Validation honesty |  |  |
| Safety compliance |  |  |
| Reproducibility |  |  |

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

## Quick Scan

```markdown
## Verdict
approve / needs revision / reject

## Top Bad Smells
1. **Smell** — evidence; impact; fix.
2. **Smell** — evidence; impact; fix.
3. **Smell** — evidence; impact; fix.

## Fastest Path to Improve
1.
2.
3.
```

## Repair Result

```markdown
## Before / After
- Previous verdict:
- New verdict:
- Previous score:
- New score:

## Changes Made
| Issue | Change | Why it fixes the smell |
|---|---|---|

## Remaining Risks
-

## Validation Performed
-

## Not Performed
-
```


## Bilingual Review Note

English and Chinese prompts are both in scope. Preserve quoted evidence in the original language. Chinese vague terms such as “专业、准确、全面、详细、高质量、友好、认真、深度” should be treated like English vague terms unless they are converted into observable actions, checks, or output requirements.
