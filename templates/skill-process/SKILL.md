---
name: your-skill-name
description: >
  用中文先说明这个流程类 skill 覆盖什么重复流程,
  在什么情况下应触发,
  再补必要的 English keywords.
license: ./LICENSE.txt
metadata:
  owner: your-name
  status: draft
  last-reviewed: 2026-03-19
  skill-type: process
---

# Task Fit

说明:

1. 哪类重复流程应该触发这个 skill。
2. 哪些相邻但不属于该流程的任务不该触发。
3. 这个流程的起点和终点分别是什么。

## Resources to Load

说明在什么条件下读取:

- `references/` 中的流程细节和决策依据。
- `scripts/` 中的自动化步骤。
- `assets/` 中的交付模板或清单。

## Inputs

列出进入流程前必须具备的输入:

- 必要上下文、素材、数据或权限。
- 缺失输入时是补齐、暂停还是升级。

## Workflow

按顺序写清阶段步骤。至少说明:

1. 每个阶段的目标。
2. 每个阶段的核心动作。
3. 阶段之间的进入和退出条件。

## Branches

列出关键分支:

- 什么时候走正常路径。
- 什么时候回退、重试或升级。
- 哪些条件会导致流程终止。

## Quality Gates

说明每个关键 gate 的通过标准。

## Done Definition

说明做到什么算真正完成，而不是“做了一些事”。

## Handoff

说明结束时要交付什么:

- 文件、摘要、状态说明、待办或下一步建议。

## Output Standard

说明最终输出至少要体现:

- 当前处于流程的哪个结果状态。
- 哪些 gate 已通过或未通过。
- 交付物是否齐全。

## Stop Conditions

说明什么时候应暂停、回退或升级，例如:

- 输入长期缺失。
- 关键 gate 无法通过。
- 当前请求超出该流程边界。

## Minimal Examples

至少给出:

1. 1 个应触发的流程执行示例。
2. 1 个应暂停、回退或升级的边界示例。
