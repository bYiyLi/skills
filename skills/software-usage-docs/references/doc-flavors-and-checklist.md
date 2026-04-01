# Usage Doc Flavors And Checklist

## Flavor Router

先问读者最需要什么：

| Need | Doc flavor | Writing posture |
| --- | --- | --- |
| 从零建立技能 | Tutorial | 学习路径、渐进式例子 |
| 完成一个具体任务 | How-to / usage guide | 目标导向步骤 |
| 查询准确事实 | Reference / API docs | 稳定字段、少叙事 |
| 理解背景和 why | Explanation | 概念、上下文、原理 |

## API / Reference Minimum Fields

如果写的是 API/CLI/reference，尽量覆盖：

1. 名称与简短描述
2. 适用版本 / baseline
3. 语法或 endpoint
4. 参数 / headers / auth / permissions
5. 请求与响应结构
6. 错误 / exceptions / exit codes
7. 示例输入输出
8. 限制、兼容性和相关链接

## Procedure Checklist

1. 前置条件、权限、环境是否清楚。
2. 每一步是否只有一个动作。
3. 是否给 expected result 或 checkpoint。
4. 是否写了失败恢复或排障入口。
5. 是否明确版本差异或已知限制。

## Common Failure Modes

1. 教程里塞满 reference 表格。
2. how-to 里掺杂长篇原理解释。
3. API 文档只列 happy path，不列错误和限制。
4. 示例不可复制或未标明版本。
5. 管理员操作文档没写权限、风险或回滚。

## Repository Usage Doc Standard

本仓库对使用说明文档采用以下本地标准：

1. tutorial 用来建立技能，不承担完整参数查询职责。
2. how-to 用来完成一个具体任务，步骤短、动作明确、默认少解释。
3. reference 用来查询准确事实，结构稳定，围绕真实产品面展开。
4. API/CLI reference 至少应覆盖：
   - 名称与描述
   - baseline / version
   - syntax or endpoint
   - parameters / auth / permissions
   - responses or outputs
   - errors / exit codes
   - examples
   - limits / caveats
5. 高风险操作必须补：
   - prerequisites
   - permissions
   - expected results
   - rollback or recovery
