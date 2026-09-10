# Maintain current design and dated history

Read this before changing design, development state, or the daily journal. Reuse
the source paths declared by the repository; `docs/design.md`,
`docs/development/`, and `docs/vlog/` below are new-project defaults.

## Change the correct source

Write current behavior and technical decisions into the design authority. Put
scope, dependencies, acceptance evidence, and progress into development docs.
Use phases only when dependencies or independently verifiable milestones justify
them. Link each acceptance criterion to a test, inspection, or runtime result;
an unchecked promise is not evidence.

When implementation exposes an undefined behavior, inspect the current contract,
existing code/tests, and applicable primary references. Within implementation
authority, decide and document the smallest amendment supported by established
goals before building on it. If alternatives materially change the product
contract and the evidence does not select one, record the unresolved choice and
pause dependent implementation. In discussion/review, propose the amendment
without changing files unless writing was also requested.

Update affected consumers after a contract change. Resolve a stale summary by
linking or correcting it, not by copying the full design into README, AGENTS,
Project Instructions, and the journal. External research records source URL,
version or access date, applicability, and limitations; a reference project's
implementation is evidence, not an automatic product requirement or dependency.

## Keep a daily engineering journal

Here `vlog` means the project's written decision/development journal, not video.
Use `docs/vlog/YYYY-MM-DD.md` unless an existing daily log convention already
serves this role. One day may contain multiple timestamped task entries. Derive
the date from the repository's declared IANA timezone; if none exists, use UTC
for the entry and state it explicitly. Do not use a guessed date from chat
history or silently switch between the developer's and Agent's local timezone.

For authorized repository changes, append a meaningful task entry after a
decision, a verified milestone, or a genuine blocker. Use the daily-log asset
routed from SKILL.md. A request restricting writable files takes precedence;
return the journal entry in chat when persistence is outside that scope. Record:

- The task and authorization scope; decisions with rationale and authoritative
  source locations, separating adopted decisions from unresolved proposals.
- Changed areas and observed verification commands/results, including skipped,
  failed, or unavailable checks and the revision/worktree state they describe.
- Remaining findings or blockers and the next concrete action, when any.

Keep entries concise and evidence-based. Omit empty sections, chat transcripts,
raw build output, secrets, opaque sessions, and routine tool-call narration.

In the asset, DATE is `YYYY-MM-DD` and TIME is `HH:mm` in JOURNAL_TIMEZONE.
TASK_TITLE and TASK_SCOPE identify the current request and its authorization.
DECISIONS_WITH_RATIONALE_AND_SOURCE, CHANGED_AREAS, VERIFIED_STATE,
VERIFICATION_RESULTS, and FINDINGS_BLOCKERS_AND_NEXT_ACTION are concise Markdown
from observed work, not template defaults. For an existing daily file, append
only the task section; preserve its date/timezone header. Report a conflicting
timezone convention instead of silently reinterpreting existing entries.

Use Git history as commit/push history rather than copying it into every entry.
Do not create endless follow-up commits solely to log the journal's own commit.

Review/discussion alone does not authorize a journal write. Return the record
in chat unless persistence is requested. Existing historical entries remain
historical: append a correction or supersession note with the current design
pointer instead of silently rewriting what was decided at the time. On a
concurrent append or revision conflict, reread and merge the new entry while
preserving the other author's text.

## Resume from evidence, not a transcript

On resumed work, inspect current Git state and the applicable design/plan first.
Read only recent or searched journal entries that explain the current task.
Recheck their commands, revisions, pending processes, and open findings before
acting. Reuse an existing task/phase record for a recovery checkpoint; do not
add a separate HANDOFF file by default. A log entry explains what happened; it
does not override current design or prove that a pending action succeeded.
