# Design View Set And Checklist

## Minimal View Router

按变更范围选最小必要视图：

| Change scope | Recommended views |
| --- | --- |
| 跨系统 / 平台级变更 | context, container, runtime, deployment, decisions, risks |
| 单特性 / 子系统 | context, component/module, interface, runtime, data, decisions |
| 模块内部重构 | module, interface, failure modes, tests/verification notes |

## What Each View Should Answer

1. Context
   - 这个系统与哪些人、系统、边界相连。
2. Container / Component / Module
   - 主要职责如何分配，边界如何切。
3. Runtime
   - 关键场景下谁先后交互，异常路径怎么走。
4. Data
   - 关键实体、状态变化、持久化与一致性要求。
5. Interface
   - 输入输出、协议、版本、权限、错误和兼容性。
6. Deployment
   - 运行在哪、怎么部署、哪些基础设施会影响质量目标。
7. Decisions / Risks
   - 为什么这么做、放弃了什么、代价是什么。

## Common Failure Modes

1. 只有组件图，没有 runtime 和 failure path。
2. 写了一堆架构名词，但没把 concerns 和 trade-offs 说清。
3. 视图之间互相矛盾，或 as-is / to-be 混写。
4. 没把质量目标和设计联系起来。
5. 没写风险、兼容性、迁移和 technical debt。

## Repository Design Standard

本仓库对软件设计文档采用以下本地标准：

1. 先写 design drivers。
   - stakeholders
   - concerns
   - constraints
   - quality goals
2. 再选视图，不追求把所有图都画一遍。
   - context
   - structure: container / component / module
   - runtime
   - interface
   - data
   - deployment
   - decisions / risks
3. 关键设计必须留下 rationale。
   - 为什么选这个方案
   - 放弃了什么
   - 代价是什么
4. 关键设计元素必须有追溯入口。
   - 能回到 requirement / constraint / quality goal
   - 能前指到 verification / rollout / migration
