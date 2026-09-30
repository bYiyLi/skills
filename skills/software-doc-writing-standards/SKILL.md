---
name: software-doc-writing-standards
description: 为软件文档提供跨类型分类、来源、共同质量及单文档位置/生命周期审查。用于类型混杂、共性质量或管理判断；具体正文交付及多文档同步由对应 Skill 负责。
---

# Software Documentation Writing Standards

在宿主任务内提供分类与质量判断，文件操作和最终交付仍由宿主负责。保留当前请求
模式；只读评审不写文件，分类建议不代表已调用或完成另一个 Skill。

## 按判断加载资源

| 当前判断 | 读取 |
| --- | --- |
| 类型未知、混杂，或标题与读者目标不符 | [references/doc-taxonomy.md](references/doc-taxonomy.md) |
| 证据、事实与假设、追溯或共同质量 | [references/quality-rules.md](references/quality-rules.md) |
| 仓库落盘、命名、状态、移动、归档或删除 | [references/doc-management-contract.md](references/doc-management-contract.md) |

独立单文档管理/生命周期判断读取本包 management contract。若同一任务已由对应正文
Skill 加载其相同 management contract，复用那一份，不重复加载本包副本。
只加载命中条件的资源。缺少必需资源时报告准确路径和未覆盖判断，不从其他资料补造
该合同；继续有依据的独立部分。

## 分类不决定文件数量

先确定请求的读者结果及已有文档职责，再按 taxonomy 判断内容类型。为同一任务服务的
概念说明、步骤和参数引用可以属于同一文档；小节类型不同本身不是拆文件的理由。
独立读者结果需要分别导航和维护时再考虑拆分，保留用户指定的数量、格式及有效结构。
单文件含多种结果时按目标分区；只指出实际导航问题，不机械附加“组合有局限”的套话。

单一文档交给对应类型 Skill；同一变更的多文档同步交给 `sync-software-docs`。
未匹配的研究、日志或其他产物保留其实际职责，不强塞入分类表。先查请求、内容和仓库，
只有仍会改变结果的未决分类才询问。

## 应用与交付

评审给出具体位置、可达读者任务、错误判断、依据和最小修正；缺事实证据不阻止文本
评审，但不能把草案或文本核对说成实际行为通过。没有发现时说明覆盖和未验证部分。
交付分类与质量判断后继续宿主已授权任务，不因 Skill 切换增加批准节点。
