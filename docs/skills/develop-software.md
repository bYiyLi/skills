# Develop Software：单一通用工程入口

正式入口：[SKILL.md](../../skills/develop-software/SKILL.md)。
本文件记录维护设计和迁移依据，不是分发包需要另外加载的运行规范。

## 目标与责任

将原六个软件文档 Skill 与 Nexum 中的通用开发规则整合为一个可独立分发的工程工作流。
它拥有当前请求限定的软件项目结果；代码、需求、设计、计划和使用文档是同一软件项目
不同事实的载体。文档请求可以是完整任务，也可以是更大实施任务的中间产物。

主类型选择 workflow：检查当前状态、确定依赖、执行当前授权部分、根据新证据调整并
完成请求结果。不是按“软件”一词无限收集能力，也不是只派发下游 Skill 的 router。
普通写作、无软件项目目标的文档工作，以及宿主能力配置不因此纳入通用工程范围。

完整任务只有一个完成边界：请求与仓库合同确定的结果。单独写计划不会启动实施；
实现请求也不会在需求、设计、计划或脚手架完成后提前交付。内部路由不是用户审批。

## 文件职责与加载设计

| 文件 | 拥有的判断 | 不承担的内容 |
| --- | --- | --- |
| SKILL.md | 目标/权限、来源、任务分支、精确路由、连续执行和结束条件 | 专业检查清单、模板或宿主调用教程 |
| references/lifecycle.md | 新建/接管、工程就绪、增量调度、变更影响和版本范围验收 | 固定七阶段、每阶段一个 Phase、全局项目状态机 |
| references/repository-contract.md | 工程结构、工具/依赖、真实质量命令、README/AGENTS | ChatGPT UI、业务架构百科、虚假初始化门禁 |
| references/verification.md | 现有实施、测试、Review、修复、复验及证据闭环 | 为每类任务跑全套检查、用绿测证明零缺陷 |
| references/requirements.md | 产品承诺、来源、适用类别和验收 | 技术实现和工作进度 |
| references/design.md | 技术合同、条件视图、设计驱动与决策 | 产品授权、任务台账和开发日志 |
| references/planning.md | 独立计划/内部阶段/roadmap、工作与完成证据 | 从目录名推导 Phase 数量、改弱验收 |
| references/usage-docs.md | 教程、指南、CLI/API 查询及使用解释 | 执行文档里的生产操作 |
| references/documentation.md | 内容分类、共同语义质量、研究来源、指令产物检查 | 文件移动/归档或第二套实施流程 |
| references/doc-management.md | 写入、路径、metadata/状态、归档删除与持久化验证 | 纯内容分类及只读正文评审 |
| references/doc-sync.md | 多文档变化分析、同步计划与实际同步的区别 | 无条件创建全部文档类型 |
| references/journal.md | 有需要时记录日期、决定、检查与历史 | 替代当前设计或计划、只读评审写日志 |
| references/git-delivery.md | 已授权 Git/CI/release/deploy 的边界与证据 | 自动授权发布或推送 |
| assets/ | 请求需要的新文档、AGENTS 和日志模板 | 当前会话的治理指令、必须创建的文件清单 |

主入口直接列出全部一级参考。只有当前工作条件命中才读取；参考内按创建类型和现有
模板是否适用，进一步链接具体 assets。没有“再找一个路由 Skill”的交接。
一般路径是 `SKILL.md → 专业 reference → 可选 asset`；references 不是一次性全量上下文。
原来的五份文件管理合同仅由 doc-management.md 维护。只读内容评审不加载持久化规则，
机械编辑和纯状态核对不加载专业正文合同；内容写入按需要同时应用两者。资源可达不等于
模型实际使用，必须从执行轨迹核对加载。

此次补强保留原模板，但将 SRS 的 stakeholders/actors、设计 drivers 中的 stakeholder
concerns 放回必读专业正文；使用仓库自有模板时也不能遗漏。同步候选发现包含仅风险或
影响范围变化，外部研究入设计/日志时记录来源 URL、版本或访问日期、适用性与限制。
不新增研究报告、人工审批或每方一个单独文档。

