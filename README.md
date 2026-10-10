# Agent Skills

本仓库维护职责明确、按需组合的 Agent Skills。正式入口位于 `skills/<name>/SKILL.md`，
编写规则见 [AGENTS.md](AGENTS.md)。按当前任务选择 Skill，读取它按条件引用的资源。

## 按结果选择

| 当前要完成的结果 | Skill | 主要职责边界 |
| --- | --- | --- |
| 编写或评审模型指令 | [prompt-authoring-spec](skills/prompt-authoring-spec/SKILL.md) | 指令必要性、归属、表达与自检 guidance，宿主持有交付 |
| 编写或评审 Skill | [skill-authoring-spec](skills/skill-authoring-spec/SKILL.md) | Skill 合同 guidance，与提示词规范共用 |
| 开发、修复、评审软件项目，或维护需求、设计、计划、使用文档与 AGENTS | [develop-software](skills/develop-software/SKILL.md) | 通用工程工作流；按请求范围和包内条件资源执行 |
| ChatGPT Web 通过 Nexum 访问环境、配置 Project 或发现/安装 Skill | [nexum-chatgpt-development](skills/nexum-chatgpt-development/SKILL.md) | 场景 guidance；宿主持有开发结果，不重复通用流程 |
| 通过 Nexum 控制用户本地浏览器状态 | [nexum-browser](skills/nexum-browser/SKILL.md) | Browser Runtime capability，不接管代码修改或上层任务 |
| 运营 Nexum 增长、渠道、社区和用户转化 | [nexum-operations](skills/nexum-operations/SKILL.md) | 运营工作流；产品开发仍由开发工作流负责 |

需求定义产品承诺，设计定义技术合同，计划安排工作与验收，指南说明使用，日志记录历史。
目标项目已有目录和职责优先；其他项目示例不自动成为通用约定。

一项请求可共用多个 Skill。Skill 的职责结束后，宿主继续该请求已授权的剩余步骤；
只读评审、真正的审批和工具权限保持各自边界。各包包含自身职责所需资源；条件依赖在
包内明确声明，不靠本仓库 README 或测试文件补全行为。各 Skill 许可保持原有声明。

Web 软件开发使用 `nexum-chatgpt-development` 与实际可读的 `develop-software` 配套；
只连接环境、查看原始状态或维护 Project Instructions 可以只用 Nexum 包。完整开发安装
应验证两个包及当前任务所需资源；通用开发包本身不依赖 Nexum。包名不会触发自动安装。

## 维护验证

在仓库根目录运行，Python 依赖仅用于维护测试，不进入 Skill 的运行环境：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python -m unittest discover -s tests/nexum-chatgpt-development -v
git diff --check
```

Windows 使用 `.venv/Scripts/python.exe`。检查覆盖全体包的官方格式、可达资源图、路径
大小写、本地链接、Codex 调用 metadata 和模板产物；Nexum 检查另含缺失、孤立、越界
资源与无效模板的负例。[CI](.github/workflows/skills.yml) 运行相同结构测试，并检查
提交内容的空白错误。

[集合场景](tests/scenarios.md)用于语义评审，不能替代模型运行证据。新增或修改 Skill
后先检查声明、正文、references、assets 和调用提示词是否一致，再按实际行为变化
选择必要验证，不用匹配提示词原句的测试冒充行为验证。

最新逐 Skill 审核与验证见 [2026-09-28 记录](docs/vlog/2026-09-28.md)及
[保留证据](tests/evidence/2026-09-28-skills-review.json)；历史集合调整见
[2026-09-19 记录](docs/vlog/2026-09-19.md)。
提示词规范的职责、自检与试跑更新见 [2026-09-29 专项记录](docs/vlog/2026-09-29.md)。
通用软件工程及旧入口迁移见[develop-software 说明](docs/skills/develop-software.md)；
Web/Nexum 场景用法见[专项说明](docs/skills/nexum-chatgpt-development.md)。
测试数据和历史记录中的旧名称保留其当时语义，不表示旧入口仍在分发；个人安装不由仓库修改自动更新。

本次软件领域整合与验证见 [2026-10-10 记录](docs/vlog/2026-10-10.md)及
[保留证据](tests/evidence/2026-10-10-software-consolidation.json)。

整合后的能力回归补强见 [2026-10-10 日志](docs/vlog/2026-10-10.md)、
[专项回归场景](tests/develop-software/regression-scenarios.md)和
[独立保留证据](tests/evidence/2026-10-10-software-hardening.json)。
