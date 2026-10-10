# Implementation plans, roadmap and progress

A plan answers what work is in scope, what it depends on, how to accept it and
what evidence exists. Requirements own product commitments; design owns the
technical contract. Read those inputs and current same-topic plans. Inspect
Git/runtime when they affect progress evidence. A bounded explicit task does not
need a separate design file merely to be planned.

## Decide plan units before stages or files

An implementation plan is a bounded unit with its own tracked scope, state and
completion. It is a Phase Plan when it represents a Phase in a roadmap. Internal
stages group work inside that unit; they may have dependencies and local tests.
A roadmap coordinates multiple independent plan units, not every implementation
step. The numbers of plan units, internal sections and Markdown files are
separate decisions.

1. Preserve the user's explicit number of plans and existing plan relationships.
   Without evidence of separate completion boundaries, organize one plan.
2. Split only work needing separately maintained scope, state and completion.
   Local testability, reviewability or use by a later step alone does not justify
   another Phase. Independent plans may run in parallel.
3. Add a roadmap only for multiple units or an existing repository requirement;
   retain and update an existing overview when working on one of its Phases.
4. Then choose internal stages and paths. A directory or template named phases
   never determines plan count.

For example, one scaffold refactor with Template -> init -> upgrade -> release
validation is one implementation plan with four internal stages, not four Phase
Plans. If the user corrects the level/count, stop dependent structural writes,
recheck the sources and correct within existing authority; ask only about an
unresolved material choice.

## Arrange concrete work and acceptance

Reuse a same-topic plan and stable item identities. Follow repository paths;
without conventions a single plan may use `docs/development/phases/NN-topic.md`.
Use `docs/development/README.md` only when an overview is needed. Installation,
run/debug instructions are usage guides regardless of a development filename.

A plan must make these facts recoverable, with headings sized to the task:

| Content | Required decision |
| --- | --- |
| Goal/scope | Observable result and excluded work |
| Inputs | Current requirement/design/decision constraining the work |
| Prerequisites | Actual dependencies and how readiness is checked |
| Work/deliverables | Changes or configuration and their responsible component |
| Acceptance | Expected results and verification entry for each deliverable |
| Review/fix/recheck | Relevant consistency/error checks and finding resolution |
| Completion | Results and mandatory checks that must hold together |
| State/evidence | Observed progress, checked state and remaining blockers |

Several work items may share integration acceptance. Local unit tests cannot
replace required actual connections, builds or environment verification. Do not
invent owners, dates, estimates or percentages. Preserve unresolved dependencies
instead of treating absent external inputs as delivered. Reference technical
decisions rather than re-deriving product behavior in the plan.

For a new plan without a repository template, optionally adapt
[../assets/phase-plan-template.md.tmpl](../assets/phase-plan-template.md.tmpl).
Its name permits either a single plan or a roadmap Phase; it mandates neither.
Use [../assets/roadmap-template.md.tmpl](../assets/roadmap-template.md.tmpl) only
for a needed overview. Populate real work, source links, criteria and evidence.

## Keep completion evidence current

Keep expected acceptance separate from actual observations. Evidence identifies
method/command, scope, environment, result and checked commit or worktree state.
Never invent a SHA for uncommitted work. Rerun checks whose inputs changed;
older success cannot substantiate new behavior. Missing, skipped, blocked and
failed checks are not passed; zero expected tests collected is not success.

A plan is implemented only after its deliverables, required checks and review
findings affecting acceptance are resolved. A plan document being written,
code existing, a local test passing or a commit existing is insufficient alone.
Commit/push is a completion condition only when the task/repository requires it
and the corresponding authority exists.

Do not delete unfinished work, weaken criteria or move failed acceptance to a
later Phase merely to match current code. An authorized scope change keeps its
reason and traceability to the earlier commitment. Maintain roadmap summaries
and links; the plan owns detailed work and evidence, and logs own history.
Retain original criteria when recording completion, rather than rewriting the
plan into a retrospective. Plan-only tasks end at the requested plan artifact;
implementation tasks continue through their entire authorized scope.
