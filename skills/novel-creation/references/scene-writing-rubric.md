# Scene Writing Rubric

## When To Load

只在 `draft` 路径下读取本参考，尤其是以下情况：

- 要继续写某一场戏。
- 要把 context pack 转成场景计划。
- 要判断这场戏应该 `keep draft`、`mark ready`，还是发生 reroute。
- 要解释为什么“信息齐了，但 scene 还不能进 ready”。

## Authoring Loop

按以下顺序推进一场戏：

1. gather context
   - 锁定当前 `scene_id`、`pov`、`time`、`location`、`plotlines`。
   - 先确认上游 `continuity_refs` 是否足够支撑续写。
2. define scene goal / conflict / turn / outcome
   - 写清这场戏想推进什么。
   - 写清主要阻力、关键转折和最后落到哪里。
3. beats
   - 先列 3 到 6 个 beats。
   - beats 要体现动作推进，而不是只列设定解释。
4. prose
   - 让每个 beat 在正文里有可观察体现。
   - 优先体现冲突、决策、变化，而不是概念讲解。
5. structured sync
   - 同步 `summary`、`new_facts`、`state_changes`、`foreshadow`、`payoff_refs`、`open_loops`。
   - 若正文引入了新事实，但结构化字段未同步，视为未完成。
6. ready decision
   - 明确给出 `keep draft`、`mark ready`、`reroute to spec`、`reroute to retrieve`、`reroute to check` 之一。

## Ready Decision

### `keep draft`

适用于以下情况：

- 结构还没补齐，但 scene 方向是对的。
- beats、prose、summary 还没完全对齐。
- 已经写出局部推进，但还没达到可以交给归档的稳定程度。

### `mark ready`

只有以下条件同时满足时才成立：

- 必填字段齐全，且没有明显占位内容。
- beats 与 prose 对齐，不是“列了计划但正文没发生”。
- 至少有一个可观察推进：冲突升级、关系变化、目标变化、信息揭示、局势逆转。
- `summary` 能用 2 到 4 句准确概括正文。
- `new_facts` 与 `state_changes` 足以支撑后续检索和一致性检查。

### `reroute to spec`

适用于以下情况：

- 世界规则不明确，scene 继续写会强行发明 canon。
- 主线目标或主要阻力不清，导致这场戏不知道在推进什么。
- 时间位置不明确，导致 scene 无法稳定落在 timeline 上。

### `reroute to retrieve`

适用于以下情况：

- `continuity_refs` 不够，无法稳定承接上一场戏。
- POV、地点、plotline 的最近状态不清，需要先查 context pack。
- 已有真源，但当前 writer 不知道该取哪一小包材料来继续写。

### `reroute to check`

适用于以下情况：

- 怀疑 scene 已经撞到 continuity 风险、冻结设定风险或重复事实风险。
- 想进 `ready`，但不确定是否还有阻断性问题。
- 写作过程引入了多个新事实，需要先确认是否与当前 canon 冲突。

## Creative Checks

写完一场戏后至少检查：

1. 这场戏是否真的推进了某条情节线，而不是只重复现状。
2. 关键角色是否做了选择、付出代价，或获得新的局部认知。
3. `pov` 是否稳定，没有无提示跳视角。
4. `outcome` 是否和 `goal`、冲突、正文动作一致。
5. 新增伏笔、线索、事实是否都已同步到结构化字段。
6. 若这是承上启下场景，是否给下一场戏留下明确可接续的问题。

## Common Failure Modes

- 只有设定解释，没有场景动作。
- `goal` 和 `outcome` 写了，但正文没有真正走到那个结果。
- 写了新设定、新关系或新线索，却没同步 `new_facts`、`state_changes` 或 `open_loops`。
- 为了继续写而跳过上游连续性缺口，导致后续 `check` 和检索失真。
- 想直接 `mark ready`，但其实应该先 reroute 到 `spec`、`retrieve` 或 `check`。
