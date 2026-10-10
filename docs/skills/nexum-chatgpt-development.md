# Nexum ChatGPT Development：Web 环境适配

正式入口：[SKILL.md](../../skills/nexum-chatgpt-development/SKILL.md)。
本包从完整开发 workflow 收敛为 ChatGPT Web + Nexum 场景 guidance；宿主持有任务结果，
通用开发由 [develop-software](develop-software.md) 承担。不是 Nexum 产品架构规范，
不为 Codex 本地执行增加 Nexum 前置依赖。

## 文件责任

| 文件 | 负责 |
| --- | --- |
| SKILL.md | 场景选择、两条资源路由、与通用任务的边界、环境结果报告 |
| references/local-execution.md | 正确 Agent/仓库、上下文刷新、文件分页/版本、进程及未知副作用恢复 |
| references/project-setup.md | Project 配置、生成/评审检查、维护源关联、配套 Skill 发现和授权安装 |
| assets/project-instructions.md | 输出到具体项目的指令模板，不是活跃仓库规则 |

软件需求、设计、计划、测试、Review、Git 交付及日志不再在此重复定义。普通代码任务
只需要 local-execution 分支；不因处于 Web 会话就加载 Project 配置或安装技能。

## 与通用开发的衔接

软件实现、修复、超出原始状态报告的仓库评审、一般软件文档和 AGENTS 工作须读取通用工程合同。
仅连接、报告原始文件/Git 状态或处理 Project Instructions 则不需通用包。通过当前发现
结果或显式仓库来源读取 develop-software；两个包可以不在同一级安装目录。
先验证入口，再读取当前分支必需资源；不假定名称触发自动激活、自动安装或 Codex 语法。
完整 Web 开发安装需验证两个包；仅安装 Nexum 的结果不能宣称软件开发环境完整。
缺包时可以读取已授权的仓库来源，但不得未经安装授权修改个人目录或凭记忆重建规范。

连接、环境诊断或 Project Instructions 草稿可以独立完成。缺失一个确实必需的工程合同
只阻塞依赖它的工程工作，不阻塞独立环境准备；Nexum 离线时也不能把 sandbox 当成本机。
环境就绪不是更大开发目标已经完成，宿主随后继续当前请求剩余的授权工作。

Project Instructions 的生成与评审在可发现时使用 prompt-authoring-spec；仓库要求它而
无法读取则阻塞相应指令工作。无强制依赖的独立场景仍执行包内明确的指令检查，不声称
已完成外部规范评审。保留 Web 专有 API 参数/权限边界，不复制整份通用提示词规范。
联合生成 AGENTS 时，只有维护源在仓库内实际存在、适合目标读者且写入获准才增加相对路径指针；
这个字段不进入通用 AGENTS 模板，也不声称 UI 已保存。

示例：

```text
通过 Nexum 打开指定 Agent 上的真实仓库，读取适用规则。
使用 nexum-chatgpt-development 处理 Web 环境约束，使用实际可读的 develop-software
完成本次功能、必要文档、测试与 Review；不提交、不推送。
```

```text
只根据已核对的产品和仓库信息起草 ChatGPT Project Instructions。
不要修改 UI 设置或仓库，缺失事实标为草案缺口。
```

仓库规则和工具权限仍优先；示例是调用方式，不是当前会话的额外授权。

## 验证及边界

维护命令沿用[仓库 README](../../README.md)。
[专项测试](../../tests/nexum-chatgpt-development/test_package.py)验证可达资源图、负例及
Project Instructions 模板；通用 AGENTS 和日志模板测试已迁入 develop-software 测试。
[场景集](../../tests/nexum-chatgpt-development/scenarios.md)覆盖正确目标、缺失能力、未知
操作结果和独立输出。结构检查、模型决策试跑、真实 Nexum 操作、ChatGPT UI 验证分开记录。

2026-10-10 核对 [OpenAI Projects 文档](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt)
及当次 Nexum 工具 schema。UI/记忆步骤仍要求执行时核对当前文档与真实设置；普通 Project
组织不构成已验证的记忆隔离，禁用记忆不会因本 Skill 被自动开启。

本次改仓库不会自动更新个人 Skill 目录、已部署的 AGENTS 或 ChatGPT Project Instructions。
原软件通用流程和历史验证请按[迁移说明](develop-software.md)查找，不能拿旧结果证明新包。

配套发现、缺失资源和独立指令产物的实际观察见
[回归场景](../../tests/develop-software/regression-scenarios.md)与
[本轮证据](../../tests/evidence/2026-10-10-software-hardening.json)；模拟发现不等于真实安装验收。
