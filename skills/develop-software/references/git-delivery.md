# Deliver exactly the authorized Git outcome

Read this for commit, push, CI inspection, publication, or deployment. Treat
modification, validation, commit, push, successful CI, release, and deployment as
different states. Permission for one does not automatically grant the next; a
single explicit request can grant several.

## Before commit

Inspect branch, upstream, remotes, Git status, staged diff, unstaged diff, and
task-owned untracked files. Preserve user changes even in a file touched by this
task. Stage only inspected task hunks/paths. Inspect pre-staged changes before
committing; use a scoped commit or pause the commit if it would absorb unrelated
work. Do not stash, reset, discard, or clean user work to obtain a clean tree.

Ensure verification still covers the staged result. Check for secrets, local
state, debug artifacts, generated output, and unintended changes. Commit only
under commit authority, then inspect the resulting commit and remaining status.
Record the actual SHA, not a planned message as proof of submission.

## Before push or external publication

Verify the target account, repository, remote, branch, visibility, and outgoing
commits. A push sends history, not just the last file changed. Do not publish
unrelated local commits. Use the intended existing remote; an `origin` remote
is not necessarily GitHub. Preserve visibility and licensing unless a change
is authorized. Do not force-push or bypass branch protection to complete a task.

If remote history advanced, inspect the divergence before deciding a safe
continuation. Do not rewrite user commits without authority. After a failed or
interrupted push, read the remote ref before retrying; the write may already
have succeeded. Verify that the intended remote ref contains the actual commit.

Creating a GitHub repository, opening a pull request, changing visibility,
publishing a release, and deploying are distinct external actions. Perform only
those in the request, after their target and authority are resolved. An existing
private repository remains private; "on GitHub" does not mean publicly released.

## Read CI for the actual commit

When CI results are requested or required for completion, inspect runs/checks
for the pushed SHA and required jobs. Poll a running job within the active task.
Report failures and unavailable logs; do not equate a workflow file, successful
push, empty status list, or older green run with current CI success.

Repair an in-scope CI defect under existing implementation authority, reverify,
and repeat commit/push only within the request's delivery scope. An environment,
billing, access, or out-of-scope failure may leave code delivered with CI blocked.
State that distinction and the exact remaining requirement.

## Report observed state

Report changed paths and verified behavior, then commit SHA, pushed remote/ref,
and CI result or its unverified state. State explicitly when commit or push was
not performed. Keep a release or deployment out of the completion claim unless
that separate action actually ran and was verified.
