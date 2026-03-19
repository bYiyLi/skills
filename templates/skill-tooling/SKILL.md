---
name: your-skill-name
description: >
  用中文先说明这个工具类 skill 操作什么工具或接口,
  在什么情况下应触发,
  再补必要的 English keywords.
license: ./LICENSE.txt
metadata:
  owner: your-name
  status: draft
  last-reviewed: 2026-03-19
  skill-type: tooling
---

# Task Fit

说明:

1. 哪类任务应该使用这个工具或接口。
2. 哪些相邻任务不该触发这个 skill。
3. 什么时候应该改用别的工具或人工判断。

## Resources to Load

说明在什么条件下读取:

- `scripts/` 中的脚本。
- `references/` 中的参数、协议或格式资料。
- `assets/` 中的模板或样例文件。

## Preconditions

列出执行前必须确认的条件，例如:

- 环境、权限、输入格式、依赖版本。
- 高风险操作前必须检查的状态。
- 不满足前置条件时该如何处理。

## Standard Procedure

写标准调用路径，而不是百科说明。至少说明:

1. 首选命令、接口或脚本。
2. 关键参数如何选。
3. 哪些操作顺序不能改。

## Failure Recovery

列出常见失败信号和恢复动作，例如:

- 输入不合法。
- 环境缺依赖。
- 命令执行失败或输出异常。

## Verification

说明如何验证结果真的正确，而不是只看命令退出成功:

1. 检查哪些输出、文件、状态或副作用。
2. 哪些验证通过后才算完成。
3. 验证失败时回到哪一步。

## Output Standard

说明最终输出至少要包含:

- 为什么选这个工具或路径。
- 做了哪些关键检查。
- 结果如何验证。

## Stop Conditions

说明什么时候应停止并升级，例如:

- 当前环境不满足工具前提。
- 操作风险超出 skill 允许范围。
- 无法验证结果是否正确。

## Minimal Examples

至少给出:

1. 1 个应触发的工具使用示例。
2. 1 个不应触发或应切换工具的边界示例。
