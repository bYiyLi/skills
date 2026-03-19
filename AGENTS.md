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
- 类型明确时，优先从对应模板复制起步:
  - `templates/skill-normative/`
  - `templates/skill-tooling/`
  - `templates/skill-process/`
- 类型尚未明确时，先从 `templates/skill/` 基础模板起步，再补全类型信息。

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
- `metadata.skill-type` 在本仓库里视为必填。
- `metadata.skill-type` 只允许 `normative`、`tooling`、`process`。
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
  skill-type: normative
---
```

### 2.3 SKILL.md body

- 用祈使句或操作式语气写。
- 主文件尽量控制在 300-500 行内。
- 主文件只保留流程、判断标准、关键 gotchas、最小示例。
- 细节资料下沉到 `references/`。
- 只有重复复用的脚本才放进 `scripts/`。

### 2.3.1 共享章节合同

- 所有正式 skill 都必须包含以下章节，标题固定使用英文，正文可以中文为主:
  - `Task Fit`
  - `Resources to Load`
  - `Output Standard`
  - `Stop Conditions`
  - `Minimal Examples`
- `Task Fit` 说明该触发与不该触发的边界。
- `Resources to Load` 说明什么情况下读取 `references/`、`scripts/`、`assets/`。
- `Output Standard` 说明最终产物应满足什么标准。
- `Stop Conditions` 说明何时应中止、升级、回退或拒绝。
- `Minimal Examples` 至少给出 1 个正例和 1 个反例或边界例。

### 2.3.2 类型内容合同

- 每个 skill 必须严格匹配一个 `metadata.skill-type`，并补齐对应章节。
- 详细说明与 eval 关注点统一参考 `references/skill-content-contracts.md`。

`normative` 规范类 skill:

- 适用于风格规范、内容标准、决策口径、审核规则、写作准则、知识边界等任务。
- 必须额外包含以下章节:
  - `Decision Rules`
  - `Exceptions`
  - `Conflict Resolution`
- 内容重点:
  - 明确规则优先级，而不是平铺罗列规则。
  - 明确例外条件和边界，不要默认一刀切。
  - 明确规则冲突时的裁决顺序。
- 不要把规范类 skill 写成教程或工具说明。

`tooling` 工具使用类 skill:

- 适用于 CLI、SDK、API、文件格式处理器、自动化脚本、环境命令等任务。
- 必须额外包含以下章节:
  - `Preconditions`
  - `Standard Procedure`
  - `Failure Recovery`
  - `Verification`
- 内容重点:
  - 先说明何时该用这个工具，而不是先介绍工具本身。
  - 说明前置检查、标准调用方式、失败后的恢复路径。
  - 把结果验证步骤写清楚，避免“命令跑完就算完成”。
- 不要把工具类 skill 写成百科介绍。

`process` 流程类 skill:

- 适用于交付流程、发布流程、排障流程、调研整理流程、知识写作流程等任务。
- 必须额外包含以下章节:
  - `Inputs`
  - `Workflow`
  - `Branches`
  - `Quality Gates`
  - `Done Definition`
  - `Handoff`
- 内容重点:
  - 定义入口条件、阶段顺序、分支判断和质量门。
  - 明确“做到什么算完成”以及要交接什么产物。
  - 对关键分支给出升级或回退条件。
- 不要把流程类 skill 写成零散 checklist。

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

1. 优先收集真实高频 prompt。
2. 没有历史 prompt 时，可以先写具体且可信的代表性 prompt，再设计 pilot 或正式 skill。
3. 不要先拍脑袋造 skill，代表性 prompt 必须能映射到明确工作流和交付物。
4. pilot 优先覆盖开发、研究整理、知识写作等不同方向，但允许按单一高价值场景先落首个正式 skill。
5. 只有任务会重复出现，或已经明确会成为长期工作流时，才创建正式 skill。
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
- 没有历史 prompt 时，允许使用代表性 prompt，但不要提交空泛描述、模板占位值或无法执行的 eval。
- 不要在 v1 中引入客户端私有扩展字段。
- 不要在 v1 中使用 `allowed-tools`。
- 不要让模板占位值进入正式 skill。
- 不要提交缺少 `metadata.skill-type` 或章节合同不完整的 skill。

## 工具管理区

<!-- tool-managed-start -->
<!-- tool-managed-end -->
