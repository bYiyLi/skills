---
name: software-design-spec
description: >
  用于软件架构文档与详细设计文档的收敛、编写与审校，包括 architecture overview、
  HLD/LLD、feature design、ADR-rich design 等。当用户要说明结构、接口、数据、
  运行时行为、部署、风险与设计取舍时触发。
  Use for software architecture and detailed design documents, HLD/LLD,
  design specs, ADR-driven design, views, and trade-off analysis.
license: ./LICENSE.txt
metadata:
  owner: yi
  status: active
  last-reviewed: 2026-04-01
  source-bucket: software-docs
  skill-type: process
---

# Task Fit

在以下情况触发：

1. 新建或改写软件架构文档、详细设计文档、模块设计文档。
2. 需要把需求、约束和质量目标转成结构化设计说明。
3. 需要评审设计是否覆盖结构、接口、运行时、部署、风险和 trade-offs。
4. 需要为实现、测试、上线前评审提供明确设计基线。

不要在以下情况触发：

1. 当前任务是定义“做什么”和“验收什么”，还没进入 solution 设计。
2. 当前任务是面向用户或运维的操作说明。
3. 当前任务只是实现代码而不交付设计文档。

本流程的起点是“已有问题定义、需求或变更目标”，终点是“形成足够指导实现和评审的设计说明”。

## Resources to Load

按需读取，不要默认全读：

- 需要决定用哪些视图或章节时，读 [references/design-view-set.md](references/design-view-set.md)。
- 需要快速检查设计是否缺结构、运行时、部署、风险或决策记录时，也读 [references/design-view-set.md](references/design-view-set.md)。
- 需要确定设计文档该保存到哪里、如何标状态和如何替代旧版时，读 [references/doc-management-contract.md](references/doc-management-contract.md)。
- 需要直接起草设计文档时，优先套用 [assets/design-spec-template.md.tmpl](assets/design-spec-template.md.tmpl)。
- 若先判断这是不是设计文档任务，应先配合 `software-doc-writing-standards` 做路由。

## Inputs

进入流程前先确认：

1. 上游需求、目标、约束或变更范围。
2. 当前设计层级：architecture overview、feature design、module-level design 还是 detailed design。
3. 现有系统上下文、外部依赖、已有接口和已有设计决议。
4. 重要质量目标：性能、可靠性、安全性、可维护性、可扩展性、可观测性等。
5. 当前 baseline：as-is、to-be，还是 migration delta。
6. 目标仓库是否已有 design 文档目录合同；如果没有，默认采用 `docs/design/`。

缺输入时按以下顺序处理：

1. 缺问题定义或关键驱动时，先停在 design drivers，不直接产出 authoritative design。
2. 缺接口真源或现状基线时，可写 provisional design，但要把假设单列。
3. 缺质量目标时，不算完成；至少要写 architecturally significant concerns。

## Workflow

1. 确定设计范围和层级。
   - 全局或跨系统变更：偏 architecture overview。
   - 单特性或子系统改动：偏 feature design。
   - 模块内部实现约束：偏 detailed design。
2. 选择 canonical document path。
   - 先判断是更新现有 design 真源，还是新建设计文档。
   - 目标仓库没有显式合同就落到 `docs/design/`。
   - 不要把长期设计基线留在 PR 描述、白板截图说明或零散笔记里。
3. 写清 design drivers。
   - 目标、约束、质量需求、stakeholders、concerns、已知边界。
4. 选择最小必要 view set。
   - 常见组合：context、container/component/module、runtime、data、interface、deployment、security/ops。
   - 只保留能支撑当前决策的视图，不追求模板填满。
5. 展开关键设计内容。
   - 每个视图写职责、边界、依赖、关键交互、失败路径或约束。
   - 记录数据模型、状态变化、兼容性和迁移点。
6. 记录 architecture decisions。
   - 对重要设计选择写 rationale、alternatives、trade-offs、known consequences。
7. 建立追溯。
   - 设计元素要能回到 requirement / constraint / quality goal。
   - 也要指向后续 verification、rollout 或 migration 方案。
8. 补文档管理信息。
   - 明确 doc type、status、owner、baseline、last updated。
   - 如替代旧文档，补 `supersedes / superseded_by`，并处理旧文档状态。
9. 做一致性审校并输出 handoff。
   - 检查各视图是否互相矛盾，当前态与目标态是否混写，风险是否被隐藏。

## Branches

- 如果需求仍频繁变化，输出 provisional design，并单列 assumptions、decision debt 和 reevaluation trigger。
- 如果改动范围很小，可以压缩 context/deployment，但不能省略接口、依赖和失败模式。
- 如果已有强制模板或 ADR 机制，优先嵌入现有决策容器，不重复堆一份平行文档。
- 如果当前实现已经偏离历史设计，明确区分 as-is / to-be / gap，不要假装历史文档仍然有效。
- 如果仓库里已有同主题 design 文档，优先更新真源；只有层级或范围明确变化时才新建。
- 如果旧设计已被新设计替代，标 `deprecated` 或归档，不要让两份 active 设计并列。

## Quality Gates

1. Driver Gate
   - stakeholders、concerns、quality goals、constraints 已明确。
2. View Coverage Gate
   - 选定视图足以覆盖结构、行为、接口和运维影响。
3. Interface Gate
   - 外部边界、数据契约、错误处理、兼容性和 ownership 清楚。
4. Decision Gate
   - 重要 trade-off、被放弃方案和 rationale 已记录。
5. Traceability Gate
   - 关键设计能够回溯到需求/约束，也能前指到验证/上线/迁移。
6. Repository Gate
   - 设计文档位于 canonical 路径，状态明确，没有制造新的平行真源。

## Done Definition

满足以下条件才算完成：

1. 设计层级和范围与当前变更匹配。
2. 实现者和评审者可以从文档中理解结构、接口、运行时行为和关键约束。
3. 风险、兼容性、运维影响和已知未决项没有被藏在口头假设里。
4. 关键设计决策和取舍已经留痕。
5. 下一步实现、验证或评审动作明确。
6. 文档已放在 canonical path，且管理状态明确。

## Handoff

结束时固定交付：

1. `design scope and level`
2. `as-is / to-be baseline`
3. `selected views`
4. `major decisions and trade-offs`
5. `key risks / compatibility / migration notes`
6. `traceability hooks`
7. `document path and status`
8. `supersede/archive actions if any`
9. `recommended next step`

## Output Standard

- 先给设计范围、canonical path、当前/目标态和主要驱动，再展开视图与决策。
- 区分 facts、assumptions、decisions、alternatives。
- 结构图、时序、部署或数据说明都应能用文字独立复现。
- 不要只写“采用微服务/事件驱动/分层架构”这种标签，必须说明为何适配当前驱动。
- 如有旧版文档，明确是更新、替代还是归档。

## Stop Conditions

- 没有足够稳定的问题定义或设计驱动。
- 用户真正需要的是需求文档或使用说明文档。
- 关键接口、依赖或部署边界无法确认，且继续写会误导实现。
- 涉及安全、合规或组织级决策，但当前没有裁决 authority。
- 仓库内已存在冲突的 design 真源，且当前无法判断哪份有效。

## Minimal Examples

正例：

1. “为这个新结算子系统写一版架构和详细设计，覆盖上下文、模块边界、数据流、关键时序和部署影响。”
2. “评审这份 feature design，重点看接口契约、失败路径、兼容性和设计取舍是否写清楚。”

边界例：

1. “先帮我明确要做哪些功能、哪些不做，再给验收标准。”
2. “写一份终端用户操作手册，教客服怎么处理退款工单。”
