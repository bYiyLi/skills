---
name: methodology-journal
description: Use when the user wants Codex to record, preserve, refine, or reuse an excellent design method, engineering principle, collaboration pattern, decision heuristic, or project-specific methodology for future work. Triggers include "整理出一个方法论", "保存这个经验", "记录优秀方法论", "我们一起成长", "以后参考这个设计", and requests to turn a successful discussion or design decision into reusable guidance.
---

# Methodology Journal

Use this skill to turn a strong design discussion or engineering decision into reusable methodology for future Codex work.

## Workflow

1. Name the method in one short phrase.
2. State the problem pattern it solves.
3. Extract the core principle.
4. Write when to use it and when not to use it.
5. Convert it into repeatable steps.
6. Add a concrete example from the originating discussion.
7. Add a checklist for future use.
8. Store detailed methods under `references/`.
9. If a method becomes broadly useful, create a dedicated skill for it.

## Method Entry Template

Use this format when adding a new method:

```markdown
# Method Name

## Problem Pattern

What repeated design or engineering problem this method solves.

## Core Principle

One sentence.

## Use When

- ...

## Do Not Use When

- ...

## Steps

1. ...
2. ...
3. ...

## Example

Concrete before/after from the project.

## Checklist

- [ ] ...
```

## Existing Methods

Read [Unified Object Design](references/unified-object-design.md) only when that method is relevant.

## Recording Rules

Keep methods practical and reusable.

Do not record vague slogans. Record decision criteria, steps, examples, and failure modes.

Prefer one method per reference file. Use lowercase hyphen-case filenames.

If the user asks to preserve a method globally, write it under this skill unless they ask for a separate dedicated skill.
