# Agent Skills

本仓库维护可独立使用的 Agent Skills。正式入口位于 `skills/<name>/SKILL.md`，
编写规则见 [AGENTS.md](AGENTS.md)。按当前任务选择 Skill，读取它按条件引用的资源。

## 按结果选择

| 当前要完成的结果 | Skill | 主要职责边界 |
| --- | --- | --- |
| 编写或评审模型指令 | [prompt-authoring-spec](skills/prompt-authoring-spec/SKILL.md) | 指令必要性、归属、表达与自检 guidance，宿主持有交付 |
| 编写或评审 Skill | [skill-authoring-spec](skills/skill-authoring-spec/SKILL.md) | Skill 合同 guidance，与提示词规范共用 |
| 区分文档类型、核对共性质量或单文档生命周期 | [software-doc-writing-standards](skills/software-doc-writing-standards/SKILL.md) | 分类/质量/管理 guidance，不接管具体正文 |
| 产品要求、约束和验收 | [software-requirements-spec](skills/software-requirements-spec/SKILL.md) | 单份需求文档 |
| 技术结构、行为合同和 ADR | [software-design-spec](skills/software-design-spec/SKILL.md) | 单份设计文档 |
| 实施计划、路线图与完成证据 | [software-development-plan](skills/software-development-plan/SKILL.md) | 独立计划单元、内部阶段与总览分开判断 |
| 安装运行、操作方法、接口查询 | [software-usage-docs](skills/software-usage-docs/SKILL.md) | 单份使用文档正文；多文档变更由同步 Skill 协调 |
| 一次变更影响多份文档 | [sync-software-docs](skills/sync-software-docs/SKILL.md) | 多文档协调含创建/更新，正文共用对应类型 Skill |
| ChatGPT Web 通过 Nexum 开发本地项目 | [nexum-chatgpt-development](skills/nexum-chatgpt-development/SKILL.md) | 特定环境的完整开发工作流 |
| 通过 Nexum 控制用户本地浏览器状态 | [nexum-browser](skills/nexum-browser/SKILL.md) | Browser Runtime capability，不接管代码修改或上层任务 |
| 运营 Nexum 增长、渠道、社区和用户转化 | [nexum-operations](skills/nexum-operations/SKILL.md) | 运营工作流；产品开发仍由开发工作流负责 |

需求定义产品承诺，设计定义技术合同，计划安排工作与验收，指南说明使用，日志记录历史。
目标项目已有目录和职责优先；其他项目示例不自动成为通用约定。

一项请求可共用多个 Skill。Skill 的职责结束后，宿主继续该请求已授权的剩余步骤；
只读评审、真正的审批和工具权限保持各自边界。分发包各自包含运行所需资源，不依赖
本仓库 README 或测试文件补全行为。各 Skill 的许可按其已有声明保留。

## 维护验证

在仓库根目录运行，Python 依赖仅用于维护测试，不进入 Skill 的运行环境：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python -m unittest discover -s tests/nexum-chatgpt-development -v
git diff --check
```

Windows 使用 `.venv/Scripts/python.exe`。检查覆盖全体包的官方格式、资源路由、路径
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
Nexum 工作流用法见[专项说明](docs/skills/nexum-chatgpt-development.md)。
