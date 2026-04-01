# Suite Workflow

## Standard Sequence

当一次 change event 可能影响多类软件文档时，默认按以下顺序处理：

1. inventory 当前文档真源
2. classify change event
3. build impact matrix
4. update upstream docs
5. update downstream docs
6. deprecate/archive stale docs
7. verify cross-links and statuses

## Upstream To Downstream Order

默认顺序：

1. requirements
2. design / ADR
3. usage / reference
4. archive / cleanup

如果上游未确认：

1. 不要直接把下游写成 authoritative baseline
2. 可以生成 draft plan
3. 必须显式标出 blockers

## Action Vocabulary

impact matrix 中统一使用以下 action：

1. `create`
2. `update`
3. `deprecate`
4. `archive`
5. `no-change`

不要使用模糊动作词，例如：

1. “看情况补一下”
2. “可能要改”
3. “顺手更新”

## Common Failure Modes

1. 只更新 design，忘了 requirements 或 reference。
2. 新文档建好了，但旧文档还保持 active。
3. 判定某类文档 `no-change`，却没有说明原因。
4. inventory 没盘清就直接开改，导致平行真源进一步增殖。
