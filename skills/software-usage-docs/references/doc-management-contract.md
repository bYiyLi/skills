# Usage Doc Management Contract

如果目标仓库没有显式文档合同，软件使用说明文档默认按以下规则管理。

## Default Placement

1. tutorial 默认放 `docs/usage/tutorials/`
2. how-to / user guide 默认放 `docs/usage/how-to/`
3. operator guide / runbook 默认放 `docs/usage/operators/`
4. API/CLI/reference 默认放 `docs/reference/`
5. 失效历史文档默认放 `docs/archive/usage/` 或 `docs/archive/reference/`

## Naming Rules

1. living usage/reference doc 使用稳定 slug：`<topic-slug>.md`
2. 时间点强相关的迁移提醒、版本快照或评审稿可用：`YYYY-MM-DD-<topic-slug>.md`
3. 不要使用 `final-v2.md` 这类文件名表达状态

## Required Metadata

使用说明文档 frontmatter 至少应包含：

```yaml
---
title:
doc_type: tutorial | how-to | operator-guide | reference
status: draft | active | approved | deprecated | archived
owner:
last_updated:
baseline:
source_of_truth: repo
related_reference:
supersedes:
superseded_by:
---
```

## Lifecycle Rules

1. 新文档默认 `draft`
2. 当前工作基线使用 `active` 或 `approved`
3. 新文档替代旧版时，旧文档标 `deprecated`
4. 归档历史文档时，移动到对应 `docs/archive/` 子目录并标 `archived`
5. 同主题同类型只保留一份 active 或 approved 真源
