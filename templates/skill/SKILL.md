---
name: your-skill-name
description: >
  用中文先说明这个 skill 做什么,
  在什么情况下触发,
  再补必要的 English keywords.
license: ./LICENSE.txt
metadata:
  owner: your-name
  status: draft
  last-reviewed: 2026-03-19
  skill-type: choose-normative-tooling-or-process
---

# Goal

说明这个 skill 要帮助另一个 agent 完成什么重复任务。

## Type Selection

- 在提交正式 skill 前，把 `metadata.skill-type` 改成 `normative`、`tooling`、`process` 之一。
- 如果类型已经明确，优先改用对应模板:
  - `templates/skill-normative/`
  - `templates/skill-tooling/`
  - `templates/skill-process/`

## Shared Sections

以下章节是所有正式 skill 的共享合同，标题保持英文，正文可以中文为主。

## Task Fit

说明哪些请求应该触发、哪些相邻请求不该触发。

## Resources to Load

说明在什么条件下需要读取 `references/`、`scripts/`、`assets/`。

## Output Standard

说明最终结果要满足哪些可观察质量标准。

## Stop Conditions

说明什么时候要中止、升级、回退或拒绝继续。

## Minimal Examples

至少给出:

1. 1 个会触发的最小示例。
2. 1 个不该触发或需要升级的边界示例。
