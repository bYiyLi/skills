# ChatGPT workspace and Skill discovery

Use for requested workspace setup/repair, Project Instructions or Skill loading,
not for routine product initialization or an unrelated code change.

## Establish the requested ChatGPT workspace

For a new independent product, recommend a separate ChatGPT Project to keep its
instructions, chats and supplied context scoped. Preserve deliberate shared or
multi-repository workspaces; their repository map must distinguish ownership.
Project UI availability is not a prerequisite for independent repository work.

Inspect supported app/browser tools before deciding whether an authorized UI
change can be performed. Without a supported writer, return the instruction
text and any steps supported by current documentation or observed UI, marking
UI work pending. If neither source can be checked, leave the exact UI procedure
unverified rather than inventing it. A generated document is not evidence that
the Project exists or that its settings were saved.

Before giving UI or memory directions, consult current
[OpenAI Projects documentation](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt)
when reachable and inspect the user's UI when available. Limit each claim to
what those sources actually establish; documentation-backed general instructions
do not prove this account's settings. Project organization alone does not prove memory isolation.
Recommend project-only memory only for a requested isolation need and supported
settings. Respect intentionally disabled memory; do not turn it on or change
sharing without authority. If settings/docs cannot be checked, label those
claims unverified rather than prescribing stale UI behavior.

## Maintain the Project Instructions source

For a requested new instruction text without an existing suitable template,
adapt [../assets/project-instructions.md](../assets/project-instructions.md).
Preserve identity, workspace, sources, working agreement and delivery meanings;
these sections are package conventions, not a required OpenAI schema.

| Fields | Value source |
| --- | --- |
| PROJECT_NAME, PROJECT_PURPOSE, PRODUCT_BOUNDARIES, PROJECT_CONSTRAINTS | Current authoritative project goals and constraints |
| AGENT_HINT, REPOSITORY_MAP | Inspected Agent names and canonical repository locations; supplied but unverified locations stay draft |
| WORKING_LANGUAGE | Project convention or user language |
| AGENTS_PATH, REQUIREMENTS_SOURCE, DESIGN_SOURCE, DEVELOPMENT_SOURCE, JOURNAL_PATH, PROJECT_INSTRUCTIONS_SOURCE | Inspected source map, preferably repository-relative |

Include only project-specific facts and boundaries that change decisions. Point
to governing sources rather than copying design, progress or daily history.
Do not store ephemeral context/process IDs. Each retained source row must name
an inspected source or one actually established by the current setup. Omit unused
missing rows; a real needed source gap stays explicit. No invented source files
just to complete a template, and design does not replace product requirements.
Replace all retained placeholders; missing mandatory fields mean draft, not
ready-to-use instructions. Before delivery, check that the generated text retains
the template's software-work requirement to read `develop-software`, its workspace-
only exception, and its read-only/full-task boundaries. Missing repository paths
are draft data gaps, not a reason to drop these execution rules. Review source
authority without claiming a required Skill is already installed or readable.

When repository writing is authorized, keep the maintained source in its existing
location, otherwise `docs/chatgpt-project.md`. Keep private machine settings out
of public repositories; use an authorized private location when needed. Treat
ChatGPT UI text as a deployed copy and report updated, user-confirmed or pending
status separately. Do not overwrite newer UI/source changes without comparison.

## Verify discovery separately from installation or use

Read current discovered Skill metadata and the actual entrypoint. A GitHub file,
a discovered Skill, a loaded reference and a successful task are different states.
No assumption that Codex `$skill` syntax or `agents/openai.yaml` activates a Skill
in this Web session. Supplied repository Skill sources can be explicitly read
without claiming personal installation.

For an authorized installation, inspect destination contents and preserve user
changes. Use a verified discovery root and supported installation mechanism;
then refresh `project.open` and check name, description, root and readable
resources. Without installation authority, do not change personal Skill folders
or connector settings. A required absent package remains a reported dependency,
not a reason to recreate it from memory.

Report repository mapping, source readability and actual UI/discovery evidence.
Do not claim full setup when a requested UI or environment step remains pending.
