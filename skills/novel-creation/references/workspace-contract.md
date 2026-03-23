# Workspace Contract

`novel-creation` 只支持单小说工作区。

固定目录树：

```text
WORK.md
设定/
  世界观.md
  主线规格.md
  时间线.md
  ...其他设定文档
角色/
  ...角色文档
正文创作区.md
归档/
  卷/
    volume-0001/
      卷.md
      章节/
        chapter-0001.md
.novel/
  config.yaml
  cache/
  runtime/
```

规则：

- `WORK.md` 是项目状态和真源索引中枢。
- `设定/` 与 `角色/` 是人类真源目录。
- `正文创作区.md` 是唯一活跃正文文件。
- `归档/卷/<卷ID>/卷.md` 是卷总结；`归档/卷/<卷ID>/章节/*.md` 是该卷章节归档。
- `.novel/runtime/` 是可重建 runtime，不是人工真源。
