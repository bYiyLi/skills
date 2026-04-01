# Software Doc Taxonomy

## Routing Table

先看读者要完成什么，再决定文档类型：

| Reader goal | Preferred doc | What it must answer | What it must not become |
| --- | --- | --- | --- |
| 决定做什么、承诺什么、验收什么 | Requirements | 目标、范围、要求、约束、验收 | 详细实现方案 |
| 解释系统如何组织、为何这样设计 | Design | 驱动、结构、接口、数据、运行时、取舍 | 纯需求清单 |
| 带用户上手并建立技能 | Tutorial | 从零完成一个学习路径 | 参数百科 |
| 帮用户完成某个具体任务 | How-to / usage guide | 前置条件、步骤、结果、回退 | 背景长篇解释 |
| 快速查找接口、命令、字段、错误 | Reference / API docs | 真值表、语法、参数、返回、错误 | 教学叙事 |
| 解释背景、原理、why | Explanation | 原理、上下文、权衡、历史原因 | 任务步骤 |

## Practical Notes

1. “用户手册”通常不是单一类型。
   - 常见做法是把 tutorial、how-to、reference、troubleshooting 放在一个文档集里，而不是塞进同一篇。
2. “详细设计文档”也不是一张图。
   - 至少要覆盖结构、接口、运行时行为、数据与关键异常路径。
3. “需求文档”不等于产品脑暴。
   - 需要有范围、约束、优先级、验收和追溯入口。

## Repository Standard Snapshot

本仓库对软件文档分类采用以下内化口径：

1. 学习型文档和任务型文档分开。
   - 新手建立技能，用 tutorial。
   - 已知目标、要完成任务，用 how-to 或 usage guide。
2. 查询型文档和解释型文档分开。
   - 查参数、接口、字段、错误，用 reference。
   - 讲背景、原理、why，用 explanation。
3. 需求与设计单独成册。
   - requirements 负责“做什么、约束什么、如何验收”。
   - design 负责“如何组织、为何如此、如何落地”。
4. 标题从属于目标。
   - 即使标题叫“开发指南”，如果内容本质上在列接口与错误码，也按 reference 处理。
