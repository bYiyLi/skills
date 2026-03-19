# Retrieval Views

## Goal

优先给 agent “最小足够材料”，不要返回整章整卷全文。

## Typed Retrieval

### `retrieve text`

- 用于按关键词、短语、正文摘要检索场景、章节、卷。
- 默认优先返回 `summary`、相关正文片段和来源定位。

### `retrieve entity`

- 用于角色、地点、势力、物件。
- 返回实体卡、最近出场场景、关系边、相关情节线。

### `retrieve timeline`

- 用于按故事内时间、实体、情节线查看事件顺序。
- 返回按 `time` 排序的场景或状态变化记录。

### `retrieve plotline`

- 用于主线、支线、伏笔、回收、未闭合线索。
- 返回关联场景、章节、当前状态。

### `retrieve fact`

- 用于查结构化事实卡片。
- 返回 `subject/predicate/object` 与其来源场景。

### `retrieve relation`

- 用于人物关系、组织归属、持有关系、敌友变化。
- 返回关系边与来源场景。

### `retrieve unresolved`

- 用于查所有未闭合线索、未回收伏笔、未解决冲突候选。

### `retrieve conflict-candidates`

- 用于查看 `check` 生成的候选冲突，而不是让 agent 从零判断。

## Context Pack

当要续写某个场景时，优先产出一个 context pack，至少包含:

1. 当前场景的上游 `continuity_refs`。
2. `pov` 角色卡与最近状态变化。
3. 当前 `location` 的最近两次关键事件。
4. 当前 `plotlines` 的最近状态与未闭合线索。
5. 最近的 conflict candidates。
