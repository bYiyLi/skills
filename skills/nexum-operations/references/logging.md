# Operating records and notifications

Read for authorized operating recording or a requested daily/weekly review.
Check `Nexum 运营资料库 / 运营日志机制` and the relevant current schema and notification
recipient before writing. An explicit read-only task does not trigger logs or
notifications. Missing write access leaves the requested analysis deliverable
possible, but required persistence uncompleted.

## Session evidence

Use one `运营日志` record with `记录类型 = 执行日志` per meaningful authorized session,
including a blocked or partial session. Capture the objective, actual research
scope, preparation or mutations, direct results, user outcome when relevant,
learning signal, updated objects and evidence sufficient for recovery.
Omit incidental reads, browser-click narration and empty fields. Log creation
itself does not require another log.

After each meaningful authorized state-changing write, send the required concise
Feishu notification: action/target, observed result and blocker or follow-up.
This includes business records, public content, comments/messages and scheduler
changes. Log writes and notification sends do not recursively trigger either
notification or logging. Resolve the recipient from current authority, not a
name guess; an unavailable recipient is an explicit notification blocker.

If an external operation succeeded but its log or notification failed, report
that split and recover only the missing evidence. Check current records before
retrying creation so an interrupted response does not cause duplicates.

## Daily and weekly results

For an authorized daily Vlog task, create or update that operating day's single
`记录类型 = 日报` record from execution logs and current durable state. Summarize
actual work, user results, new evidence or contradictions, judgment changes and
important follow-up. No new experience is a valid observation; do not invent
learning to fill a daily quota. This instruction does not create a scheduler.

For a weekly review, inspect relevant recent logs, daily records, content, leads,
experiments and experience. Identify work producing neither results nor learning;
propose redesign or stop within the request's decision authority.

## Scheduled run identity

For each scheduled business run, resolve the matching live `运营任务` contract
and its planned slot before recording. Use the verified Asia/Shanghai slot, not
actual start time. Existing Nexum run-key conventions are:

| Job | Key |
| --- | --- |
| Community patrol | `社区巡航:YYYY-MM-DD HH:00` |
| Owned content | `内容生产:YYYY-MM-DD` |
| Daily Vlog | `每日Vlog:YYYY-MM-DD` |
| Weekly review | `周复盘:YYYY-Www` (ISO week) |
| Guardian | `守护巡检:YYYY-MM-DD HH:45` |

Apply a convention only to its matching task and expected slot; do not change an
existing job's timezone/cadence to fit the examples. New job identities require
the live contract. A resumed business run keeps its original key. Guardian logs
use `关联运行键` and `恢复轮次` for the target and attempt.
