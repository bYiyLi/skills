# Consistency Checks

## Blocking Errors

以下问题默认视为 blocking：

1. 场景缺少必填字段。
2. `scene_id`、`fact_id`、`hook_id`、`loop_id` 重复。
3. `continuity_refs` 指向不存在的场景。
4. `payoff_refs` 指向不存在的伏笔。
5. 章节归档边界不连续。

遇到 blocking `errors` 时：

- 当前任务必须停在 `check`，不要继续大规模 `draft` 或 `archive`。
- 若问题在设定真源，reroute 到 `spec`。
- 若问题在场景结构或 scene 内容，reroute 到 `draft`。

## Warnings

`warnings` 不是立即阻断，但不能静默忽略。

常见含义：

1. 某些 hook / loop 缺少稳定 id。
2. 某些结构化记录勉强可用，但检索质量会下降。
3. 某些 scene 暂未形成 blocking conflict，但存在风险累积。

遇到 `warnings` 时：

- 可以继续当前局部任务。
- 必须把风险写进 handoff。
- 若本轮目标是 `mark ready` 或 `archive`，优先先处理掉高风险 warning。

## Review Required

`review_required` 表示系统不能确定 scene 是否真的可交接，需要人工判断。

常见来源：

1. 场景关键字段仍有占位内容。
2. prose 与 `summary`、`beats`、结构化字段对不齐。
3. 设定足够，但 scene 本身还没写成稳定可接力状态。

遇到 `review_required` 时：

- 默认回到 `draft`，继续修 scene。
- 若根源是 canon 缺口，而不是 scene 书写问题，则 reroute 到 `spec`。
- 在 `review_required` 未处理前，不要把 scene 视为稳定 `ready`。

## Candidate Conflicts

以下问题默认生成候选冲突，需要 agent 结合上下文判断：

1. 同一角色在完全相同的 `time` 出现在不同 `location`。
2. 同一实体的 `state_changes` 在相邻记录里互相否定。
3. 主线或支线长时间未更新，但仍被标记为活跃。
4. 伏笔存在过久且没有回收引用。
5. 新场景引入的事实与冻结设定文件中的固定表述明显背离。

遇到 `conflict_candidates` 时：

- 先留在 `check`，不要把它们当成已确认事实。
- 优先运行或引用 `report conflicts` 查看来源。
- 若确认问题在 canon，reroute 到 `spec`。
- 若确认问题在 scene 的写法或结构同步，reroute 到 `draft`。

## Frozen Setting Check

从 `设定/` 与项目 `AGENTS.md` 中提取冻结项。若场景的 `summary`、`new_facts` 或 `state_changes` 显式覆盖冻结项，输出 candidate conflict，并在报告中带上冻结项来源路径。

## Reporting Rule

- 把确定性错误写到 `check-summary.json` 的 `errors`。
- 把需要 agent 判断的内容写到 `conflict-candidates.json`。
- 为人类阅读额外生成 `conflict-candidates.md`。
- skill 在最终输出里必须把结果翻译成路径动作：继续当前路径、回 `spec`、回 `draft`、或停止归档。
