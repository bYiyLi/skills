# Workspace Contract

## Overview

`novel-creation` v1 只支持单小说工作区。

- Markdown 小说文档是唯一 Git 真源。
- `.novel/runtime/` 是运行时可重建层，不进入普通 Git 跟踪。
- `.novel/cache/embeddings/` 是向量缓存层，建议用 Git LFS 共享。
- 所有人工文档都遵守“正文/说明 + 结构化字段同文件”原则。

## Required Layout

```text
AGENTS.md
设定/
  世界观.md
  主线规格.md
  时间线.md
  角色/
  势力/
  地点/
  物件/
进展/
  项目状态.md
  变更记录.md
正文创作区.md
归档/
  章节/
  卷/
.novel/
  config.yaml
  cache/
    embeddings/
  runtime/
    manifests/
    indexes/
    reports/
    llamaindex/
  tmp/
  logs/
```

## Git And LFS Policy

- 普通 Git 跟踪：
  - `设定/`
  - `进展/`
  - `正文创作区.md`
  - `归档/`
  - 项目 `AGENTS.md`
  - `.novel/config.yaml`
- Git LFS 跟踪：
  - `.novel/cache/embeddings/**`
- 普通 Git 忽略：
  - `.novel/runtime/`
  - `.novel/tmp/`
  - `.novel/logs/`
  - `.novel/**/*.lock`

## Runtime Guarantees

- `novelctl sync` 只按文件 MD5 判断真源是否变化。
- 文件 MD5 未变时跳过提取。
- 文件 MD5 变化时，重提取该文件内全部记录。
- 运行时层缺失时，可以从小说真源和 embedding cache 自动重建。
- 读命令在执行前先做 freshness 检查，必要时自动触发增量 `sync`。

## Source Of Truth Rules

- `设定/*.md`、实体文件、`AGENTS.md`、`进展/*.md` 使用 `frontmatter + Markdown body`。
- `正文创作区.md` 与 `归档/章节/*.md` 使用 `H2 场景块 + YAML 代码块 + 正文`。
- 结构化字段和正文必须写在同一文件里，不维护平行人工副本。

## Project AGENTS.md Responsibilities

项目级 `AGENTS.md` 至少维护：

1. 当前阶段
2. 当前活跃情节线
3. 冻结设定与禁改项
4. 当前创作约束
5. 检索优先路径
6. 归档规则与下一步建议
