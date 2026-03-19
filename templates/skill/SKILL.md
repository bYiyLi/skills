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
---

# Goal

说明这个 skill 要帮助另一个 agent 完成什么重复任务。

## Workflow

1. 先说明如何判断任务是否匹配这个 skill。

2. 再说明完成任务的标准流程。

3. 如果有脚本、资料或模板，明确写出读取条件。

## Guardrails

- 说明什么时候不该用这个 skill。

- 说明哪些行为会损害结果质量或浪费上下文。

- 长说明移动到 `references/`，不要全部塞进主文件。

## Minimal Example

给出 1-2 个最小示例，帮助另一个 agent 快速上手。
