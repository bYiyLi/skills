# Usage Document Flavors And Checks

本 reference 定义 `software-usage-docs` 内部的文档类型决策和内容检查，不定义目标
仓库的路径、metadata、生命周期或外部产品事实。文档中的事实仍以目标任务核对后的
governing source 为准。

## 选择单一读者目标

| 读者的主要目标 | 文档类型 | 结果边界 |
| --- | --- | --- |
| 从零建立一项产品使用能力 | tutorial | 完成一条递进学习路径，不承担完整参数查询。 |
| 完成一个已知任务 | how-to | 到达一个可观察结果，不展开背景长文。 |
| 执行管理或运维任务，需要操作者权限、环境判断或恢复路径 | operator guide | 按实际影响完成操作、检查结果并处理故障。 |
| 查询接口、命令、字段、输出或错误 | reference | 返回可定位的事实，不承担教学叙事。 |
| 理解影响产品使用的概念或行为 | explanation | 解释使用层面的 why，不进入系统内部设计。 |

面向普通用户的故障恢复通常用 how-to，运维权限与环境判断主导的恢复用 operator guide。
FAQ 是组织形式，先识别每个问题服务的读者结果。同一任务需要的概念、步骤和参数可以
在一个文档内协调；类型不同本身不要求拆文件。独立结果需要不同导航或维护时才考虑
拆分，保留单文件要求与已有有效结构。评审指出实际误用或导航问题，不自动整理文件。
同一产品可交付多个使用文档，分别验证并保留独立结果。跨文档同步由宿主协调。

共享的范围、示例、空章节、权限和高影响操作边界由 `SKILL.md` 维护；以下只补充
各文档类型特有的内容检查。

## Tutorial

- 从读者可满足的起点开始，步骤递进建立目标能力。
- 每个阶段给出动作和可观察结果。
- 只引入当前阶段需要的概念和 reference 链接。
- 未实际执行的学习路径标为未验证。
- 受保护动作未满足共用检查的安全证据时，不把“学习”当成让新手执行该动作的理由。

## How-to

- 标题和开头说明一个具体结果。
- 步骤按依赖、权限、side effect 或恢复需要排序。
- 每一步包含一个主要动作和适用的观察结果。
- 失败会改变结果时，给出诊断入口和恢复动作。
- Troubleshooting how-to 从可观察 symptom 开始，以恢复或明确升级结束。

## Operator Guide

- 在受保护动作前写明操作者权限、环境、影响范围和风险。
- 在不可逆或高影响步骤前提供检查点和停止条件。
- 给出验证当前状态的方法，以及可执行的 rollback、recovery 或 escalation 边界。
- 不把文档中的权限说明当作执行者已经获得该权限。

## Product-Use Explanation

- 明确要解释的产品行为或使用概念及其适用 baseline。
- 用已核对事实解释 why、边界和用户可观察影响。
- 不伪装成步骤，也不扩展到架构或详细设计评审。

## CLI/API Reference 字段合同

CLI/API reference 必须能恢复以下适用信息；可通过公共说明或引用共享，不要求每个条目
重复字段。概念词汇表不强套 endpoint 合同。不适用项只有省略会误导时才说明，缺证据标明缺口：

1. canonical identifier 与用途。
2. 适用 baseline、版本或 availability。
3. syntax、command shape 或 endpoint 与 method。
4. 输入、参数或明确的无输入状态。
5. 输出、response 或可观察结果。
6. 已知错误、失败行为或 exit/response 状态。
7. 作者能定位支持每组事实的 governing source 或验证证据；仅当用户、仓库合同要求，
   或读者需要该来源才能正确使用接口时，才把 provenance 写进交付文档。

仅在目标 surface 适用时加入：

- 访问受控时的 authentication、authorization 和 permissions。
- API 的 headers、request body、response schema、pagination 或 rate limit。
- CLI 的 environment、configuration、interactive behavior 和 exit codes。
- 能由证据支持且可消除用法歧义的示例。
- 已知 limits、compatibility、deprecation 和相关任务入口。

全文 review 检查全部适用信息，报告会影响使用的缺失、歧义或来源冲突；限定评审只检查
指定内容和必要依赖，并简述覆盖范围，不输出无关字段的逐项“不适用”清单。
