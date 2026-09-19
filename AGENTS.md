# Personal Agent Skills

本项目用于开发、验证和发布 Agent Skills。每个正式 Skill 都维护在 `skills/<skill-name>/`。

创建或修改 `skills/<skill-name>/` 前，必须同时使用 `skill-creator` 和本项目的 `skill-authoring-spec`（`skills/skill-authoring-spec/SKILL.md`）。涉及编写、修改或评审模型可见指令时，还必须使用 `prompt-authoring-spec`（`skills/prompt-authoring-spec/SKILL.md`）。创建或修改时，如果当前要求的任一 Skill 不存在或无法读取其完整指令，必须停止写入。明确的只读评审可以报告已覆盖范围，但必须把缺失 Skill 的规则标为未评审，不得声称完成完整评审。

集合入口与职责见 [README.md](README.md)。修改选择边界时，同步受影响的 description、
正文、资源和调用提示词；包内资源必须可独立分发，不依赖维护文档补全指令。

维护验证使用 README 中的两组 unittest 命令和 `git diff --check`。场景推演、结构检查
与独立模型试跑分别报告，不把任何一种说成其他验证。保留现有许可与用户工作；
修改、验证、提交、推送和安装分别以实际结果为准。
