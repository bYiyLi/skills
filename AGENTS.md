# Personal Agent Skills

本项目用于开发、验证和发布 Agent Skills。每个正式 Skill 都维护在 `skills/<skill-name>/`。

创建或修改 `skills/<skill-name>/` 前，必须同时使用 `skill-creator` 和本项目的 `skill-authoring-spec`（`skills/skill-authoring-spec/SKILL.md`）。涉及编写、修改或评审模型可见指令时，还必须使用 `prompt-authoring-spec`（`skills/prompt-authoring-spec/SKILL.md`）。创建或修改时，如果当前要求的任一 Skill 不存在或无法读取其完整指令，必须停止写入。明确的只读评审可以报告已覆盖范围，但必须把缺失 Skill 的规则标为未评审，不得声称完成完整评审。
