# Evidence-Driven Usage Document Management

仅当当前操作涉及仓库写入、路径、metadata、supersede、deprecation、archive，或用户
明确要求审校这些状态时使用本 reference。它不提供默认目录、frontmatter schema、
状态枚举或 archive 布局。

## 确定适用合同

按 instruction authority、scope 和适用 baseline 决定目标仓库规则，再在同一权限层
比较来源。检查：

1. 当前任务中适用的高权限项目说明和 agent instructions。
2. 用户在其权限范围内对本次交付作出的明确决定。
3. 目标仓库中适用的贡献指南、文档规范或生成配置。
4. 当前 canonical artifact 及同一文档集合中稳定、可重复观察的约定。

仓库中的现有文件只能证明观察到的用法，不能单独建立强制政策。检查证据的 scope、
baseline 和 freshness；多份规则冲突且权限与范围不能裁决时，保持只读并返回 blocker
或 review finding，不自行选择一套规则。

## 决定路径和交付形式

- `revise` 优先修改用户指定或经证据确认的 canonical artifact，不平行新建同一结果。
- `create` 使用用户明确指定或目标仓库合同导出的路径和文件名。
- 目标仓库没有可确认规则且用户要求写文件时，报告缺失的路径决定并请求确认；确认前
  可以返回内联 artifact 或 explicitly unverified draft，但不得写入猜测路径。
- 不从本 Skill 推导 `docs/usage/`、`docs/reference/` 或任何其他默认目录。

## 处理 Metadata 和 Lifecycle

- 只添加目标仓库合同要求的 metadata，使用该合同定义的字段和值。
- 没有 lifecycle 合同时，不创建 `status`、`owner`、日期、source-of-truth 或关系字段。
- 验证状态与 lifecycle 状态分开报告；不要把 `verified` 当作未经定义的 lifecycle 值。
- `source_of_truth` 或同类字段必须表示目标合同要求的真实来源，不硬编码为 `repo`。
- 只依据当前证据报告 active、approved、deprecated、archived 或其他项目状态。

## 处理替代和归档

Supersede、deprecate、move、archive 和 delete 是独立 side effect，不是创建或修订
文档自动附带的动作。

1. 先识别旧 artifact、当前引用和目标仓库的 lifecycle 规则。
2. 说明拟执行动作及其影响，逐项核对已有明确授权。同一本次请求可以授权多项，不要求多轮重复批准；明确的即时确认要求仍须遵守。
3. 只有路径、状态表示和授权都已确认时才执行。
4. 不静默删除仍有引用或历史价值的 artifact。
5. `review` 只报告建议动作，不执行任何状态改变。
6. 删除只在准确目标、当前引用、适用保留要求、恢复证据和该动作的明确授权都已确认时执行。

完成非删除 lifecycle 动作后重新读取目标，确认实际状态或位置且正文未改变。删除只在准确
目标已不存在，并复核引用、保留和恢复要求后报告完成。

## 处理失败和重入

side effect 开始后失败时，重新检查当前文件和仓库状态。保留已完成且可验证的授权
结果，不重复执行可能已经成功的动作，包括删除。报告：

- 已写入、移动或更新的 artifact；
- 未执行或失败的动作及证据；
- 当前路径和 lifecycle 状态；
- 恢复、回滚或重入所需的决定与权限。

不要把计划动作报告成已执行，也不要把局部成功报告成完整成功。commit 和 push 只有
在用户分别明确请求且 host 允许时执行，并与文档内容结果分开验证和报告。
