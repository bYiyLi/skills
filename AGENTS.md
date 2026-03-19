# Personal Skill 仓库规范

## 1. 仓库目标

- 这个仓库是个人 Agent Skills 源仓库。
- `skills/` 是唯一真源。
- 安装统一交给官方 CLI 处理。
- 跨平台、跨客户端的安装命令统一使用 `npx skills add ...`。
- 根目录 `AGENTS.md` 只定义本仓库流程，不替代 Agent Skills 标准。

## 2. 制作规则

### 2.1 目录合同

- 每个正式 skill 都放在 `skills/<skill-name>/`。
- 每个正式 skill 必须包含 `SKILL.md`。
- 每个正式 skill 必须包含 `LICENSE.txt`。
- 每个正式 skill 必须包含 `evals/evals.json`。
- `scripts/`、`references/`、`assets/` 按需创建。
- 不要在 skill 目录中加入 `README.md`。
- 不要在 skill 目录中加入 `CHANGELOG.md`。
- 不要在 skill 目录中加入人类向的杂项说明文件。
- 新 skill 从 `templates/skill/` 复制起步。

### 2.2 SKILL.md frontmatter

- `name` 必填，并且必须和目录名一致。
- `description` 必填。
- `description` 先用中文说明做什么、什么时候用。
- `description` 同时保留必要的 English keywords。
- `license` 在本仓库里视为必填。
- `license` 固定写成 `./LICENSE.txt`。
- `compatibility` 只在确有环境要求时写。
- `metadata` 只允许字符串键和值。
- `metadata` 只放仓库内部约定信息。
- 优先使用 `owner`、`status`、`last-reviewed`、`source-bucket` 这类键。
- v1 不使用 `allowed-tools`。
- 不要加入未约定的 frontmatter 字段。

推荐骨架:

```md
---
name: your-skill-name
description: >
  用中文先说明这个 skill 做什么,
  在什么情况下触发,
  再补必要的 English keywords.
license: ./LICENSE.txt
metadata:
  owner: your-name
  status: draft
  last-reviewed: 2026-03-19
---
```

### 2.3 SKILL.md body

- 用祈使句或操作式语气写。
- 主文件尽量控制在 300-500 行内。
- 主文件只保留流程、判断标准、关键 gotchas、最小示例。
- 细节资料下沉到 `references/`。
- 只有重复复用的脚本才放进 `scripts/`。

### 2.4 evals 约定

- 每个 skill 都必须有 `evals/evals.json`。
- `trigger_queries` 至少 4 条。
- `trigger_queries` 里 `should_trigger: true` 至少 2 条。
- `trigger_queries` 里 `should_trigger: false` 至少 2 条。
- `output_cases` 至少 2 条。
- 每个 `output_cases` 条目都必须写 `comparison_mode: "with-vs-without-skill"`。
- JSON 结构参考 `schemas/skill-evals.schema.json`。
- JSON 模板参考 `templates/skill/evals/evals.json`。

## 3. 工作流

1. 先收集真实高频 prompt。
2. 不要先拍脑袋造 skill。
3. 从真实任务里选择 pilot。
4. pilot 至少横跨开发、研究整理、知识写作三个方向。
5. 只有任务会重复出现时，才创建正式 skill。
6. 先写 `SKILL.md`、`LICENSE.txt`、`evals/evals.json`。
7. 再按需补 `scripts/`、`references/`、`assets/`。
8. 完成后运行结构校验。
9. 发现性和安装性验证统一使用 `npx skills`。

## 4. 完成前必跑命令

- `node scripts/validate-skills.mjs`
- `npx skills add ./skills --list`
- `npx skills add ./skills -a codex -y`
- `npx skills list -a codex --json`

如果目标不是 Codex, 把 `codex` 换成对应客户端名称。

## 5. 编辑边界

- 不要实现仓库私有安装器或镜像安装层。
- 不要提交缺少 `LICENSE.txt` 的 skill。
- 不要提交缺少 `evals/evals.json` 的 skill。
- 没有真实 prompt 时，只更新规范和模板。
- 不要在 v1 中引入客户端私有扩展字段。
- 不要在 v1 中使用 `allowed-tools`。
- 不要让模板占位值进入正式 skill。

## 工具管理区

<!-- tool-managed-start -->
<!-- tool-managed-end -->
