---
name: nexum-operations
description: >
  Operate Nexum growth and user-facing channels using Feishu as the live operating memory and production Nexum as the execution/evidence layer. Use for channel research, content planning and review, community opportunity analysis, publishing preparation, comment/lead handling, performance review, operating experiments, learning extraction, and AI handoff. Product development and code implementation remain owned by the Nexum development workflow.
---

# Nexum Operations

This Skill owns Nexum operating work around growth channels, community, user acquisition, content, conversion, review, and operating learning. A requested operation ends when its real-world evidence has been checked and the durable operating state has been written back to Feishu, or when a concrete blocker prevents that result.

## Live sources of truth

Do not use old chats as current operating truth when live sources are available.

Use stable resource names rather than persisting Feishu tokens or temporary links:

- `Nexum 运营资料库`: operating strategy, channel Playbooks, scripts, community and sales materials.
- `Nexum 运营资料库 / 运营方法`: the stable Nexum operating methodology, including the evidence-driven growth and learning loops.
- `Nexum 运营资料库 / 运营日志机制`: the logging contract for meaningful operating sessions, daily Vlogs, and recovery evidence.
- `Nexum 运营资料库 / 运营守护机制`: the reliability contract for scheduled-run keys, grace periods, interruption detection, duplicate-safe recovery, and resuming the original task conversation.
- `Nexum 运营中台`: structured operating state. Its current tables are `内容池`, `样本库`, `用户线索`, `运营实验`, `运营经验`, `社区机会`, `运营任务`, and `运营日志`.
- `Nexum 用户反馈`: raw user feedback.
- `Nexum 使用手册`: user-facing product instructions.
- The current Nexum repository, production configuration, and observed production behavior: product capability and technical facts.

When a required Feishu resource cannot be resolved by its stable name, report the missing resource instead of inventing an ID or using a cached token.

## Start every operating task from current state

1. Resolve the requested channel, outcome, and whether the task is research, preparation, external execution, monitoring, review, or learning.
2. Read `Nexum 运营资料库 / 运营总览` and the relevant live records in `Nexum 运营中台` that can change the decision.
3. When the task involves prioritization, experiment design, review, learning, or a cross-channel decision, read `Nexum 运营资料库 / 运营方法` before deciding.
4. Before channel-specific execution, read `平台发布材料 / <渠道>`; that page is the current channel Playbook.
5. If the task makes a claim about Nexum capabilities, pricing, entitlements, installation, runtime behavior, or current release state, verify the current product/repository/production evidence before using the claim.
6. If existing evidence conflicts with a Playbook rule or operating experience, preserve the conflict and treat it as a revalidation signal rather than silently following the older rule.

Load only the Feishu tables and documents needed by the requested operation. Do not read the entire operating database by default.

## Core operating model

Use the Nexum evidence-growth double loop.

Growth loop:

`真实事件/市场讨论 → 内容或社区参与 → 用户行为 → 有效线索 → 开始使用/激活 → 新的用户问题`

Learning loop:

`真实数据/用户语言 → 观察 → 假设 → 实验 → 运营经验 → 渠道 Playbook / 跨渠道运营方法 → 下一轮执行`

Every recurring operating action should produce at least one of two outcomes: a user result or new evidence that changes a future decision. If repeated execution produces neither, stop or redesign the action instead of preserving it as routine.

The primary growth signal is qualified Nexum intent, not vanity metrics alone. Treat questions such as how to connect local projects, how to use Nexum, installation, pricing, trial intent, actual usage, and activation as qualified signals. Likes, saves, comments, views, and follows remain important diagnostic metrics but do not substitute for qualified intent.

Prefer real development evidence over marketing-style invention. When suitable real screenshots, actual product behavior, terminal output, browser actions, diffs, usage data, failures, or user questions exist, use them as the default evidence source.

## Operation: channel research

Use live platform state when current ranking, reactions, comments, account behavior, or logged-in content matters. Public web search can supplement but must not replace the logged-in platform view when the platform view is the subject.

