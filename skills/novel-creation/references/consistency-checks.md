# Consistency Checks

## Blocking Errors

以下问题默认视为 blocking:

1. 场景缺少必填字段。
2. `scene_id`、`fact_id`、`hook_id`、`loop_id` 重复。
3. `continuity_refs` 指向不存在的场景。
4. `payoff_refs` 指向不存在的伏笔。
5. 章节归档边界不连续。

## Candidate Conflicts

以下问题默认生成候选冲突，需要 agent 结合上下文判断:

1. 同一角色在完全相同的 `time` 出现在不同 `location`。
2. 同一实体的 `state_changes` 在相邻记录里互相否定。
3. 主线或支线长时间未更新，但仍被标记为活跃。
4. 伏笔存在过久且没有回收引用。
5. 新场景引入的事实与冻结设定文件中的固定表述明显背离。

## Frozen Setting Check

从 `设定/` 与项目 `AGENTS.md` 中提取冻结项。若场景的 `summary`、`new_facts` 或 `state_changes` 显式覆盖冻结项，输出 candidate conflict，并在报告中带上冻结项来源路径。

## Reporting Rule

- 把确定性错误写到 `check-summary.json` 的 `errors`。
- 把需要 agent 判断的内容写到 `conflict-candidates.json`。
- 为人类阅读额外生成 `conflict-candidates.md`。
