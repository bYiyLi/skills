# Cross-Document Quality Rules

## Baseline Rules

所有软件文档都先检查这 6 个问题：

1. 这份文档写给谁。
2. 这份文档解决什么问题。
3. 事实以什么真源为准。
4. 对应哪个版本、里程碑或状态。
5. 哪些内容已确认，哪些只是假设。
6. 下游谁会用这份文档做什么。

## Traceability Rules

1. 需求要能追到来源和验证方式。
2. 设计要能追到需求、约束或质量目标。
3. 使用说明和 reference 要能追到真实接口、真实命令或真实产品行为。
4. 发现 orphan 内容时，不要默认保留；先标注来源缺失。

## Repository Management Rules

1. 文档必须落在 canonical 路径，而不是散落在随机目录。
2. 每份正式文档都必须有状态，至少区分 `draft / active / approved / deprecated / archived`。
3. 每个 topic 在每种文档类型下只允许一份 active 或 approved 真源。
4. 文档被替代时，必须显式写 supersede 关系，不靠文件名猜。
5. 归档是显式动作；不要把过时文档继续留在工作目录冒充当前基线。

## Non-Fabrication Rules

1. 没确认的接口、字段、权限、错误码，不要自己补。
2. 没量化的 NFR，不要写成“高性能”“高可用”这种空话。
3. 没评审通过的方案，不要写成最终决议。
4. 没跑通过的步骤或示例，不要写成 verified procedure。

## Review Focus

评审时重点看：

1. 类型是否路由正确。
2. 是否混淆事实、假设、建议和示例。
3. 关键内容是否可验证。
4. 上下游追溯是否断链。
5. 文档是否真的服务目标读者，而不是服务作者的表达习惯。

## Repository Standard Snapshot

本仓库对跨文档质量要求收敛为以下硬约束：

1. 需求必须清晰、唯一、可验证，且能追溯到来源。
2. 设计必须能追溯到需求、约束或质量目标，不能出现无来源的重要设计元素。
3. reference 必须贴近真实接口面，结构稳定，不能混入大段教学叙事。
4. 文档要显式区分 facts、assumptions、open questions、examples。
5. 文档要显式区分当前真源、替代关系和归档状态。
6. 无法确认时默认保守，标注 gap，不补写想当然的细节。