For each useful external sample, record what is observable: title/topic, channel, interaction snapshot, content form, core hook, comment demand, and why it may matter to Nexum. External samples enter `样本库` as evidence; they do not become a Nexum rule by themselves.

When a sample suggests a reusable claim, create or update `运营经验` with confidence `观察` or `假设`, including evidence and known boundary conditions.

## Operation: content planning and preparation

Choose content from real Nexum events, user demand, current experiments, and validated or revalidation-needed experience before inventing a topic from scratch.

For a new content item, make the intended job explicit: traffic/discovery, save-worthy utility, proof, trust, community interaction, or conversion. Do not force one post to optimize every job.

Record the working item in `内容池`. Before preparing channel copy, apply only `运营经验` entries whose channel applies and whose status/credibility supports use. `待验证` experience may shape an experiment but must not be presented as a fixed formula.

Do not mechanically cross-post. Reuse the underlying evidence and insight, then adapt the format, opening, pacing, proof, CTA, and conversion path for the target channel.

## Operation: community opportunities

Community participation exists to add independent value where target users already discuss relevant problems; it is not a competitor-poaching tactic.

Create a `社区机会` record when a discussion is relevant enough to evaluate. Prefer opportunities where all are true:

- target users overlap materially with Nexum users;
- Nexum has real experience, technical context, data, or a useful counterexample to add;
- the comment still helps the discussion if every mention of Nexum is removed.

Do not participate only to create visibility. Do not use mechanical diversion phrases such as asking people to view the profile or privately contact Nexum. On competitor product posts, normal technical discussion is allowed, but do not target clearly expressed purchase intent for poaching.

Record the participation result, replies/likes when observable, qualified leads, and what was learned.

## Operation: external publishing and communication

The user has delegated Nexum operating authority to the operator acting as the operating director. Within Nexum operations, the operator may independently research, write Feishu state, publish or edit public channel content, post public comments/replies, send community/sales messages or private messages, maintain operating tasks, and make ordinary channel-execution decisions, subject to the action-specific confirmation requirements below.

Standing operating authorization does not override explicit action-time confirmation required by the host, platform, or execution tool. In particular, browser work follows `nexum-browser` and its immediate-confirmation requirements. Complete already-authorized research, copy preparation, and non-publishing preparation first; obtain the required confirmation immediately before the protected action. Do not switch tools or execution paths to evade confirmation or a permission denial. When no applicable rule requires renewed confirmation, use the existing authorization instead of asking again.

This standing authorization does not authorize bypassing CAPTCHAs, login challenges, platform safety controls, missing account permissions, payment/account-recovery flows, secret handling rules, or other host/platform restrictions. When one of those blockers prevents execution, preserve completed state, record the blocker, and contact the user with the exact action needed to unblock it.

Use this authority to serve Nexum's operating goals, not to relax community-value or evidence rules. Continue to prohibit misleading claims, fake engagement, mechanical spam, competitor purchase-intent poaching, or outbound behavior that conflicts with the current Playbook.

The user has also authorized and required Feishu operational notifications. After every meaningful state-changing operating write, send a concise Feishu notification describing what was written or executed, the result, and any blocker or follow-up. State-changing writes include Feishu business-state mutations, public publishing/editing, comments/replies/DMs, scheduler/task changes, and other operating changes that alter durable or external state. The Vlog write and the notification send themselves do not recursively trigger another Vlog or notification.

After an authorized external action, verify the resulting platform state and write the real result back to Feishu. Never mark an item published or a comment sent based only on an attempted click or command.

## Operation: monitoring, leads, and review

Update observable content metrics and user signals from the real platform. Use the existing content record instead of creating duplicate records for each measurement window.

Use 2h/24h/72h checkpoints as diagnostic timing when applicable, but do not invent a checkpoint value that the platform cannot expose. Record what is actually observable.

Qualified user intent belongs in `用户线索`. Preserve the original question/intent and update state as the relationship progresses; do not create fake leads from generic positive comments.

A review must answer what changed, why the current evidence suggests it changed, what remains uncertain, and what next decision follows. Separate correlation from causation.

## Operation: experiments and learning

