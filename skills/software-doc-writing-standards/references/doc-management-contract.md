# Software Doc Management Contract

这份合同定义软件文档在仓库中的默认存放、命名、状态、追溯和归档规则。

如果目标仓库已经有显式文档合同，优先遵守目标仓库的合同；只有在目标仓库没有明确规则时，才使用本合同作为默认标准。

## Default Layout

默认目录如下：

```text
docs/
  requirements/
  design/
  usage/
    tutorials/
    how-to/
    operators/
  reference/
  adr/
  archive/
    requirements/
    design/
    usage/
    reference/
    adr/
```

## Canonical Source Rules

1. 仓库内文档文件才是 authoritative source。
2. PR 描述、聊天记录、工单评论、会议纪要不算真源，除非内容已同步回仓库文档。
3. 每个 topic 在每种 doc type 下只保留一份 active 或 approved 的 canonical 文档。
4. 发现同主题多份平行文档时，必须显式指定哪份是当前真源，其他文档降级为 deprecated 或 archived。

## Naming Rules

1. 长期维护的 living document 使用稳定 slug：`<topic-slug>.md`
2. 时间点强相关的提案、评审纪要、快照或迁移计划使用日期前缀：`YYYY-MM-DD-<topic-slug>.md`
3. 不要使用 `final.md`、`final-v2.md`、`new-final-final.md` 这类命名。
4. 被替代的文档不要靠文件名后缀硬区分版本，优先用 metadata 和 `supersedes / superseded_by` 表达。

## Required Metadata

建议所有正式软件文档在 frontmatter 中至少写：

```yaml
---
title: <doc title>
doc_type: requirement | design | tutorial | how-to | operator-guide | reference | adr
status: draft | active | approved | deprecated | archived
owner: <team-or-person>
last_updated: YYYY-MM-DD
baseline: <release-branch-version-or-milestone>
source_of_truth: repo
---
```

建议按需补充：

```yaml
audience:
related_requirements:
related_designs:
related_reference:
related_adrs:
supersedes:
superseded_by:
review_cycle:
```

## Lifecycle Rules

1. 新文档默认以 `draft` 状态进入 canonical 目录。
2. 文档成为团队当前工作基线时，提升为 `active` 或 `approved`。
3. 新文档替代旧文档时，旧文档标记为 `deprecated`，并维护 `supersedes / superseded_by`。
4. 不再作为当前基线使用、但需保留历史追溯性时，移动到 `docs/archive/<category>/` 并标记 `archived`。
5. 已被代码、发布说明、测试计划或外部流程引用的正式文档，不要静默删除。

## Cross-Link Rules

1. requirement 应链接相关 design、reference 或 acceptance 入口。
2. design 应链接相关 requirement、ADR、migration 或 rollout 入口。
3. usage/how-to 应链接相关 reference 和版本基线。
4. reference 应链接相关 how-to、usage 或 design caveat，而不是孤立存在。

## Repository Hygiene Rules

每次创建、修改或评审软件文档时，都要明确：

1. 文档保存路径
2. 新建还是更新
3. 当前状态
4. 当前真源
5. 是否替代旧文档
6. 相关文档是否需要一起更新
