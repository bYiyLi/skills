# Design View Routing

根据请求需要定义或核对的设计问题、已观察到的当前或目标范围和设计驱动选择视图。以下内容不是必填文档目录；目标仓库适用的
设计合同或模板优先。

## 按可观察信号选择视图

只有请求的设计问题或至少一个已观察信号需要某个视图时才加入：

| View | 选择信号 |
| --- | --- |
| Context | 需要定义或核对外部参与者、系统、trust boundary、ownership 或责任转移 |
| Structure | 需要定义或核对部署单元、component、module、依赖方向或职责分配 |
| Interface | 需要定义或核对 API、event、command、configuration、schema、权限、错误、版本或兼容性 |
| Runtime | 需要定义或核对顺序、并发、timeout、retry、idempotency、降级、恢复或其他失败路径 |
| Data | 需要定义或核对持久化实体、状态变化、一致性、保留、迁移或 ownership |
| Deployment and operations | 需要定义或核对运行位置、基础设施、rollout、rollback、容量、可观测性或运维 ownership |
| Security | 需要定义或核对身份、授权、敏感数据、trust boundary、滥用路径或安全控制 |
| Decisions and risks | 存在 architecturally significant choice、未决备选、后果或 explicit gap |

一个结果可以选择多个视图。重叠事实只保留一个 canonical 表达，其他视图通过引用关联，
避免复制出冲突版本。若某视图没有请求问题、观察信号或目标仓库要求，则删除该视图。

## 定义 Architecturally Significant Decision

一个选择满足以下任一条件时，视为 architecturally significant：

- 改变外部边界或模块边界；
- 改变数据模型、状态变化、ownership 规则或一致性行为；
- 改变会影响已声明 driver、外部结果或恢复条件的运行交互、失败行为、恢复路径或
  兼容性契约；
- 改变部署、运维、安全或已明确声明的质量目标；或
- 产生代价高或难以逆转的取舍。

对每个此类选择记录决定、支持证据、备选方案、取舍、已知后果和未决风险。若一个实现
细节同等满足所有已声明 driver，且不产生上述影响，则不强制建立 decision record。

## 建立 Driver 映射

为每个已声明目标、约束、质量目标、stakeholder concern，以及必须满足的兼容性或迁移
条件建立以下映射：

    driver
      -> design element 或 architecturally significant decision
      -> verification、rollout、migration 或 explicit gap

explicit gap 要说明缺失证据或未决决定，以及受影响的设计部分。会改变请求结果的 gap
存在时，不能声称 completed result。

## 检查已选视图

对每个已选视图检查触发其选择的问题：

- 标明相关职责、边界、依赖或 owner。
- 描述支持的交互或状态变化。
- 当失败、拒绝、timeout、冲突或恢复会改变实现或验证时，描述对应行为。
- 将视图关联到 driver 和适用证据。
- 存在多个 baseline 时，区分 as-is、to-be 和 gap。

review 只有在上述请求问题或可观察信号没有得到等价覆盖时，才能报告缺失视图。不要因为文档省略
未使用的标题或图，就判定设计不完整。
