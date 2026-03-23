# WORK Contract

`WORK.md` 固定分两部分：

## Frontmatter

至少包含：

- `stage`
- `current_task_type`
- `current_scope`
- `current_scene`
- `current_chapter`
- `current_volume`
- `blockers`
- `next_step`

## Body

固定章节：

- `Current Focus`
- `Blockers`
- `Next Step`
- `设定索引`
- `角色索引`

约束：

- 程序读取 frontmatter 状态字段。
- 程序读取 `设定索引` 与 `角色索引` 的 Markdown links。
- `设定索引` 只登记 `设定/*.md`。
- `角色索引` 只登记 `角色/*.md`。
- 索引坏链、重复、越界或漏登记都会在 `check` 中暴露。
