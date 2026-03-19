---
name: your-skill-name
description: >
  用中文先说明这个规范类 skill 管什么,
  在什么情况下应触发,
  再补必要的 English keywords.
license: ./LICENSE.txt
metadata:
  owner: your-name
  status: draft
  last-reviewed: 2026-03-19
  skill-type: normative
---

# Task Fit

说明:

1. 哪类请求应该触发这个规范类 skill。
2. 哪些相邻任务不该触发。
3. 触发时最关键的判断对象是什么。

## Resources to Load

说明在什么条件下读取规范资料:

- 什么时候读 `references/` 中的详细规则。
- 什么时候只用主文件中的核心规则即可。
- 如果存在多个规范来源，什么时候需要交叉检查。

## Decision Rules

按优先级列出规则，不要只列平级 bullet。至少说明:

1. 哪些是硬约束。
2. 哪些是偏好或建议。
3. 遇到证据不足时默认怎么处理。

## Exceptions

列出不适用范围、例外条件和边界情况。

## Conflict Resolution

说明:

1. 多条规则冲突时先采用哪一条。
2. 规范正文与示例冲突时如何处理。
3. 无法裁决时是升级、保守处理，还是明确标记不确定。

## Output Standard

说明最终输出应该做到什么:

- 结论能对应到具体规则或规则组。
- 命中例外时能明确指出。
- 不能判断时不编造新规则。

## Stop Conditions

说明什么时候应停止并升级，例如:

- 现有规范无法覆盖当前情况。
- 请求需要新增规范而不是应用规范。
- 规则冲突且仓库内没有裁决依据。

## Minimal Examples

至少给出:

1. 1 个应触发的规范判断示例。
2. 1 个不应触发或应升级的边界示例。
