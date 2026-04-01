# Change Impact Matrix

## Default Mapping

| Change event | Requirements | Design | Usage | Reference | ADR | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Net-new feature | create/update | create/update | create/update | create/update | optional | 按是否存在重要设计决策决定 ADR |
| Behavior change | update | update | update | update | optional | 先确认是否改变外部行为 |
| API or CLI change | update | update | optional | update | optional | reference 通常必须更新 |
| Internal refactor | no-change/update | update | no-change | no-change | optional | 必须显式说明为何下游不变 |
| Deprecation / removal | update | update | update | update | optional | 旧文档通常需 deprecate/archive |
| Migration / rollout | optional | update | update | optional | optional | 重点补迁移与操作说明 |
| Docs cleanup | no-change | no-change | no-change | no-change | no-change | 重点治理状态、真源和链接 |

## Decision Rules

1. 如果 change event 改变了承诺、范围、验收或外部约束，requirements 不应默认 `no-change`。
2. 如果 change event 改变了结构、接口边界、运行时行为或部署影响，design 不应默认 `no-change`。
3. 如果 change event 改变了用户、管理员或集成者的实际操作路径，usage 不应默认 `no-change`。
4. 如果 change event 改变了 API、CLI、参数、字段、错误或兼容性，reference 不应默认 `no-change`。
5. 如果 change event 产生了值得单独留痕的设计决策，创建或更新 ADR。

## Output Shape

impact matrix 至少包含：

1. doc category
2. canonical path
3. current status
4. target status
5. action
6. reason
