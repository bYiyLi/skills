---
name: software-usage-docs
description: >
  用于软件使用说明文档的收敛、编写与审校，包括 tutorial、how-to、user guide、
  operator guide、troubleshooting、reference/API docs 等面向使用者或集成者的说明。
  当用户要让读者上手、完成任务、排障或查询接口/命令时触发。
  Use for software usage docs, tutorials, how-to guides, user guides,
  troubleshooting, reference docs, and API documentation.
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

1. 新建或改写用户指南、集成指南、运维操作说明、教程、how-to、FAQ、排障文档。
2. 新建或改写 CLI/API/reference 文档，让读者能快速查参数、返回值、错误码和示例。
3. 审校使用说明是否按正确文档类型组织，步骤是否可执行，reference 是否贴近真实接口。
4. 为读者建立从“学习上手”到“完成任务”再到“快速查询”的文档路径。

不要在以下情况触发：

1. 当前任务是定义需求承诺和验收边界。
2. 当前任务是解释系统内部设计和技术取舍给研发评审。
3. 当前任务只是实现功能，不交付任何说明文档。

本流程的起点是“已有产品、CLI、API 或操作流程需要说明”，终点是“形成能让目标读者独立完成任务或准确查询事实的文档”。

## Resources to Load

按需读取，不要默认全读：

- 需要判断 tutorial / how-to / reference / explanation 的边界时，读 [references/doc-flavors-and-checklist.md](references/doc-flavors-and-checklist.md)。
- 需要确认 API/reference 至少该写哪些字段时，也读 [references/doc-flavors-and-checklist.md](references/doc-flavors-and-checklist.md)。
- 需要确定使用说明应保存到哪里、如何标状态和如何替代旧版时，读 [references/doc-management-contract.md](references/doc-management-contract.md)。
- 需要直接起草文档时，优先套用 [assets/tutorial-template.md.tmpl](assets/tutorial-template.md.tmpl)、[assets/how-to-template.md.tmpl](assets/how-to-template.md.tmpl) 或 [assets/reference-template.md.tmpl](assets/reference-template.md.tmpl)。
- 若请求先问“该写成哪种说明文档”，应先配合 `software-doc-writing-standards` 做路由，再回本流程。

## Inputs

进入流程前先确认：

1. 目标读者是谁：终端用户、管理员、运维、开发者、第三方集成者。
2. 当前文档要服务的主目标：学习、完成任务、查询事实、理解原理。
3. 对应的产品/API/CLI baseline、版本、环境和权限前提。
4. 真实成功路径、已验证步骤、示例输入输出、常见错误和限制。
5. 如果是 API/reference，接口真源是什么：OpenAPI、源码、SDK、已发布契约还是命令帮助输出。
6. 目标仓库是否已有 usage/reference 文档目录合同；如果没有，默认采用 `docs/usage/` 与 `docs/reference/`。

缺输入时按以下顺序处理：

1. 缺 baseline 或真源时，不要产出 authoritative guide，只能写 draft。
2. 缺已验证成功路径时，允许先写 skeleton，但必须标注未验证。
3. 涉及危险操作而缺权限/回滚信息时，停止继续写正式操作步骤。

## Workflow

1. 先路由文档形态。
   - tutorial：帮助新手建立技能。
   - how-to / user guide：帮助读者完成具体任务。
   - reference / API docs：帮助读者快速查询接口、命令、字段和错误。
   - explanation：解释原理、背景和 why。
2. 选择 canonical document path。
   - tutorial 默认落 `docs/usage/tutorials/`
   - how-to / user guide 默认落 `docs/usage/how-to/`
   - operator guide / runbook 默认落 `docs/usage/operators/`
   - reference / API docs 默认落 `docs/reference/`
   - 有现成真源就优先更新，不要另起平行文档
3. 固定读者上下文。
   - 写清 audience、baseline、prerequisites、permissions、expected outcome。
4. 收集真源与任务路径。
   - UI/CLI/API 以真实界面、真实命令、真实契约为准。
   - 选一个 canonical flow 作为主线，不把所有分支混成一步。
