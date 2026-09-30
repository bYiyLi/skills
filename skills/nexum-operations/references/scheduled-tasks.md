# Scheduled operations and recovery

Read for authorized scheduler maintenance, guardian patrol or run recovery.
For scheduler-state maintenance, resolve the matching `运营任务` contract and real
scheduler. Additionally resolve `Nexum 运营资料库 / 运营守护机制` and recent logs for
guardian patrol, recovery, or a maintenance decision that depends on those rules
or observations. These instructions do not guarantee a scheduler,
original-conversation access or a resume interface.
Unavailable capabilities block that action; do not simulate them with a record.

## Maintain intent separately from observations

`运营任务` records the intended job; the real scheduler proves whether it exists,
is enabled and has the expected cadence. A job describes one bounded iteration
and references the Skill/live state rather than copying its full instructions.
Only activate a proposed schedule once the actual task scope and cadence are
authorized. Intentional create, cadence change, pause, resume or delete updates
both scheduler and registry, with observed evidence and required logging.
Scheduled execution uses the task's applicable delegation, not authority created
by this file. Business mutations still require Playbook and evidence checks.

Within the task set named by the request or live guardian contract, reconcile
each registered task with its linked scheduler before filtering for business
recovery. Include a linked scheduler that remains active while its registry says
stopped; do not inspect or manage unrelated jobs. A registry state alone does not
determine patrol membership.

Business recovery is eligible only for a confirmed task whose intended state is
running and whose `守护策略 = 恢复原会话`, `会话链接`, `守护宽限分钟` and `最大恢复次数`
are established. A disabled/missing scheduler can be an incident or an intentional
stop. Read latest explicit decisions and authorized changes; inaccessible or
ambiguous stop evidence leaves intent unresolved, not continued execution authorized.

If a legitimate pause, stop, completion, replacement or deletion is established,
honor it: under the corresponding authority, disable any still-active linked
scheduler and synchronize the registry; do not resume its business runs. If continuing intent is established and
scheduler state drifted, repair from the recorded contract under repair authority,
record the result and notify. Do not invent cadence or copy an unexpected failure
into the intended state just to make the stores match. A stale stopped registry
also requires reconciliation from actual decisions rather than blind trust.

## Classify before recovery

Resolve planned slots and run keys using the logging reference routed from the
root Skill and the matching live task contract before comparing run evidence.

Derive a finite candidate interval from the live task's activation/cadence history
and last verified patrol coverage, or its explicit lookback contract. Include
separately recorded unresolved run keys outside that interval. Do not rescan all
history on each patrol or invent a cutoff that silently drops required recovery.
If the boundary cannot be established, report historical coverage as unverified;
continue scheduler diagnosis and individually known runs without claiming a full
patrol or automatically replaying uninspected history.

For each candidate slot strictly past its grace period, inspect its log, original
conversation and attributable Feishu/channel state. A matching completed log ends
recovery unless contrary evidence needs investigation.

- Interrupted: partial/blocked log, an execution turn or an attributable side
effect proves work started. Continue missing work under the same key regardless
of the never-started compensation policy.
- Never started: inspected sources show no execution turn, log or attributable
side effect. Only this state uses `漏跑策略`.
- Unknown: required sources cannot be inspected or conflict. Do not infer never
started from absent logs or automatically replay business work.

The live task's `漏跑策略` uses these existing values:

| Value | Never-started slot handling |
| --- | --- |
| `跳过历史槽位` | Record `历史漏跑-不补偿`; no historical continuation or fabricated completed log |
| `同业务周期补偿` | Recover only within the same Beijing hour/day/ISO week corresponding to the original key; afterwards record `历史漏跑-过期不补偿` |
| `必须补偿` | Eligible after grace beyond the original period, subject to current scope, retry limits and blockers |

Missing/invalid policy gives `策略缺失-不补偿`: report a configuration incident,
notify and do not compensate automatically. It does not itself cancel future
scheduled execution. Scheduler repair is not evidence that missed work may be
replayed; derive missed slots from the expected schedule and classify each.

## Resume without duplicate actions

Before resuming, verify the original conversation is not still executing, inspect
completed side effects, and count prior recoveries from guardian logs with the
same target key. Honor the task's configured maximum and live guard limits;
the existing standard is two attempts per key. Missing limits or an unknown
attempt history do not authorize another automatic attempt.

Inspect every due candidate in the bounded set, but resume at most one business
run per patrol.
Choose the eligible run longest past grace. Scheduler repair does not consume
that business-run quota. Recheck state on the next patrol before selecting another.

Use the supported interface to resume the original conversation with its run key
and an instruction to inspect state, retain completed effects and finish only
missing conditions. Do not restart from zero. If publishing succeeded, repair only
missing Feishu/log evidence. Log the recovery attempt and result; a failed resume
with uncertain outcome must be investigated before another attempt.

CAPTCHA, login/security checks, missing account permission, payment/account recovery
or another user-only blocker stops automatic retries for that incident/run.
Record and contact the user immediately; this is not deferred by the one-run quota.

The guardian writes one patrol log under logging authority. It does not mutate
`运营任务` just for a heartbeat. Business/task writes are for actual recovery,
state correction, a system incident or a confirmed user blocker, and follow the
notification rule. A read-only diagnostic request reports these findings without
repairing schedules or writing logs unless separately authorized.
