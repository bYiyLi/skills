# Requirements Modes And Quality Contract

在 `create`、`revise` 或 `review` 中选择或审查文档模式。create 和全文 review 检查每条正式
requirement；限定范围的 revise 或 review 只检查请求改变、指定或受影响的 requirement 及其
必要依赖，并把其余内容列为 out-of-scope。

## Select the Document Mode

1. 用户明确要求 SRS 时采用 SRS。用户明确要求 feature spec 且未命中下方任一 SRS 条件时
   采用 feature spec；若命中，停止 drafting 并请求用户选择改为 SRS，或提供能消除该条件的
   更窄范围。不要静默覆盖用户指定模式，也不要带着未解决的模式冲突继续。
2. `PRD` 只是用户或目标仓库可能使用的文档标签，不构成第三种内容模式。目标仓库定义
   了 PRD 格式时保留其格式；内容范围仍按下列条件选择 feature spec 或 SRS 合同。目标
   仓库没有 PRD 合同时，不自行发明一个 PRD schema。
3. 用户未指定内容模式时，出现任一以下可观察条件就选择 SRS：
   - 来源明确指出失败会造成安全、隐私、合规、重大财务或运营、合同或人身安全后果；
   - 多个 actor group 有不同的权限、责任或验收要求；
   - 文档要作为跨版本、跨团队或需正式批准的长期系统或子系统基线。
4. 不满足 SRS 条件，且请求只覆盖一个边界明确的 feature 时选择 feature spec。
5. 同时命中 feature 与 SRS 条件时选择 SRS。仍无法从现有事实判断时，询问会区分两种模式的缺失事实，不要任意选择。

`review` 不自动转换被审文档；按上述条件报告当前模式是否适配。

## Cover the Requirement Classes

检查以下每个类别是否适用：

- `functional`
- `interface`
- `data`
- `quality`
- `security`
- `operational`

对适用类别写正式 requirement。类别不适用但省略可能被误解为遗漏时，记录 `not applicable` 及依据。不要保留空章节代替判断。

Feature spec 至少覆盖 problem、goal、scope、actors、正式 requirements、constraints/dependencies、acceptance、assumptions 和 unresolved issues。

SRS 至少覆盖 purpose、scope、audience、stakeholders/actors、system context、正式 requirements、constraints/dependencies、acceptance/verification、traceability、assumptions 和 unresolved issues。

## Use One Formal Requirement Record

每条正式 requirement 都使用同一组字段：

- `ID`：在当前 artifact 中唯一且稳定。
- `Class`：使用适用的 requirement 类别。
- `Statement`：一个可判断的规范性要求。
- `Source`：可定位的来源或 draft 中明确的 unresolved source。
- `Priority`：来自适用来源或明确决策；没有证据时不要发明枚举或优先级，draft 中标为 unresolved，formal baseline 中作为 blocker。
- `Verification`：可观察的检查、测试、分析、评审或验收入口。

创建的 artifact 及每条新增或修订的正式 requirement 都要让这些字段可恢复，不要求目标仓库采用固定标题。全文 `review` 对所有正式 requirements 检查这些字段；用户明确限定的 review 只检查指定 requirements 和判断它们所需的依赖，并把其余内容列为 out-of-scope。范围受限的 `revise` 报告未修改的既有缺陷，不要借机扩大变更。不要使用未定义的“关键”或“重要”子集。约束如果会规范目标系统行为，也要写成正式 requirement；只描述既定外部条件时，可作为有来源的 constraint 单独列出。

## Check Every Formal Requirement

逐条确认：

1. 只有一个规范性语义；可独立判断通过或不通过。
2. 主体、行为、对象、条件和例外可从文本恢复。
3. 需求强度明确，没有把偏好写成强制要求。
4. 未把无来源的实现选择伪装成需求；强制实现决定标为 constraint 并保留来源。
5. 量化边界写明单位、计量范围、方向和端点；无法量化时给出可观察判断标准。
6. ID 唯一，且与其他 requirements 不重复、不冲突。
7. Source 和 Verification 能支持当前声明强度；缺失证据在 draft 中明确 unresolved，在 formal baseline 中构成 blocker。

## Check the Document Contract

- 系统或 feature 边界、scope、out of scope、actors、baseline、dependencies 和 constraints 没有相互矛盾。
- 每个适用 requirement 类别均已覆盖，或有可检查的 `not applicable` 依据。
- 完整结果中的每条正式 requirement 都能通过 ID 关联到来源和 verification；限定范围检查
  对指定或受影响的 requirement 及其必要依赖应用该规则，acceptance 不依赖未声明的行为。
- Assumptions、observed as-is behavior、unresolved issues 和正式 requirements 分开展示。
- 接口输入输出、数据边界、权限、异常状态和操作约束没有仅存在于背景或示例中。
- 文档没有残留模板占位符、空 scaffold 或把未来工作写成已完成事实。

全文 review 只有在这些检查覆盖所有正式 requirements 后才能通过内容质量与追溯检查；
限定范围 review 只对已检查元素形成结论，并明确其余内容 out-of-scope。一次理想 walkthrough
只证明文本可导出一致判断，不证明目标模型、工具或运行时行为。