5. 写正文。
   - tutorial：按学习曲线递进，示例可运行。
   - how-to：步骤化、目标导向、少解释、多动作。
   - reference/API：列语法、参数、返回、错误、版本、限制、copyable example。
   - explanation：补背景、原理、设计原因和常见误解。
6. 补可执行性与恢复。
   - 列预期结果、常见错误、排障建议、回滚或撤销方式。
7. 补文档管理信息。
   - 明确 doc type、status、owner、baseline、last updated。
   - 如替代旧文档，补 `supersedes / superseded_by`，并处理旧文档状态。
8. 做类型审校。
   - 检查是否混入过量解释、隐藏步骤、未验证示例、过时版本信息。
9. 输出文档状态与下一步。
   - 区分 verified、draft、deprecated、version-specific notes。

## Branches

- 如果同一篇文档同时承担 tutorial 和 reference，优先拆分；不拆时至少显式分区。
- 如果主要面向集成者，reference/API docs 可作为主文档，how-to 只保留常见任务入口。
- 如果主要面向运维或管理员，必须加权限、风险、回滚和排障；否则不算完成。
- 如果真实产品仍在快速变化，输出草稿并单列 version caveats / known gaps。
- 如果仓库里已有同主题 usage/reference 文档，优先更新真源；只有受众或文档类型明显变化时才新建。
- 如果旧 guide/reference 已被新文档替代，标 `deprecated` 或归档，不要让两份 active 文档并列。

## Quality Gates

1. Routing Gate
   - 当前文档类型与读者主目标匹配，没有明显混型。
2. Truth Gate
   - 步骤、命令、参数、字段、返回和错误与真实 baseline 一致。
3. Task Gate
   - 读者按步骤能完成任务，或按 reference 能快速查到答案。
4. Recovery Gate
   - 前置条件、权限、错误和恢复路径在需要时已写清。
5. Navigation Gate
   - 文档有版本说明、相关链接、下一步或邻近文档入口。
6. Repository Gate
   - 文档位于 canonical 路径，状态明确，没有制造新的平行真源。

## Done Definition

满足以下条件才算完成：

1. 目标读者和文档类型已经明确。
2. 主任务步骤或主查询结构已经稳定，可直接使用。
3. 示例与命令可复制、可验证，或明确标成未验证草稿。
4. 关键错误、限制、权限和版本差异没有被省略。
5. 读者无需翻设计文档也能完成任务或查到所需事实。
6. 文档已放在 canonical path，且管理状态明确。

## Handoff

结束时固定交付：

1. `doc flavor`
2. `target audience and baseline`
3. `verified vs draft areas`
4. `primary tasks or reference surface covered`
5. `known gaps / deprecations / version caveats`
6. `document path and status`
7. `supersede/archive actions if any`
8. `recommended next step`

## Output Standard

- 先写 canonical path、读者对象、目标、baseline 和 prerequisites，再写正文。
- task docs 用祈使句和可执行步骤；reference 用陈述句和稳定字段结构。
- 一步只做一个动作，并尽量给 expected result。
- API/reference 文档至少覆盖 endpoint/command、syntax、parameters、responses、errors、examples、auth/version notes 中的相关项。
- 如有旧版文档，明确是更新、替代还是归档。

## Stop Conditions

- 无法确认产品、CLI 或 API 的真实 baseline。
- 用户真正需要的是需求或设计文档。
- 涉及高风险操作，但没有权限边界、回滚或排障信息。
- 当前内容会把未发布或未验证行为误写成正式能力。
- 仓库内已存在冲突的 usage/reference 真源，且当前无法判断哪份有效。

## Minimal Examples

正例：

1. “给这个 CLI 写一组使用说明，包含新手 tutorial、常见 how-to 和命令 reference。”
2. “把这份 API 文档整理成正式 reference，补齐参数、返回值、错误码和可复制示例。”

边界例：

1. “先明确这个功能到底该不该做、范围多大、验收怎么算。”
2. “写一份研发评审用的详细设计，说明模块边界、时序和部署拓扑。”
