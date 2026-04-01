---
name: software-requirements-spec
description: >
  用于软件需求文档的收敛、编写与审校，包括 PRD、feature spec、SRS 风格的需求基线。
  当用户要定义范围、角色、功能/非功能要求、接口约束、验收标准与追溯关系时触发。
  Use for software requirements documents, product requirements, feature specs,
  SRS, acceptance criteria, and traceability.
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

1. 新建或改写软件需求文档。
2. 把零散讨论、用户故事、工单、会议纪要收敛成可评审的 feature spec 或 SRS。
3. 审校需求是否清晰、原子、可测、可追溯。
4. 为后续设计、实现、测试建立需求基线与验收口径。

不要在以下情况触发：

1. 主要任务是设计系统结构、模块划分、接口细节或技术选型。
2. 主要任务是写用户指南、教程、FAQ 或 API reference。
3. 用户明确只要一个技术方案，而不是需求定义。

本流程的起点是“已有需求线索但尚未形成清晰需求基线”，终点是“形成可交给设计/测试继续工作的需求文档”。

## Resources to Load

按需读取，不要默认全读：

- 需要选文档层级或章节骨架时，读 [references/requirements-outline.md](references/requirements-outline.md)。
- 需要确认 requirement quality checklist、追溯项和常见坏味道时，也读 [references/requirements-outline.md](references/requirements-outline.md)。
- 需要确定需求文档该保存到哪里、如何标状态和如何替代旧版时，读 [references/doc-management-contract.md](references/doc-management-contract.md)。
- 需要直接起草文档时，优先套用 [assets/feature-spec-template.md.tmpl](assets/feature-spec-template.md.tmpl) 或 [assets/srs-template.md.tmpl](assets/srs-template.md.tmpl)。
- 若请求先问“这该不该写成需求文档”，应先配合 `software-doc-writing-standards` 做路由，再回到本流程。

## Inputs

进入流程前先确认：

1. 需求面向的产品、系统或子系统边界。
2. 目标读者是谁：产品、研发、测试、外部合作方还是混合评审组。
3. 当前要产出的深度：brief、feature spec 还是较完整的 SRS。
4. 已有事实来源：用户问题、业务目标、法规、合同、现网问题、现有接口、历史决议。
5. 当前版本、里程碑或范围基线。
6. 目标仓库是否已有 requirements 文档目录合同；如果没有，默认采用 `docs/requirements/`。

缺输入时按以下顺序处理：

1. 缺系统边界时，先停在范围澄清，不进入正式 requirements drafting。
2. 缺事实来源时，允许先写 draft，但必须显式分出 assumptions / open questions。
3. 缺验收口径时，不算完成；至少要写 verification intent 或 acceptance placeholders。

## Workflow

1. 定义文档模式。
   - 低风险或单功能：可写 feature spec。
   - 多角色、多约束、要长期留档：提升到 SRS 风格。
   - 如果用户只给“想法”，先收敛成 problem / goal / scope brief。
2. 选择 canonical document path。
   - 先判断是更新现有 requirements 真源，还是新建文档。
   - 目标仓库没有显式合同就落到 `docs/requirements/`。
   - 不要把正式需求长期放在 PR 描述、临时笔记或随机目录中。
3. 固定边界。
   - 写清问题陈述、业务目标、成功指标、范围内/范围外、关键角色、依赖与约束。
4. 盘点需求项。
   - 分类整理 functional、interface、data、quality、security、compliance、operational requirements。
   - 把“背景说明”“设计建议”“实现细节”从 requirement statement 里剥离出去。
5. 正式化每条关键要求。
   - 给唯一标识或稳定标题。
   - 保持单一语义。
   - 说明来源、优先级和验证方式。
6. 写验收与追溯。
   - 需求至少能追到来源和预期验证。
   - 关键需求要能为后续 design / test 留出 traceability hook。
7. 补文档管理信息。
   - 明确 doc type、status、owner、baseline、last updated。
   - 如替代旧文档，补 `supersedes / superseded_by`，并处理旧文档状态。
8. 做质量审校。
   - 查歧义、重复、互相冲突、实现泄漏、空泛 NFR、遗漏接口、遗漏例外。
9. 输出基线与未决项。
   - 区分 accepted baseline、assumptions、open questions、follow-up actions。

## Branches

- 如果请求其实是“写一个产品愿景或路线图”，收缩为 problem/scope/goal brief，不要冒充完整 SRS。
- 如果实现方案已经被上游强制指定，把它记为 constraint，不要写成“需求天然如此”。
- 如果需求来源互相冲突，保留冲突对照和待裁决项，不要私自选边并写成定论。
- 如果是对已有系统补文档，允许从现状和已实现行为倒推，但要标明“as-is baseline”。
- 如果仓库里已有同主题 requirements 文档，优先更新真源；只有主题或层级明显不同的情况下才新建。
- 如果旧文档已被替代但仍在工作目录中，标记 `deprecated` 或移入 archive，不要继续并列维护。

## Quality Gates

1. Boundary Gate
   - audience、scope、out-of-scope、baseline、dependencies 已明确。
2. Requirement Quality Gate
   - 关键 requirement 是原子、清晰、必要、可验证、非重复的。
3. Interface Gate
   - 外部接口、输入输出、关键数据或第三方依赖没有被遗漏。
4. NFR Gate
   - 重要质量要求有量化目标、边界条件或至少明确的判断标准。
5. Traceability Gate
   - 关键要求可追到来源，并指向 acceptance / verification 入口。
6. Repository Gate
   - 需求文档位于 canonical 路径，状态明确，没有制造新的平行真源。

## Done Definition

满足以下条件才算完成：

1. 文档模式已经确定，且与风险和受众匹配。
2. 需求边界、范围、角色、依赖和约束已经显式表达。
3. 关键 requirements 已写到可供设计和测试继续工作的粒度。
4. 验收/验证思路和 open questions 已分离，不互相混淆。
5. 关键追溯入口已经建立。
6. 文档已放在 canonical path，且管理状态明确。

## Handoff

结束时固定交付：

1. `doc mode`
2. `baseline and scope`
3. `key requirements and priorities`
4. `acceptance / verification hooks`
5. `assumptions and open questions`
6. `document path and status`
7. `supersede/archive actions if any`
8. `recommended next step`

## Output Standard

- 先给文档模式、canonical path、范围基线和当前置信度，再给 requirements 正文。
- requirement statement 与背景、例外、设计建议分开展示。
- 不要把“可能”“最好”“支持一下”这类模糊话术当成正式要求。
- 重要要求后面要能看到来源、约束或验证入口。
- 如有旧版文档，明确是更新、替代还是归档。

## Stop Conditions

- 无法确认系统边界或主要目标。
- 用户真正需要的是设计文档而不是需求文档。
- 没有可信事实来源，却要求交付正式承诺性需求基线。
- 上游来源互相冲突且当前无法裁决。
- 仓库内已存在冲突的 requirements 真源，且当前无法判断哪份有效。

## Minimal Examples

正例：

1. “把这批需求讨论整理成一版 feature spec，包含范围、角色、功能要求、非功能要求和验收标准。”
2. “帮我审一下这份 SRS，重点看是否可测、是否有实现泄漏、是否能追溯到来源。”

边界例：

1. “把系统怎么拆模块、怎么部署、怎么选数据库写清楚。” 
2. “给终端用户写一个使用教程，教他们怎么完成导入任务。”
