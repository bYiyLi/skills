# Requirements Doc Management Contract

如果目标仓库没有显式文档合同，软件需求文档默认按以下规则管理。

## Default Placement

1. requirements 真源默认放 `docs/requirements/`
2. 失效历史文档默认放 `docs/archive/requirements/`
3. 不要把正式需求长期放在 PR 描述、临时笔记或随机目录中

## Naming Rules

1. living requirement doc 使用稳定 slug：`<topic-slug>.md`
2. 时间点强相关的审阅稿或快照可用：`YYYY-MM-DD-<topic-slug>.md`
3. 不要使用 `final-v2.md` 这类文件名表达状态

## Required Metadata

需求文档 frontmatter 至少应包含：

```yaml
---
title:
doc_type: requirement
status: draft | active | approved | deprecated | archived
owner:
last_updated:
baseline:
source_of_truth: repo
related_designs:
supersedes:
superseded_by:
---
```

## Lifecycle Rules

1. 新建需求文档默认 `draft`
2. 当前工作基线使用 `active` 或 `approved`
3. 新需求文档替代旧版时，旧文档标 `deprecated`
4. 归档历史文档时，移动到 `docs/archive/requirements/` 并标 `archived`
5. 同主题同层级只保留一份 active 或 approved requirements 真源
