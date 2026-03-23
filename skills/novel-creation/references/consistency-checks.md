# Consistency Checks

`check` 会把结果分成三层：

- `pending_by_stage`
  - 当前阶段允许不完整，但必须给出下一步。
- `review_required`
  - 需要人工确认或补齐，但不一定阻断整个工作区。
- `blocking`
  - 当前不能安全继续。

重点检查：

- `WORK.md` frontmatter 是否完整。
- `WORK.md` 是否包含 `设定索引` 和 `角色索引`。
- 索引链接是否越界、坏链、重复。
- `设定/` 与 `角色/` 里的真源是否都已登记。
- scene 结构字段是否缺失。
- continuity refs / payoff refs 是否失效。
- 前部连续 `ready` scenes 是否满足章节归档阈值。
- 归档树中的章节与卷引用是否一致。
