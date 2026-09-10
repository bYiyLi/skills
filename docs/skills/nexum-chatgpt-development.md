# Nexum ChatGPT Development

面向 **ChatGPT Web + Nexum + 本地仓库** 的开发 Skill。它把一个明确的项目开发任务
推进到有证据的结果，覆盖初始化、实现、修复与只读评审；不是 Nexum 产品设计，
也不是 Codex CLI 工作流。正式入口：
[SKILL.md](../../skills/nexum-chatgpt-development/SKILL.md)。

## 内容与职责

主文件只保留任务边界、Nexum 上下文、资源路由、执行闭环和结束条件。
需要某类工作时才读取对应资料，不要求每次加载整套规范。

| 资源 | 解决的问题 |
| --- | --- |
| references/project-setup.md | ChatGPT Project 隔离、指令来源、UI 配置与 Skill 发现的证据 |
| references/repository-contract.md | README、AGENTS、设计/计划/历史的职责，真实质量命令 |
| references/documentation.md | 设计变更、开发状态、按天记录的书面 vlog |
| references/verification.md | 基线、局部到整体验证、review/fix 循环、验收与停止条件 |
| references/git-delivery.md | 保护用户修改，独立处理 commit/push/CI/release/deploy |
| references/prompt-writing.md | 可执行提示词、上下文与指令分离、输出与证据规范 |
| assets/ | Project Instructions、AGENTS.md.tmpl、daily-log 三份输出模板 |

新项目默认使用 `README.md`、`AGENTS.md`、`docs/design.md`、`docs/development/`、
`docs/vlog/` 和 `docs/chatgpt-project.md`。已有项目沿用自己的真源和日志路径，
不为了目录统一迁移文件。设计记录当前合同，vlog 记录历史，不相互替代。

## 完整目标与连续执行

完成范围由用户的实际目标、已约定范围和仓库验收决定，不用“最小实现”或补丁大小
限制交付。需要的跨模块集成、错误处理、测试、设计和开发文档都属于完整结果。
用户明确只要原型、某个子阶段或只读评审时，完成该范围，不扩大成整个产品。

AI 自行组织编辑与验证单元，在同一授权任务内持续推进。一次修改、一次测试、
一个子阶段或一个专项 Skill 的结束只是检查点，不要求用户再次说“继续”。
验证按受影响行为和必要门禁选择；没有新修改、失败或具体疑点时，不机械重复。

宿主与工具权限仍然有效。工作流默认规则不能覆盖用户的明确任务指令；必要审批前
先完成不依赖审批的已授权准备。指令导致暂停、额外确认或遗漏工作时，说明具体
文件位置、原句、受影响动作，并区分明确规则与 AI 自己的解释。

## 在 ChatGPT Web 使用

在目标 ChatGPT Project 内明确任务，连接 Nexum，并让当前会话读取正式 Skill。
通过 Nexum 当前支持的发现机制加载时，以 `project.open` 实际返回的 Skill 路径为准。
尚未加入发现目录时，可以打开本 skills 仓库，明确要求读取上述正式入口及所需资料；
这只是显式加载，不代表已经安装到所有项目。

示例请求：

```text
通过 Nexum 读取 nexum-chatgpt-development Skill，按目标仓库规范完成 Phase 03。
本任务授权实现、测试、review 和必要文档同步，不包含 commit 或 push。
```

```text
通过 Nexum 使用 nexum-chatgpt-development，初始化这个项目的开发规范。
生成项目专用的 ChatGPT Project Instructions、README、AGENTS 和必要 docs。
已有内容先检查再适配，不能操作的 ChatGPT UI 配置明确标为待完成。
```

GitHub 上有文件、Nexum 能发现 Skill、会话已经读取 Skill、实际任务执行成功，是不同状态。
本次交付不自动改变个人 Skill 目录或现有 ChatGPT Project 设置。

## 验证与维护

运行时包没有脚本或 Python 依赖。以下依赖仅用于维护者检查，隔离在本地虚拟环境：

```sh
python3 -m venv .venv/nexum-chatgpt-development
.venv/nexum-chatgpt-development/bin/python -m pip install -r tests/nexum-chatgpt-development/requirements.txt
.venv/nexum-chatgpt-development/bin/skills-ref validate skills/nexum-chatgpt-development
.venv/nexum-chatgpt-development/bin/python -m unittest discover -s tests/nexum-chatgpt-development -v
```

Windows 使用虚拟环境的 `Scripts/python.exe` 和对应 `skills-ref` 可执行文件。
使用 uv 创建的无 pip 环境时，可以用 `uv pip install --python <venv-python> -r ...`。
这两条安装路径只用于维护者环境，不是 Skill 对用户项目的前提。

[测试](../../tests/nexum-chatgpt-development/test_package.py) 覆盖官方格式、直接资源路由、
路径大小写、缺失/孤立/越界资源、模板字段与临时输出。主入口 150 行是本包维护预算，
不是 Agent Skills 格式强制上限。CI 只检查这个 Skill，复用这些命令。

[场景集](../../tests/nexum-chatgpt-development/scenarios.md) 用于闭合合同评审，
不作为真实模型行为测试的证明。需要验证模型选择、长任务表现或 UI 操作时，
在相应宿主上独立测试，并区分观察结果与预期答案。

## 规范来源与证据范围

格式依据 [Agent Skills specification](https://agentskills.io/specification)，
结构验证使用该项目的 `skills-ref`，开发依赖固定在已检查的上游 commit。
编写时同时应用本仓库的 skill-authoring-spec、prompt-authoring-spec 和可用的
skill-creator 指导；分发后的 Skill 不强迫使用者安装这些编写工具。

提示词参考用户指定的
[OpenAI prompt-engineering guide](https://help.openai.com/zh-hans-cn/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)：
前置明确指令、分隔上下文、定义输出、使用有必要的例子与正向动作要求。
API 参数建议不转换成 ChatGPT Web 的虚构控制项。

2026-09-10 复核用户指定的
[OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)，
采用与本场景相关的持续完成、指令冲突诊断和适度验证原则；没有把 API 参数、
异步工具或子 Agent 示例写成本 Skill 的默认能力或权限。

Project UI/记忆行为以当前
[OpenAI Projects 文档](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt)
和实际设置为准；普通项目组织不等于已验证的跨项目记忆隔离。
Nexum 操作根据本次实际读取的工具 schema，以及后续调用时的当前 schema。
提示词不能替代宿主权限与安全控制。

本 Skill 的职责类型为 workflow：拥有当前请求的项目开发结果，不是只分发任务的 router。
名称沿用已确认的产品/场景词，避免新增一个含义重叠的通用开发 Skill。
评审与修订记录见 [每日日志](../vlog/2026-09-10.md)。
