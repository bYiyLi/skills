# Requirements Outline And Checklist

## Recommended Outline

按复杂度选择，不要默认写最重的版本。

### A. Feature Spec

1. Context / problem
2. Goal / success metrics
3. Scope / out of scope
4. Actors / scenarios
5. Functional requirements
6. Non-functional requirements
7. Constraints / dependencies
8. Acceptance criteria
9. Open questions / risks

### B. SRS-Style Baseline

1. Purpose / scope / glossary
2. Stakeholders / actors
3. Product or system context
4. Functional requirements
5. External interface requirements
6. Data requirements
7. Quality / security / reliability / performance requirements
8. Constraints and compliance
9. Acceptance / verification approach
10. Traceability notes
11. Assumptions / unresolved issues

## Requirement Quality Checklist

每条关键 requirement 至少自查：

1. 是否单一语义。
2. 是否清晰、无歧义。
3. 是否必要，而不是偏好性噪音。
4. 是否尽量实现无关；若不是，是否明确写成 constraint。
5. 是否有验证方式。
6. 是否能追到来源。
7. 是否与其它 requirement 冲突或重复。

## Common Failure Modes

1. 把设计方案写成需求。
2. 把愿景、目标、假设和 requirement 混写。
3. NFR 只写“高性能”“高可用”而无量化边界。
4. 接口依赖、异常场景、权限边界被遗漏。
5. 新需求写在随机目录或临时笔记里，没有进入 canonical requirements 路径。
6. 同主题出现多份 requirements 文档，但没有标哪份是当前真源。

## Repository Requirements Standard

本仓库对软件需求文档采用以下本地标准：

1. requirement 要满足：
   - 单一语义
   - 清晰无歧义
   - 必要
   - 尽量实现无关
   - 可验证
   - 可追溯
2. 需求文档至少要覆盖：
   - purpose / scope
   - actors / stakeholders
   - functional requirements
   - interface or data-related requirements
   - quality / security / operational requirements
   - constraints / dependencies
   - acceptance / verification
   - assumptions / unresolved issues
3. 对设计的要求：
   - 设计方案可以在背景中出现，但不得伪装成 requirement statement。
4. 对追溯的要求：
   - 关键 requirement 要能指向来源。
   - 后续设计和测试应能回指到这些 requirement。
5. 对文档管理的要求：
   - 默认放 `docs/requirements/`
   - 标明 status、baseline、owner
   - 替代旧文档时显式写 supersede 关系
