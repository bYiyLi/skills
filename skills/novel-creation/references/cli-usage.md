# CLI Usage

## Runtime

`novelctl` 位于 `skills/novel-creation/scripts/novelctl/`，使用 `uv` 管理。

从仓库根目录调用，优先使用以下 shell-neutral 形式：

```bash
uv run --project skills/novel-creation/scripts/novelctl novelctl <command> <workspace>
```

示例：

```bash
uv run --project skills/novel-creation/scripts/novelctl novelctl init /path/to/novel
```

```powershell
uv run --project skills/novel-creation/scripts/novelctl novelctl init C:\path\to\novel
```

## Command Routing

按技能路径选命令，不要默认整条链路全跑：

- `bootstrap`：优先 `init`，必要时补 `status`。
- `spec`：必要时先 `status` 或 `sync`，再修改真源设定文件。
- `draft`：优先 `report context-pack`、`retrieve`、`check`，需要时显式 `sync`。
- `retrieve`：优先 `retrieve` 或 `report`，只返回最小足够材料。
- `check`：优先 `check`、`report conflicts`、`report gates`、`report unresolved`。
- `archive`：先 `archive chapter` 或 `archive volume`，再确认 `status` 或 `check`。

说明：

- 技能入口里统一叫 `retrieve`，命令层可以使用 `novelctl retrieve` 或 `novelctl report`。
- `spec` 路径主要更新真源文档，本身不依赖专属命令，但经常需要在改前改后查看 `status` 或 freshness。

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
- `conflict_candidates`
- `next_actions`

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

说明：

- `text`、`entity`、`timeline`、`plotline`、`fact`、`relation` 默认要求非空 query。
- 如果要显式浏览 query-driven mode，使用 `--browse`，输出会带 `browse_mode: true`。
- `unresolved` 与 `conflict-candidates` 可以不带 query。
- `--limit` 未显式传入时，默认值来自 `.novel/config.yaml` 的 `retrieval.default_limit`。

### `archive chapter`

把 `正文创作区.md` 前部连续 `ready` 场景归档成章节，并在归档后立即重新同步 runtime 层。

支持：

- `--force`
- `--dry-run`

### `archive volume`

当章节数量或字数达到阈值，且至少一条情节线阶段性闭合时，抽取成卷并重新同步 runtime 层。

支持：

- `--force`
- `--dry-run`

### `status`

输出当前阶段、freshness、runtime 完整性、语义后端可用性、gate 状态和建议下一步。

说明：

- `--json` 只是兼容占位；默认输出已经是 JSON。
- 当 `freshness.auto_sync_on_read: false` 且 runtime stale 时，`status` 不会自动 sync，而是返回 `stale: true` 和下一步建议。

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

- 未配置时：继续使用结构化索引加 lexical retrieval；这是 `retrieve` 路径的正常 fallback，不是错误。
- 配置 embedding 时：优先复用 `.novel/cache/embeddings/`。
- 配置 reranker 时：只对候选集做二阶段重排。

## Freshness Contract

`.novel/config.yaml` 的 `freshness.auto_sync_on_read` 现在是实际生效的行为开关：

- 为 `true` 时：`status`、`retrieve`、`check`、`report` 等读命令遇到 stale runtime 会自动 sync。
- 为 `false` 时：
  - `status` 和 `report freshness` 返回 `stale: true`，并提示先运行 `novelctl sync`。
  - `retrieve`、`check`、`report summary/conflicts/gates/unresolved/context-pack`、`archive` 会直接报 stale-runtime error。

## Verification

把以下命令当作稳定验证路径：

```bash
node scripts/validate-skills.mjs
```

```bash
npx skills add ./skills --list
```

```bash
npx skills add ./skills -a codex -y
```

```bash
npx skills list -a codex --json
```

```bash
uv run --project skills/novel-creation/scripts/novelctl python -m unittest discover -s skills/novel-creation/scripts/novelctl/tests -p 'test_*.py'
```

说明：

- 仓库当前把 `python -m unittest discover` 作为 bundled CLI 的稳定 smoke test。
- 不要把裸 `pytest` 当成必经验证路径，除非额外引入并声明 dev/test 依赖。