Use `运营实验` when a meaningful operating belief can be tested with a defined variable and success criterion. Avoid post-hoc relabeling of ordinary posts as controlled experiments when the variable was not actually isolated.

Use `运营经验` as the learning layer:

- External examples normally start as `观察` or `假设`.
- Nexum-specific repeated evidence can increase confidence.
- Always retain material counterexamples and applicability boundaries.
- New conflicting evidence triggers revalidation; do not protect an old rule from contradiction.
- Do not promote a rule merely because one post performed well.
- Mark a channel-specific experience as a Playbook candidate only after it has repeated Nexum-specific support and no unresolved material contradiction for the claimed scope.
- Mark a cross-channel operating principle as a methodology candidate only when it is useful beyond one channel, has repeated Nexum-specific support or is an explicit operating-governance decision, and can change future operating decisions without depending on one platform's mechanics.

When a Playbook candidate is promoted, update the corresponding `平台发布材料 / <渠道>` page and record the Playbook location in `运营经验`. When a rule is invalidated or replaced, update both the experience state and the Playbook so future AI operators do not keep applying stale guidance.

When a methodology candidate is promoted, update `Nexum 运营资料库 / 运营方法`, record the methodology location in `运营经验`, and keep channel-specific tactics out of the methodology. Change this Skill only when the stable AI execution protocol itself changes; do not copy dynamic channel knowledge into the Skill.

## Operation logging and daily Vlog

`运营日志` is the execution-evidence trail for the growth and learning loops. Use one log record per meaningful operating session, not one record per browser click, page open, scroll, read, or other mechanical step.

After a meaningful operating session, write one `记录类型 = 执行日志` record that captures the parts that actually occurred:

- the operating objective;
- the real browse/research scope when browsing or research occurred;
- actions that changed operating state or prepared an external action;
- material findings and direct result;
- observable user result, or explicitly no user result when that distinction matters;
- learning signal: none, observation, hypothesis, supporting evidence, counterexample, or revalidation signal;
- durable Feishu objects updated by the session; and
- evidence sufficient to recover or review the decision.

For a guarded scheduled task, also write its deterministic `运行键`. Use the planned Asia/Shanghai slot, not the actual start time:

- community patrol: `社区巡航:YYYY-MM-DD HH:00`;
- owned content: `内容生产:YYYY-MM-DD`;
- daily Vlog: `每日Vlog:YYYY-MM-DD`;
- weekly review: `周复盘:YYYY-Www` using the ISO week;
- operations guardian: `守护巡检:YYYY-MM-DD HH:45`.

When the guardian resumes another run, its own log uses `关联运行键` for the target run and `恢复轮次` for the automatic recovery attempt. The resumed business conversation keeps the original business run key instead of creating a recovery-specific key.

This logging requirement applies to meaningful channel research/community patrols, content work, authorized publishing or communication, user/lead handling, data checks, reviews, learning, Playbook/methodology changes, development-event capture, and other work that changes operating state or future operating judgment.

Do not create recursive logs for the act of writing the log itself. Do not create a separate log for incidental context reads or mechanical browser operations that did not constitute an operating session.

Once per operating day, create one `记录类型 = 日报` record from that day's execution logs plus the current durable operating state. The daily Vlog should summarize what was actually done, user results, new evidence or contradictions, whether current judgment changed, and the most important follow-up. Do not manufacture a new experience every day; record that there was no decision-changing evidence when that is the truth.

Weekly deep review should use the recent execution logs and daily Vlogs together with content, leads, experiments, experience, and channel evidence. Use the logs to identify repeated work that produces neither user results nor useful learning and stop or redesign that work.

## Operation: scheduled operating tasks

`运营任务` is the registry of real recurring, event-triggered, or manual operating jobs; it is not a substitute for the actual scheduler. Treat the registry's intended operating state and the scheduler's observed runtime state as separate facts.

A scheduled job should describe one bounded iteration and reference this Skill plus the live Feishu state rather than embedding a large copied operating prompt. After an intentional create, cadence change, pause, resume, or delete decision, update both the real scheduler and the matching `运营任务` record. Do not convert an unexpected scheduler failure into a new intended task state merely to make the two stores agree.