## 如何推进项目

新项目先确定当前产品结果和验收，再完成首批工程工作依赖的架构决策、可复现运行和
真实验证基础。技术不确定性可先做有界验证，不要求一次完成未来所有设计。

增量开发以当前设计和开发计划为依据。已有文档足够就直接执行；合同变化先维护受影响
设计，工作/验收状态变化更新计划。实施和验收复用原有闭环，完成一个增量后继续剩余
授权工作。不同模块可以处于不同状态，不因局部返工重启整个项目。

工程初始化、版本功能验收、提交、推送、CI、发布和部署分别取证。缺必需依赖不假装
通过，也不阻断无关且已获授权的准备。目标完成后停止，不擅自发起下一版本或后台开发。

## 原入口迁移映射

| 原入口/内容 | 当前归属 |
| --- | --- |
| software-requirements-spec | requirements.md + 原需求模板 |
| software-design-spec | design.md + 原设计模板 |
| software-development-plan | planning.md + 原单计划和 roadmap 模板 |
| software-doc-writing-standards | documentation.md（内容）+ doc-management.md（文件/状态） |
| software-usage-docs | usage-docs.md + 原使用文档模板 |
| sync-software-docs | doc-sync.md + 原同步计划模板 |
| Nexum 通用仓库/质量规则 | repository-contract.md、verification.md、git-delivery.md |
| Nexum 通用日志/AGENTS | journal.md、AGENTS.md.tmpl、daily-log.md |
| Nexum 特定连接和 Project 配置 | 保留在 nexum-chatgpt-development |

旧六个入口从正式 skills 集合移除，不创建六个转发壳，避免仍被误选和继续维护重复规则。
原许可证一致，合并包保留 Private Use License；迁移不等于重新许可、公开发布或个人安装。
历史日志与观察数据保持其历史语义；旧实现可从迁移前 Git 版本恢复。

维护脚本/校验器和试跑数据位于 tests，而非分发包。无需额外软件文档 Skill，也不要求
开发执行时安装本仓库的 authoring 工具。宿主或目标仓库明确要求的编写规范仍须遵守。

## 验证设计

结构测试检验官方格式、所有资源可达、路径大小写、隔离分发、二级模板路由、缺失/孤立/
越界资源以及模板实例化。资源图可达不证明模型真的按条件加载；后者查看独立试跑轨迹。

保留既有计划单元、单文件指南、文档同步、未知副作用与只读边界用例，增加新项目完整
交付、仅初始化、主任务连续执行、适配器缺失依赖等场景。原始任务与预期答案分开，
独立模型只接收实际任务、必要输入和候选包。文本评审、结构测试和模型观察分别报告。

全量命令见[仓库 README](../../README.md)，专属场景见
[develop-software 场景](../../tests/develop-software/scenarios.md)。

## 依据与适用性

2026-10-10 核对 [Agent Skills specification](https://agentskills.io/specification)：
metadata 用于发现，主入口在选择后加载，资源按任务需要读取。沿用小主入口与浅层路由，
不将篇幅预算误称为强制格式限制，也不从链接存在推导自动激活保证。

同日核对用户指定的 [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)：
采用连续完成已授权目标、查明指令冲突和按真实变化选择验证的指导。API 参数、异步
函数和子 Agent 示例不成为该包的默认权限或宿主能力。具体能力仍以当前工具为准。

本次实际审阅、修正及验证结果见 [2026-10-10 日志](../vlog/2026-10-10.md)与
[持久证据](../../tests/evidence/2026-10-10-software-consolidation.json)，不将设计预期视为运行证明。

能力回归补强的输入和边界见[专项场景](../../tests/develop-software/regression-scenarios.md)，
实际结果、失败与候选哈希见[本轮证据](../../tests/evidence/2026-10-10-software-hardening.json)。
