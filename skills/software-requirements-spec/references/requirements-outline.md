# Requirements Modes And Quality Contract

在 `create`、`revise` 或 `review` 中选择或审查文档模式。create 和全文 review 检查每条正式
requirement；限定范围的 revise 或 review 只检查请求改变、指定或受影响的 requirement 及其
必要依赖，并把其余内容列为 out-of-scope。

## Select the Document Mode

1. 保留用户明确选择及目标仓库适用格式。PRD 是项目标签，可按其已有结构表达产品需求，
   不强行改名或创造新的 schema。
2. 一个边界明确的 feature 默认使用 feature spec；需要完整系统/子系统基线、跨团队
   接口与长期追溯时使用 SRS。两者都可以覆盖多个角色、权限和安全要求。
3. 风险决定需要覆盖哪些要求和验证，不单凭安全词或角色数量强制升级文档。实际法规、
   合同或仓库明确要求特定格式时才受其约束，并给出来源。
4. 未指定模式时按实际范围选择能覆盖要求的简单结构。先从材料查明范围，只在不同
   解释会改变产品承诺或交付范围时提问，不为模板选择制造审批。

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

每条正式 requirement 必须能恢复以下信息；沿用仓库字段，不要求固定标题：

- `ID`：在当前 artifact 中唯一且稳定。
- `Statement`：一个可判断的规范性要求。
- `Source`：可定位的来源或 draft 中明确的 unresolved source。
- `Verification`：可观察的检查、测试、分析、评审或验收入口。

`Class` 可以通过章节或记录表达，用于类别覆盖检查。`Priority` 仅在项目需要排序或
分期取舍时添加，值来自明确决定；没有优先级不阻止一组全部必须满足的要求形成基线。
不得为凑字段发明优先级、负责人或批准状态。稳定 ID 可沿用已有编号或可定位锚点。

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