Do not register an unapproved scheduling proposal as an active operating task. A draft cadence belongs in discussion until the real scheduler design has been accepted and created.

Scheduled operating jobs inherit the standing Nexum operating authorization above. They may research, write Feishu, publish, comment, reply, DM, or perform other ordinary operating actions when those actions satisfy the current Playbook, evidence requirements, and task scope. Every meaningful scheduled iteration must write its execution log, and every state-changing write must send the required Feishu notification. Blocked runs record the real blocker and contact the user when user intervention is required.

### Scheduled-run guarding and recovery

The `运营守护机制` is a reliability layer for confirmed scheduled tasks. It does not own their business work. Guard confirmed scheduled tasks whose latest explicit operating intent is to keep running and that use `守护策略 = 恢复原会话` with a configured `会话链接`, `守护宽限分钟`, and `最大恢复次数`. Do not remove a task from guarding solely because the scheduler is disabled/missing or because a previous guardian incorrectly copied that failure into `运营任务 / 状态`.

For every guarded task, distinguish two states:

- **Expected operating state**: what the task is supposed to be doing, based on explicit user instructions, authorized operating decisions, the task contract in `运营任务`, and corresponding state-change logs/notifications. Only explicit pause, stop, completion, replacement, or deletion evidence changes this state to not-running.
- **Observed scheduler state**: whether the real Scheduled Task currently exists, is enabled, has the expected cadence, and is producing runs.

The real scheduler is authoritative for what is happening now, not for what the business intended to happen. When expected state is running but the scheduler is missing, disabled, or cadence-drifted, treat that mismatch as a scheduler incident rather than a legitimate stop:

1. Inspect recent explicit user instructions and recorded authorized scheduler/task changes for legitimate stop evidence. Scheduler state alone is not sufficient evidence of intent.
2. If legitimate stop evidence exists, accept the stop and synchronize the scheduler and registry to that decision.
3. If no legitimate stop evidence exists, diagnose the scheduler incident and restore or re-enable the task from its recorded task contract. Keep or correct `运营任务 / 状态` to running, record the incident and repair result, and send the required Feishu notification. Do not invent a cadence that is absent from the registered contract.
4. Scheduler repair does not consume the patrol's one-business-run recovery quota. After repairing the scheduler, identify missed planned slots from the **expected schedule**, then apply each task's `漏跑策略` before deciding whether a never-started slot should be compensated. Missing run evidence alone does not authorize historical reruns.
5. If scheduler repair is blocked by CAPTCHA, login/security verification, missing permission, or another user-only action, record the blocker, stop automatic scheduler retries for that incident, and contact the user.

If `运营任务` currently says stopped but there is no explicit stop evidence and the latest confirmed contract says the task should continue, re-derive the intended state instead of trusting the stale stop record. A prior erroneous synchronization must not permanently remove a confirmed task from guarding.

Before run-level recovery, distinguish two states:

- **Interrupted run**: there is a partial/blocked log, a visible original-conversation turn for that run key, or a real Feishu/channel side effect attributable to that run. Recovery uses the original run key regardless of `漏跑策略`; the objective is to close already-started work without repeating completed side effects.
- **Never-started missed run**: the run key is strictly past grace, but there is no completed/partial/blocked log, no original-conversation execution turn for that run key, and no attributable Feishu/channel side effect. Only this state uses `运营任务 / 漏跑策略`.

`漏跑策略` is a closed set:

- `跳过历史槽位`: classify the never-started run as `历史漏跑-不补偿`. Record the scheduler incident in the guardian log, do not send a historical continuation turn, do not recreate stale business activity, and do not fabricate a completed business-run log.
- `同业务周期补偿`: compensate a never-started run only while the current Asia/Shanghai time remains inside the run key's business period. An hourly `HH:00` run uses that Beijing hour; a `YYYY-MM-DD` run uses that Beijing calendar date; a `YYYY-Www` run uses that ISO week. After the period ends, classify it as `历史漏跑-过期不补偿` and do not send a continuation turn.
- `必须补偿`: a never-started run remains eligible for recovery after grace even after its original business period ends, subject to the task's recovery limit and blocker rules.

