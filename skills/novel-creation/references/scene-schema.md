# Scene Schema

`正文创作区.md` 使用固定 scene block：

~~~md
## scene-0001 场景标题
```yaml
scene_id: scene-0001
status: draft
pov: 林野
time: time-0001
location: 黑石城
characters:
  - 林野
plotlines:
  - plot-main-001
goal: 拿到名单
outcome: 只拿到一半
continuity_refs: []
summary: 林野在黑石城推进调查。
beats:
  - 进入码头
  - 遇到阻拦
new_facts: []
state_changes: []
foreshadow: []
payoff_refs: []
open_loops: []
```
正文:

这里写 prose。
~~~

最小要求：

- 必须有 `scene_id`
- `status` 只能表达当前可写状态，不能代替 check 结论
- `continuity_refs` 只引用已存在 scene
- `ready` 只用于允许进入章节归档的场景
