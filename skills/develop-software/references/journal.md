# Engineering journal

## Keep a daily engineering journal

Here `vlog` means the project's written decision/development journal, not video.
Use `docs/vlog/YYYY-MM-DD.md` unless an existing daily log convention already
serves this role. One day may contain multiple timestamped task entries. Derive
the date from the repository's declared IANA timezone; if none exists, use UTC
for the entry and state it explicitly. Do not use a guessed date from chat
history or silently switch between the developer's and Agent's local timezone.

When the target repository already uses a development journal, project setup
establishes one, or the user requests one, append a meaningful task entry after a
decision, verified milestone, or genuine blocker. For a new entry without an existing template, adapt
[../assets/daily-log.md](../assets/daily-log.md). Do not create a journal in an existing repository solely because
code changed. A request restricting writable files takes precedence; return the
entry in chat when persistence is outside that scope. Record:

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

For discussion or review-only work, return any journal note in chat unless the
request separately authorizes persisting that note; this does not authorize
repairing the reviewed subject. Authorized implementation follows the existing-
journal/setup/request conditions above. Existing historical entries remain
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
