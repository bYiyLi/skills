# Requirements Repository Evidence Contract

仅在仓库写入或文档生命周期路径中使用本 reference。它规定如何取得和报告管理证据，不为目标仓库发明目录、frontmatter、状态枚举或审批流程。

## Inspect Governing Evidence

写入、替代、移动、归档、删除或改变状态前，检查当前路径适用的来源：

1. host 和目标仓库指令；
2. 仓库内明确的文档目录、命名、模板和生命周期合同；
3. 已有同主题 artifact、文档索引和可验证的当前状态；
4. 用户在其权限和当前任务范围内明确给出的路径或管理决定。

按 instruction authority、source authority 和 scope 解决冲突。两个适用来源仍冲突时，不选择其一写入；报告冲突、受影响动作和需要的裁决。

## Resolve the Target

- 优先更新已确认的同主题真源。不要仅因请求使用“新建”一词就制造平行 artifact。
- 新建路径必须来自用户明确目标或仓库合同。没有可验证路径规则时，先请求目标位置；可以交付未持久化 draft，但不要硬编码默认目录。
- 文件名、扩展名和目录结构遵循目标仓库已有合同。没有证据时不要发明 slug、日期前缀或 archive 目录。
- 目标不可读、同主题真源互相冲突或路径大小写不确定时，停止写入并报告观察到的候选项。

## Preserve Format and State

- 修订时保留现有且仍受仓库合同支持的文档格式和管理字段。
- 只添加仓库合同或用户决定要求的 metadata。没有证据时不要添加 frontmatter、owner、status、baseline 或 source-of-truth 字段。
- 状态值（例如 active、approved、deprecated 或 archived）只能按目标仓库的已验证状态合同使用。
- 不要把 draft 提升为 accepted 或 approved，除非有可定位的批准决定和执行该状态变更的授权。
- 替代关系、旧文档状态和 archive 位置必须来自仓库合同或用户决定；不能验证时报告 proposed action，不执行迁移。
- 删除前确认准确目标、当前引用、适用保留要求和可用的恢复证据。任一项不明确时不删除。

## Control Side Effects

- 文件创建或修改必须位于用户请求或 host task 已授权的范围内。
- 移动、删除、归档、改变状态、commit、push、deploy 或外部发送分别需要覆盖该动作的明确授权。
- 执行动作前读取当前状态，避免覆盖并发修改或重复已完成的迁移。
- 动作被拒绝、工具不可用或执行中失败时，保留已完成的独立结果；重新读取当前状态并报告未完成动作，不盲目重试。

## Report Completion Evidence

仓库动作只在获得对应证据后才能声称完成：

- 创建或修改：准确路径、重新读取结果和实际 diff；
- 状态变化：变更前后值及其 governing evidence；
- 替代或归档：新旧 artifact 的关系、实际位置和双方可验证状态；
- 删除：准确目标已不存在，且引用、保留和恢复要求仍满足；
- commit 或 push：仅在另行授权并实际成功后报告对应提交或远端证据。

未执行或无法验证的动作单独列出，并说明当前状态、缺失能力或权限及重新进入条件。
