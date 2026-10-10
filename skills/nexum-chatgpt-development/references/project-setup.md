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

For Project Instructions creation or review, use a discovered
`prompt-authoring-spec` and its selected references when available or required.
A required missing spec blocks dependent work; otherwise apply the local checks
below without claiming that external specification was reviewed. Do not make
ordinary connection checks depend on prompt-authoring guidance.

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
are draft data gaps, not a reason to drop these execution rules. Review the actual
output independently: identifiable conditions/actions, consistent terms and
requirement strength, scope, approvals, unavailable inputs, recovery and completion.
Separate trusted instructions from retrieved text/examples; formatting is not a
security control. Request decisions and brief rationale, not hidden reasoning or
coercive personas. API model/temperature/token parameters are not ChatGPT Web
settings, and prompt text does not grant tools, delegation or enforcement. Ground
new host-capability claims in current official documentation or observed controls;
report unsupported claims as unknown. Review-only reports findings without edits.

When repository writing is authorized, keep the maintained source in its existing
location, otherwise `docs/chatgpt-project.md`. Keep private machine settings out
of public repositories; use an authorized private location when needed. Treat
ChatGPT UI text as a deployed copy and report updated, user-confirmed or pending
status separately. Do not overwrite newer UI/source changes without comparison.
When authorized setup also creates/updates AGENTS and an instruction maintenance
source exists inside the repository and is appropriate for its readers, add the
verified repository-relative pointer to AGENTS. Do not expose an external private
source path in a public repository or fabricate a local counterpart. Use the
discovered develop-software repository-instruction route for that artifact; do not
make a ChatGPT-specific field mandatory in all repositories or create a source
just to fill one. Verify the link and that it claims no saved UI state.

## Verify discovery separately from installation or use

Read current discovered Skill metadata and the actual entrypoint. A GitHub file,
a discovered Skill, a loaded reference and a successful task are different states.
No assumption that Codex `$skill` syntax or `agents/openai.yaml` activates a Skill
in this Web session. Supplied repository Skill sources can be explicitly read
without claiming personal installation.

For Web software development, verify both nexum-chatgpt-development and
develop-software entrypoints and the current task's routed resources. Use current
discovery first, then any authorized explicit repository source; an available
source can be read without claiming installation. Verify package-local references
relative to each actual root, not one assumed shared directory.

An authorized full Web-development installation includes both packages from the
intended source. A Nexum-only/environment-only install remains limited to that
scope. Inspect destinations and preserve user edits; use the supported installer,
then refresh `project.open` and verify each required name, root and resource.
Do not invent installer flags or dependency metadata. Without installation
authority, report the precise missing source and continue independent work; never
write personal Skill folders merely to satisfy a dependency. Discovery, successful
loading and actual development are separate results.

Report repository mapping, source readability and actual UI/discovery evidence.
Do not claim full setup when a requested UI or environment step remains pending.
