---
name: software-doc-suite-workflow
description: >
  用于软件文档套件的编排、同步与治理。当一次需求变更、设计调整、接口演进、
  功能废弃或文档清理会同时影响 requirements、design、usage、reference、ADR
  等多类文档时触发。Use for multi-document software documentation workflow,
  impact analysis, document sync, deprecation, archival, and canonical-source governance.
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

1. 一次功能、接口、架构或流程变更需要同时更新多类软件文档。
2. 需要盘点某次变更会影响哪些 requirements、design、usage、reference 或 ADR。
3. 需要决定哪些文档应新建、更新、替代、废弃或归档。
4. 需要治理文档仓库，识别平行真源、过时文档和断链关系。

不要在以下情况触发：

1. 只需要写单一类型文档，例如只写一份 requirement 或一篇 API reference。
2. 只需要评审一篇单文档内容质量，而不涉及文档套件联动。
3. 当前目标是实现代码、修 bug 或跑发布，而不是同步文档体系。

本流程的起点是“已有一个会影响多份文档的 change event 或治理目标”，终点是“形成清晰的文档影响矩阵，并把相关文档同步到一致状态”。

## Resources to Load

按需读取，不要默认全读：

- 需要按阶段推进整套文档同步时，读 [references/suite-workflow.md](references/suite-workflow.md)。
- 需要判断某类变更通常影响哪些文档时，读 [references/change-impact-matrix.md](references/change-impact-matrix.md)。
- 需要直接输出文档同步计划或治理报告时，套用 [assets/doc-sync-plan-template.md.tmpl](assets/doc-sync-plan-template.md.tmpl)。

## Inputs

进入流程前先确认：

1. change event 是什么：新功能、行为调整、接口演进、架构重构、废弃/下线、文档治理。
2. 当前 baseline、版本、里程碑或目标分支。
3. 仓库是否已有文档目录合同；如果没有，使用默认 `docs/` 布局。
4. 当前仓库里已存在哪些 canonical 文档、哪些可能已过时。
5. 当前输出目标是什么：同步计划、执行更新、治理报告，还是 release 前检查。

缺输入时按以下顺序处理：

1. 缺仓库文档现状时，先做 inventory，不直接开始大范围改写。
2. 缺变更范围时，先收缩成 impact analysis，不把未确认文档一并改掉。
3. 缺 baseline 时，允许先做 draft sync plan，但要显式标注未确认项。

## Workflow

1. 做文档 inventory。
   - 盘点当前 requirements、design、usage、reference、ADR 的 canonical path、status 和 owner。
   - 识别平行真源、过时文档、缺失文档和断链关系。
2. 分类 change event。
   - 判断这是 net-new feature、behavior change、internal refactor、deprecation、migration 还是 docs cleanup。
3. 生成 impact matrix。
   - 为每类文档决定 action：`create / update / deprecate / archive / no-change`。
   - 明确每份文档的 canonical path、预期状态和与其它文档的关系。
4. 排同步顺序。
   - 默认顺序是 `requirements -> design / ADR -> usage / reference -> archive / cleanup`。
   - 如果 change event 不影响某层，显式标 `no-change`，不要省略判断。
5. 执行或规划更新。
   - 新建缺失文档。
   - 更新现有真源。
   - 处理 supersede、deprecation 和 archive。
6. 同步元信息与交叉链接。
   - 对齐 baseline、status、owner、last_updated。
   - 回填 requirement-design-reference-ADR 之间的链接。
7. 做套件级审校并输出 handoff。
   - 确认没有遗留平行真源、错误状态或明显断链。

## Branches

- 如果是 net-new feature，通常至少检查 requirements、design、usage/reference 是否都需要建立真源。
- 如果是 internal refactor 且无外部行为变化，通常以 design 为主；但必须显式判断 requirements 和 usage/reference 是否维持 `no-change`。
- 如果是 API 或 CLI 行为变化，reference 必须进入 impact matrix，通常还要检查 requirements、design 和 how-to。
- 如果是 deprecation / removal，必须同时处理替代文档、旧文档状态和 archive。
- 如果是 docs cleanup，没有功能变更也可以触发；此时重点是 canonical-source 治理，而不是重写正文。

## Quality Gates

1. Inventory Gate
   - 当前仓库文档现状、canonical path 和状态已经盘清。
2. Impact Gate
   - 每类文档都已判定 `create / update / deprecate / archive / no-change`。
3. Sequencing Gate
   - 同步顺序清晰，没有跳过上游判断就直接改下游文档。
4. Repository Gate
   - 不会制造新的平行真源，旧文档状态处理明确。
5. Linkage Gate
   - requirements、design、usage/reference、ADR 之间的交叉链接和 supersede 关系完整。

## Done Definition

满足以下条件才算完成：

1. 已形成完整的 impact matrix。
2. 每份受影响文档都明确了 canonical path、action 和 target status。
3. 需要更新的文档已同步，或至少形成明确的执行计划和顺序。
4. 平行真源、过时状态和 archive 动作没有被遗漏。
5. 下一步由谁继续、继续什么已经明确。

## Handoff

结束时固定交付：

1. `change event and baseline`
2. `document inventory summary`
3. `impact matrix`
4. `actions taken or planned`
5. `stale docs / supersede / archive actions`
6. `remaining gaps or blockers`
7. `recommended next step`

## Output Standard

- 先给 change event、baseline 和 inventory 结论，再给 impact matrix。
- 每类文档都必须有 action 和 canonical path，哪怕是 `no-change`。
- 明确区分“已执行更新”和“建议更新”。
- 如果发现平行真源、错误状态或断链，要单独列出，不要埋在正文里。

## Stop Conditions

- 无法确认 change event 范围，且继续判断会误伤大量文档。
- 仓库内存在冲突的文档合同，当前无法判断应以哪套为准。
- 用户真正需要的是单篇文档创作，而不是文档套件协同。
- 仓库文档现状严重失控，必须先做人为裁决后才能继续自动同步。

## Minimal Examples

正例：

1. “这个支付功能上线前，帮我同步需求、设计、API reference 和操作手册，并告诉我哪些旧文档该归档。”
2. “本次账号体系重构会影响哪些软件文档？请做一份 impact matrix，说明哪些更新、哪些保持不变。”

边界例：

1. “只帮我写一版新的 feature spec。”
2. “只补这条接口的 reference 文档，不要管别的文档。”
