# CLI Usage

## Runtime

`novelctl` 位于 `scripts/novelctl/`，使用 `uv` 管理。

推荐调用方式：

```powershell
uv run --project skills/novel-creation/scripts/novelctl novelctl init C:\path\to\novel
```

## Commands

### `init`

初始化单小说工作区、模板文件、`.gitignore`、`.gitattributes`、`.novel/cache/embeddings/` 与 `.novel/runtime/`。

支持：

- `--force`
- `--dry-run`

### `sync`

按文件 MD5 做 freshness 检查和增量提取，生成运行时层：

- `.novel/runtime/manifests/`
- `.novel/runtime/indexes/`
- `.novel/runtime/reports/`
- `.novel/runtime/llamaindex/`

支持：

- `--full`
- `--dry-run`

### `check`

执行确定性校验，输出：

- `errors`
- `warnings`
- `review_required`

支持：

- `--strict`

### `retrieve`

使用 typed retrieval，而不是自由问答。支持：

- `text`
- `entity`
- `timeline`
- `plotline`
- `fact`
- `relation`
- `unresolved`
- `conflict-candidates`

所有结果都返回来源定位和命中字段。

### `archive chapter`

把 `正文创作区.md` 前部连续 `ready` 场景归档成章节，并在归档后立即重新同步 runtime 层。

支持：

- `--force`
- `--dry-run`

### `archive volume`

当章节数量/字数达到阈值，且至少一条情节线阶段性闭合时，抽取成卷并重新同步 runtime 层。

支持：

- `--force`
- `--dry-run`

### `status`

输出当前阶段、freshness、runtime 完整性、语义后端可用性、gate 状态和建议下一步。

### `report`

支持：

- `summary`
- `context-pack --scene <scene_id>`
- `conflicts`
- `gates`
- `unresolved`
- `freshness`

## Optional Semantic Retrieval

`.novel/config.yaml` 可配置 OpenAI-compatible embedding 与 reranker。

- 未配置时：仍可使用结构化索引 + lexical retrieval。
- 配置 embedding 时：优先复用 `.novel/cache/embeddings/`。
- 配置 reranker 时：只对候选集做二阶段重排。
