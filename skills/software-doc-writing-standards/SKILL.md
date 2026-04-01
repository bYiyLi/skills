---
name: software-doc-writing-standards
description: >
  用于软件需求文档、架构/详细设计文档、使用说明、教程、reference/API 文档的选型、
  写作和审校规范。当用户要新写、改写、统一或评审软件文档体系时触发。
  Use for software documentation taxonomy, writing standards, requirements/design docs,
  user guides, tutorials, reference docs, API docs, and traceability.
license: ./LICENSE.txt
metadata:
  owner: yi
  status: active
  last-reviewed: 2026-04-01
  source-bucket: software-docs
  skill-type: normative
---

# Task Fit

在以下情况触发：

1. 需要判断某个软件文档应写成需求、设计、教程、how-to、reference 还是 explanation。
2. 需要把已有草稿改写成更合适的软件文档类型。
3. 需要统一一组软件文档的结构、语气、证据边界和质量标准。
4. 需要按统一口径审校软件文档是否清晰、可验证、可追溯。

不要在以下情况触发：

1. 任务目标是直接实现代码，而不是交付文档。
2. 只是做项目计划、排期、预算、法务条款或市场文案。
3. 用户已经明确指定单一文档类型且只需要执行该流程时，应改用对应流程类 skill。

最关键的判断对象不是文档标题，而是：

1. 读者要完成什么工作。
2. 文档依赖什么真源。
3. 这份文档最终要支撑决策、设计、实现、操作还是查询。

## Resources to Load

按需读取，不要默认全读：

- 需要先判断写哪种文档时，读 [references/doc-taxonomy.md](references/doc-taxonomy.md)。
- 需要统一共性质量规则、追溯规则和“不可编造”边界时，读 [references/quality-rules.md](references/quality-rules.md)。
- 当一个请求混合了多个读者目标，或已有标题与实际内容不一致时，两个 reference 都要交叉检查。
- 本 skill 的标准依据已经内化到本地 references；不要把使用方再跳转到外部资料。

## Decision Rules

按优先级执行，不要跳级：

1. 先按读者任务路由文档类型。
   - 要决定做什么、承诺什么、验收什么：优先写需求文档。
   - 要说明系统如何组织、为何这样设计、如何落地：优先写设计文档。
   - 要让用户、运维或集成人员完成任务：优先写 tutorial、how-to 或 usage guide。
   - 要让读者快速查语法、参数、接口、返回值、错误码：优先写 reference 或 API docs。
   - 要解释背景、原理、取舍、历史原因：优先写 explanation。
2. 一份文档只允许有一个主工作目标。
   - 如果请求同时要求“学会概念 + 完成任务 + 查参数”，必须拆成多个交付物，或至少显式分段标注。
   - 不要把教程、任务步骤、参考表和设计原理混成一篇无边界长文。
3. 所有软件文档都必须明确以下最小上下文。
   - audience：写给谁。
   - scope：覆盖什么，不覆盖什么。
   - baseline：对应哪个系统、版本、分支、发布日期或决议状态。
   - source of truth：事实来自哪份代码、接口、需求、设计或产品决议。
   - assumptions / open questions：哪些仍未确认。
4. 需求类文档必须满足“可判断、可验证、可追溯”。
   - 写成单一、必要、清晰、可测试的要求。
   - 非设计约束不要伪装成需求。
   - 每条关键要求都要能追到来源和预期验证方式。
5. 设计类文档必须满足“有驱动、有视图、有取舍”。
   - 先写驱动因素、质量目标、约束和边界。
   - 再写结构、接口、数据、运行时行为、部署和故障处理。
   - 每个重要设计都要解释 rationale 和 trade-off，而不是只列结果。
6. 使用与参考类文档必须满足“面向任务或面向查询，而不是面向作者叙述习惯”。
   - task docs 用步骤、前置条件、预期结果、回退和排障。
   - reference docs 直接镜像真实接口面，列语法、参数、返回、错误、示例、适用版本。
   - explanation 只讲 why，不伪装成操作步骤。
7. 缺证据时默认保守，而不是补写想当然的内容。
   - 缺真源就标假设。
   - 缺结论就列 open question。
   - 缺版本确认就降低为 draft，不写成 authoritative baseline。

## Exceptions

以下情况允许压缩形式，但不允许丢掉核心判断：

1. 用户明确要一页纸 brief，可以压缩章节，但仍要交代 audience、scope、baseline 和 open questions。
2. 团队已有强制模板时，允许沿用模板标题，只要不违反本 skill 的硬约束。
3. ADR、RFC、feature brief 这类轻量文档可以不是长篇，但仍要明确决策对象、约束、结论和影响。
4. 原型期文档可以保留较多假设，但必须显式标成 draft / proposal，而不是写成既定事实。

## Conflict Resolution

冲突时按以下顺序裁决：

1. 已确认的真源优先于二手摘要。
   - 已发布接口、已合并代码、已批准需求、已接受设计决议，优先于聊天记录或口头转述。
2. 文档目标优先于文档标题。
   - 标题叫“用户指南”，但内容主要在讲接口字段与错误码时，应按 reference 处理。
3. 用户给定模板优先于本 skill 的建议结构，但不能破坏可验证、可追溯、不可编造这三条硬约束。
4. 规范正文优先于示例。
   - 示例只能帮助理解，不能推翻正文规则。
5. 无法裁决时，明确标“不确定”并停止声称这是最终版。

## Output Standard

最终输出至少满足：

1. 明确说明当前采用的文档类型或混合拆分方案。
2. 说明为什么是这个类型，而不是相邻类型。
3. 标出关键事实来自哪类真源。
4. 单独列出 assumptions、gaps、open questions，不把它们伪装成定论。
5. 评审输出时，结论能对应到具体规则或规则组，而不是只给“建议更清晰”。

## Stop Conditions

在以下情况停止并升级：

1. 请求本质上不是文档任务，而是实现、测试或运营动作。
2. 没有可用真源，但用户要求交付“最终、正式、可对外”的文档。
3. 请求要求给出合规、审计或合同级承诺，但缺少 governing standard。
4. 一个文档被要求同时承担互相冲突的目标，且用户不允许拆分。

## Minimal Examples

正例：

1. “把这份零散讨论收敛成一版软件需求文档，并告诉我哪些内容应该单独进设计文档。”
2. “这篇开发文档现在像教程和 API 参考混在一起，帮我按正确文档类型重组。”

边界例：

1. “这个功能别写文档了，直接实现掉。”
2. “给我写一篇产品宣传页文案，突出卖点和品牌语气。”
