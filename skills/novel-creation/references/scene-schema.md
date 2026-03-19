# Scene Schema

## Scene Block Layout

在 `正文创作区.md` 与章节归档文件中，使用如下结构:

````md
## scene-0001 场景标题
```yaml
scene_id: scene-0001
status: draft
pov: 林玄
time: 第一日-夜
location: 黑石城外
characters:
  - 林玄
  - 赵七
plotlines:
  - plot-main-bloodline
goal: 进入祖祠
outcome: 发现黑铁令异动
continuity_refs:
  - scene-0000
summary: >
  本场景的 2 到 4 句摘要。
beats:
  - 潜入城外乱葬岗
  - 黑铁令示警
new_facts:
  - id: fact-scene-0001-token
    subject: 黑铁令
    predicate: 指向
    object: 祖祠入口
state_changes:
  - entity: 林玄
    field: 对祖祠的认知
    from: 只知其名
    to: 知道入口与黑铁令相连
foreshadow:
  - id: hook-black-iron
    note: 黑铁令与祖祠血脉有关
payoff_refs: []
open_loops:
  - loop-ancestor-secret
```
正文:

这里写场景正文。
```
````

## Required Fields

必填顶层字段:

- `scene_id`
- `status`
- `pov`
- `time`
- `location`
- `characters`
- `plotlines`
- `goal`
- `outcome`
- `continuity_refs`
- `summary`
- `beats`
- `new_facts`
- `state_changes`
- `foreshadow`
- `payoff_refs`
- `open_loops`

## Status Semantics

- `draft`: 仍在创作中，不能归档。
- `ready`: 通过 ready 最低结构标准，可以参与章节归档。
- `hold`: 暂停，等待设定或上游剧情修复。

## Ready Minimum Standard

即使 prose 已经写出来，只要以下任一条件不满足，就不要把 `status` 改成 `ready`：

- 顶层必填字段仍有缺失、空值或明显占位内容。
- 正文仍是占位、提纲式备注，或明显还没把 beats 写成 scene。
- `beats` 没体现到正文里，或正文出现了主要动作但 beats 没同步。
- `summary` 不能稳定概括正文。
- 正文引入了新事实、新关系或状态变化，但 `new_facts` / `state_changes` / `foreshadow` / `open_loops` 没同步。

满足以下条件时，才适合把 `status` 改成 `ready`：

- 必填字段完整。
- 正文是可交接的完整 scene，而不是半成品说明。
- beats、summary、事实卡片与正文对齐。
- 后续 `retrieve` 和 `check` 可以依赖这些结构化字段工作。

## Optional Nested Fields

以下字段可选，但有助于 deterministic checks:

- `new_facts[].rule_refs`
- `state_changes[].reason`
- `foreshadow[].payoff_expectation`
- `open_loops[].owner`

## Authoring Rule

CLI 不负责从自由 prose 猜事实。场景里没有显式摘要、事实卡片或状态变化时，索引质量会显著下降，`check` 应提示修复。