If `漏跑策略` is missing or not one of those values, do not infer a default. Classify a never-started run as `策略缺失-不补偿`, record a configuration incident, notify the user, and keep future scheduler execution running.

For an expected run that is past its grace period:

1. Derive the expected run key from the planned Asia/Shanghai slot, including slots that should have occurred while the scheduler was unhealthy.
2. If `运营日志` already has that run key with `状态 = 完成`, stop checking that run.
3. Inspect the matching log, original task conversation, and attributable Feishu/channel state to classify the run as interrupted or never-started.
4. If an interrupted run's original conversation is still visibly executing, do not start a concurrent recovery turn.
5. If the run is interrupted and no longer executing, or is a never-started run whose `漏跑策略` requires compensation, resume the **original task conversation** with the target run key. Instruct it to inspect current state, preserve completed side effects, and continue only the missing completion conditions.
6. If the never-started run's policy says not to compensate, record the applicable non-compensation classification and do not send a recovery turn.
7. Count prior automatic recoveries from guardian logs with the same `关联运行键`. Do not exceed the task's configured maximum; the current standard maximum is two attempts per run key.
8. Once a CAPTCHA, login challenge, missing account permission, payment/account-recovery step, security verification, or other user-only blocker is confirmed, stop automatic retries for that run and contact the user.

Inspect and classify every due guarded run in each guardian patrol, but automatically resume at most one target run per patrol. If several targets are recoverable, choose the run that has been past its grace period the longest and leave the others for the next patrol after re-checking their current state. User-only blockers are not deferred by this one-recovery limit; contact the user as soon as the blocker is confirmed.

Never rerun a guarded task from zero merely because the original turn stopped. Before any resumed publish, comment, reply, DM, record creation, Playbook/methodology update, or scheduler change, re-check whether that side effect already succeeded. If the external action succeeded but Feishu state or the log is missing, repair only the missing durable state.

The guardian itself writes one operating log per patrol. A normal read-only patrol does not update `运营任务` just to record a heartbeat. Write business/task state only when recovery is triggered, scheduler/registry state is corrected, a real system error is recorded, or a user blocker is identified; those writes follow the Feishu notification rule.

## Handoff and recovery

A new AI operator should recover from durable state, not conversation history:

1. Load this Skill.
2. Resolve `Nexum 运营资料库 / 运营总览`.
3. Read `Nexum 运营资料库 / 运营方法` when the task requires operating judgment, prioritization, experiment design, review, or learning.
4. Read only the relevant `Nexum 运营中台` tables for the requested task.
5. Read the target channel Playbook.
6. When continuing recent operating work, read only the recent `运营日志` records needed to recover what was actually done and avoid repeated actions.
7. If continuing a guarded scheduled run, resolve its target `运行键`, read `Nexum 运营资料库 / 运营守护机制`, and inspect the matching task's guard configuration before resuming.
8. Verify current product facts through production Nexum/repository evidence when those facts matter.
9. Continue from the recorded state and avoid repeating completed external actions.
10. Write new durable data and learning back to Feishu and write the session log before declaring the operating task complete.

## Completion evidence

Do not call an operating task complete until the evidence appropriate to the requested operation exists:

- research: useful samples/opportunities are recorded with observable evidence;
- preparation: the content/opportunity state and deliverable are recorded;
- external execution: the resulting platform state has been re-inspected;
- monitoring: current observable metrics/signals are written to the existing record;
- learning: the experiment/experience/Playbook/methodology state reflects the conclusion and its evidence;
- scheduled task maintenance: the real scheduler state and `运营任务` registry agree.

For any meaningful operating execution covered by the logging contract, completion also requires the corresponding `运营日志` record. A blocked or partially completed session still gets a log with the real completed work and blocker. Writing the log itself does not require another log.

If only part of a combined request completes, report the completed parts and the exact blocker for the rest rather than claiming the whole operating cycle succeeded.
