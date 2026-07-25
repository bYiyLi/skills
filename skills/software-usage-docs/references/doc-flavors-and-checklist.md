# Usage Document Flavors And Checks

本 reference 定义 `software-usage-docs` 内部的文档类型决策和内容检查，不定义目标
仓库的路径、metadata、生命周期或外部产品事实。文档中的事实仍以目标任务核对后的
governing source 为准。

## 选择单一读者目标

| 读者的主要目标 | 文档类型 | 结果边界 |
| --- | --- | --- |
| 从零建立一项产品使用能力 | tutorial | 完成一条递进学习路径，不承担完整参数查询。 |
| 完成一个已知任务 | how-to | 到达一个可观察结果，不展开背景长文。 |
| 执行需要操作者权限、执行前检查点，或 rollback、recovery 或 escalation 边界的管理或运维任务 | operator guide | 完成受权限和风险约束的操作，并能检查和恢复。 |
| 查询接口、命令、字段、输出或错误 | reference | 返回可定位的事实，不承担教学叙事。 |
| 理解影响产品使用的概念或行为 | explanation | 解释使用层面的 why，不进入系统内部设计。 |

面向普通用户的 troubleshooting 按恢复目标写成 how-to；面向管理员或运维的
troubleshooting 按 operator guide 处理。FAQ 只是组织形式：每个问题按上表判型；
不同目标默认拆成不同 artifact。用户明确要求单一 artifact 时，可以按类型和读者目标清楚
分区，但每个分区仍遵守自己的结果边界，并说明组合带来的导航限制。

如果一份现有文档混合多个目标，review 应指出边界；create 或 revise 只在用户授权
范围内拆分，明确要求保留单文件时改为建立上述分区。一个请求明确要求同一产品 surface 的多个 usage/reference artifacts 时，
分别选择类型、生成结果和验证；一个 artifact 失败不得抹去其他独立结果。由同一产品
变更驱动的跨 requirements、design、usage 等类别同步不属于本 reference。

## 共用检查

- 内容保持在所选类型的结果边界内，不替其他文档类型完成独立结果。
- 前置条件只包含完成当前读者目标所需的信息。
- 示例不提供规则之外的唯一必需行为，也不把偶然值写成固定要求。
- 不适用的章节被删除，不用空标题制造已覆盖的假象。
- 动作会改变远端或共享持久化状态、权限或安全边界、生产状态，或使数据难以恢复时，
  只有权限、影响范围、执行前检查点以及 rollback、recovery 或 escalation 均有适用
  证据，才把它写成可执行步骤。否则只记录语法和 gap，或把教程/任务限制在已知不会
  应用变更的预演、查询或检查路径。

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

以下字段对 reference artifact 必需；当目标 surface 没有某项时，明确写“不适用”，
当证据不足时写明 gap，不编造值：

1. canonical identifier 与用途。
2. 适用 baseline、版本或 availability。
3. syntax、command shape 或 endpoint 与 method。
4. 输入、参数或明确的无输入状态。
5. 输出、response 或可观察结果。
6. 已知错误、失败行为或 exit/response 状态。
7. 每组事实的 governing source 或验证证据。

仅在目标 surface 适用时加入：

- 访问受控时的 authentication、authorization 和 permissions。
- API 的 headers、request body、response schema、pagination 或 rate limit。
- CLI 的 environment、configuration、interactive behavior 和 exit codes。
- 能由证据支持且可消除用法歧义的示例。
- 已知 limits、compatibility、deprecation 和相关任务入口。

全文 review 时逐项报告缺失、不适用、证据不足或与 governing source 冲突；用户明确限定
范围时，只检查指定字段和判断它所需的依赖，把其他字段列为 out-of-scope。不要用字段数量
代替内容正确性判断。
