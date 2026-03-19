---
name: novel-creation
description: >
  用于单部、长篇小说项目的工程化创作与知识库管理。
  当任务涉及从空白状态搭建设定、维护正文场景块、做章节/卷归档、
  运行一致性检查、生成最小上下文包、typed retrieval、runtime indexing、
  embedding cache、archive workflow、plotline tracking 时触发。
license: ./LICENSE.txt
compatibility: Python 3.11+ with uv is required to run the bundled novelctl CLI.
metadata:
  owner: baiyihuan
  status: active
  last-reviewed: 2026-03-19
  source-bucket: novel
  skill-type: process
---

# Task Fit

在以下情况触发本 skill：

1. 需要在 Git 仓库里长期维护一部小说的设定、正文、归档与检索。
2. 需要用结构化场景块推进正文，并在续写前快速拿到最小上下文包。
3. 需要用 CLI 从几百万字项目里检索角色、地点、时间线、情节线、事实和冲突候选。
4. 需要把 `.novel/runtime/` 当作可重建层，把 `.novel/cache/embeddings/` 当作可共享缓存层。

不要在以下情况触发本 skill：

1. 只想写一个短片段，不需要仓库化管理。
2. 只讨论文学理论、题材分析或审美建议，不落地到项目工作区。
3. 只问某个通用 CLI 的基础用法，不涉及小说项目流转。

# Resources to Load

按需读取，不要默认全读：

- 需要确认目录、Git/LFS 边界、真源与 runtime 分层时，读取 [references/workspace-contract.md](references/workspace-contract.md)。
- 需要确认场景块字段和正文写法时，读取 [references/scene-schema.md](references/scene-schema.md)。
- 需要选择检索视角或解释最小上下文包时，读取 [references/retrieval-views.md](references/retrieval-views.md)。
- 需要执行或解释 CLI 命令时，读取 [references/cli-usage.md](references/cli-usage.md)。
- 需要初始化工作区时，使用 `assets/workspace/` 模板或直接运行 `scripts/novelctl/` 里的 `novelctl init`。

# Inputs

进入流程前至少确认：

1. 小说工作区根目录。
2. 当前目标是设定、续写、检索、检查、章节归档还是卷抽取。
3. 可用真源文件是否存在：`设定/`、`正文创作区.md`、`归档/`、`进展/`、项目 `AGENTS.md`。
4. 若要用语义检索，`.novel/config.yaml` 是否已配置 OpenAI-compatible embedding/reranker。

若输入缺失，按以下顺序处理：

1. 缺工作区时，先运行 `novelctl init`。
2. 缺结构化字段时，先补字段，再继续正文工作。
3. 缺 runtime 层时，先运行 `novelctl sync` 或直接调用会自动 freshness check 的读命令。
4. 缺关键设定时，暂停续写，先补设定。

# Workflow

1. Bootstrap
   - 初始化或修复工作区。
   - 确认 Git 真源、LFS 缓存、runtime 目录三层边界。
2. Spec
   - 在 `设定/` 中补齐世界观、主线规格、时间线和关键实体。
   - 把冻结设定、当前活跃情节线、检索优先路径写入项目 `AGENTS.md`。
3. Draft
   - 只在 `正文创作区.md` 里维护活跃场景块。
   - 正文与结构化字段必须同文件更新。
4. Sync And Check
   - 优先依赖 `novelctl` 的自动 freshness check。
   - 必要时显式运行 `novelctl sync`、`novelctl check`。
5. Retrieve Or Report
   - 查事实、实体、时间线、情节线时优先用 `retrieve`。
   - 续写前优先用 `report context-pack`。
6. Archive
   - 章节归档只处理正文前部连续 `ready` 场景。
   - 卷抽取必须满足阈值和情节线阶段性闭合。
7. Handoff
   - 结束时明确当前阶段、未解冲突、推荐下一步和推荐检索路径。

# Branches

- 工作区不存在或结构不完整：先 `novelctl init`，不要手工拼目录。
- 真源有变化但 runtime 未刷新：直接运行读命令或显式 `sync`，让 CLI 自动补齐。
- `check` 仍有 blocking error：回到真源修复，不继续大规模续写。
- 只查资料不改正文：优先 `retrieve` 或 `report`，不要手动翻全仓库。
- 章节归档条件不足：继续留在 `正文创作区.md` 推进。
- 卷级情节线未闭合：允许继续章节归档，不抽卷。

以下情况中止并升级给用户：

- 同时管理多部小说。
- 要求 CLI 直接生成正文。
- 要求在无结构化字段前提下“自动理解”全仓库事实并保证一致。
- 无法判断哪份文档才是真源。

# Quality Gates

1. Workspace Gate
   - `AGENTS.md`、`进展/项目状态.md`、`正文创作区.md`、`.novel/config.yaml` 存在。
2. Spec Gate
   - `设定/` 足以回答当前续写所需的世界规则、主线目标、关键实体背景。
3. Scene Gate
   - 变更过的场景块包含必填字段。
   - 结构化字段与正文都已更新。
4. Index Gate
   - runtime 层可重建且 freshness 状态最新。
   - `.novel/runtime/` 不当作 Git 真源。
5. Consistency Gate
   - `check` 没有 blocking errors。
   - `review_required` 项已被显式注意。
6. Archive Gate
   - 章节只归档前部连续 `ready` 场景。
   - 卷抽取满足阈值并至少闭合一条情节线。

# Done Definition

满足以下之一才算本轮完成：

- 设定工作完成：通过 Workspace Gate、Spec Gate、Index Gate。
- 正文续写完成：目标场景写完，并通过 Scene Gate、Consistency Gate。
- 章节归档完成：已生成章节文件，正文活跃区已裁剪，并完成重新同步。
- 卷抽取完成：已生成卷文件、卷摘要与闭合情节线清单，并完成重新同步。
- 检索支持完成：已给出最小足够上下文包或 typed retrieval 结果，下一轮无需全仓库重读。

# Handoff

结束时至少交付：

1. 当前阶段状态。
2. 本次变更过的真源文件列表。
3. 最近一次 `sync` / `check` 状态。
4. 未解决冲突候选或 review_required 项。
5. 推荐下一步命令，例如 `novelctl report context-pack --scene ...` 或 `novelctl retrieve ...`。

# Output Standard

- 清楚区分真源改动、runtime 产物、embedding cache。
- 涉及检索时，结果必须带来源路径和 `scene_id/chapter_id/volume_id` 或等价 `source_ref`。
- 涉及检查时，明确区分 `errors`、`warnings`、`review_required`。
- 涉及归档时，说明哪些内容已迁出活跃正文。

# Stop Conditions

- 缺工作区且用户不允许初始化。
- 当前请求跨多个小说仓库。
- 结构化字段严重缺失，CLI 无法稳定提取。
- `check` 存在 blocking errors，但请求仍要求继续大规模续写。
- 用户要求覆盖已归档大段内容，却没有明确回退策略。

# Minimal Examples

正例：

- “帮我初始化这个小说工作区，并搭好设定、正文创作区和 runtime 索引。”
- “继续写 `正文创作区.md` 里的下一场戏，先把主角和黑石城这条线的 context pack 取出来。”
- “把前面三个 `ready` 场景归档成一章，然后检查是否还有未回收伏笔。”

反例或边界例：

- “随手写一段仙侠开头，不要目录和长期管理。”
- “比较《三体》和《基地》的叙事结构。”
- “别写结构化字段，直接自己把仓库全看懂并保证零冲突。”
