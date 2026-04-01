# Design Doc Management Contract

如果目标仓库没有显式文档合同，软件设计文档默认按以下规则管理。

## Default Placement

1. design 真源默认放 `docs/design/`
2. ADR 默认放 `docs/adr/`
3. 失效历史文档默认放 `docs/archive/design/`
4. 不要把长期设计基线留在 PR 描述、白板截图说明或随机笔记里

## Naming Rules

1. living design doc 使用稳定 slug：`<topic-slug>.md`
2. 时间点强相关的快照、迁移计划或评审稿可用：`YYYY-MM-DD-<topic-slug>.md`
3. 不要使用 `final-v2.md` 这类文件名表达状态

## Required Metadata

设计文档 frontmatter 至少应包含：

```yaml
---
title:
doc_type: design
status: draft | active | approved | deprecated | archived
owner:
last_updated:
baseline:
source_of_truth: repo
related_requirements:
related_adrs:
supersedes:
superseded_by:
---
```

## Lifecycle Rules

1. 新建设计文档默认 `draft`
2. 当前工作基线使用 `active` 或 `approved`
3. 新设计替代旧版时，旧文档标 `deprecated`
4. 归档历史文档时，移动到 `docs/archive/design/` 并标 `archived`
5. 同主题同层级只保留一份 active 或 approved design 真源
