# Documentation Change Impact Decisions

用可观察变化发现候选文档；本表不是要求每个仓库都拥有这些文档。

| Observed change | Candidate documents | Decision question |
| --- | --- | --- |
| 产品承诺、范围、角色、约束或验收改变 | Requirements | 已确认的需求基线是否会给出不同答案？ |
| 结构、边界、数据、运行时、部署、安全、已声明质量目标或难逆取舍改变 | Design / ADR | 实现者或评审者是否需要新的设计事实或决策记录？ |
| 用户学习路径或常见任务改变 | Tutorial / how-to | 目标读者的步骤、前置条件或预期结果是否改变？ |
| 权限、风险、恢复或运维路径改变 | Operator guide | 操作者的授权、检查点或恢复动作是否改变？ |
| API、CLI、配置、字段、返回、错误或兼容性改变 | Reference | 可查询的真实接口面是否改变？ |
| 当前文档重复、过时、断链或状态冲突 | Applicable existing docs | 哪个目标仓库规则或有权来源决定当前关系？ |

## 选择动作

矩阵的单位是 document-action。每个由 change evidence 或 inventory 发现的候选文档都要
覆盖所有不同变化维度；一个文档需要多个独立动作时复制为多行，每行只选择一个动作：

- `create`：当前没有承担所需读者结果的文档。
- `update`：已有文档拥有该结果，且变化改变其内容。
- `update-metadata`：正文不变，governing evidence 或用户在其权限内的治理决定要求改变
  非状态 metadata，且目标合同定义或允许字段和值；记录准确前后值。
- `change-state`：正文不变，目标合同定义的一般 lifecycle 状态需要改变；记录当前值、目标值
  和进入条件。变为 deprecated 时使用 `deprecate`。
- `move`：仍为当前文档，governing evidence 或用户在其权限内的治理决定要求移动或重命名，
  且目标合同定义或允许准确源路径、目标路径和受影响引用处理。移入历史位置时使用 `archive`。
- `deprecate`：文档需保留但不再表示当前事实，且目标合同已定义表示方式、当前与目标状态
  及进入条件；缺任一项时将该维度标为 `unresolved`，不自创表示方式。
- `archive`：governing evidence 或用户在其权限内的治理决定要求归档非当前文档，且目标
  合同定义或允许准确源路径、历史目标路径和进入条件。
- `delete`：准确目标和 governing evidence 表明应删除而非保留、deprecate 或 archive；记录
  引用、保留和恢复要求。实际执行还需要用户对准确目标的明确删除授权，且这些要求已满足。
- `no-change`：来源证据表明正文、metadata、状态、路径和 lifecycle 关系的所有适用变化维度
  都不需要动作。
- `unresolved`：缺少选择动作所需的来源、目标合同或 canonical 判断；执行权限缺失单独记录，
  不把已确定动作改为 `unresolved`。

`no-change` 与同一文档的其他动作行互斥。`unresolved` 可以与已确定的独立动作并存，但必须
指明尚未决定的准确变化维度，不能替代已确定动作。同一文档的多项副作用分别授权、排序
和验证。

不要用 change event 的名称直接决定动作。同一 API change 可能不改变 requirements，
也可能改变公开承诺；需要比较各文档拥有的事实。`no-change` 必须记录比较依据，未知不能
当作无影响。

## 每行所需证据

impact matrix 的每行记录：

1. 实际文档类别和当前来源；不存在时写明未发现。
2. 适用 baseline。
3. 该行唯一的 action 和它覆盖的变化维度。
4. change evidence 与判断理由。
5. 依赖、所需权限和验证方式。
6. blocker 或未验证项。
