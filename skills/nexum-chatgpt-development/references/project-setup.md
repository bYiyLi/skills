# Establish the ChatGPT Web workspace

Read this for project initialization, workspace repair, or skill discovery. It
does not require reorganizing an existing workspace for an unrelated code task.

## Establish isolation without claiming capabilities

For a new independent product, guide the user to a separate ChatGPT Project
before ongoing development conversations. Keep its project instructions, chats,
and uploaded context scoped to that product. A deliberate multi-repository
project needs an explicit repository map and separate design ownership; opening
one repository does not authorize changes to another.

Check available app/browser tools before deciding whether setup can be performed.
Use only a supported, authorized interface. Without one, deliver the instruction
text and the concrete UI steps for the user; mark UI setup pending. Continue
independent authorized repository preparation. A generated file is not evidence
that a ChatGPT Project was created or its settings saved.

Consult the current [OpenAI Projects documentation](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt)
when giving UI or memory instructions. Guide creation through New project and
configuration through Project settings, adjusting to the observed UI. Recommend
Project-only memory when the user needs cross-project memory isolation and the
account supports it. Ordinary project organization alone is not proof of memory
isolation. Respect intentionally disabled memory; do not turn it on, change
sharing, or claim a privacy boundary through prompt text. If current docs or
settings cannot be checked, distinguish verified organization from unverified
memory behavior instead of presenting stale UI details as current.

## Generate project-specific instructions

Use the project-instructions asset routed from SKILL.md. Preserve its sections:
Identity, Workspace, Sources, Working agreement, and Delivery. These are this
workflow's template convention, not an OpenAI-required schema.

Fill purpose, non-goals, Agent hint, canonical repository path, source map, and
working language from the user's request and inspected repository. Discover
opaque Nexum IDs at runtime; store neither context IDs nor process IDs in durable
instructions. Include only project-specific constraints that change decisions.
Point to design and AGENTS instead of copying their changing contents. Keep
implementation progress and daily history out of Project Instructions.

Template fields are text unless specified otherwise:

| Fields | Value source |
| --- | --- |
| PROJECT_NAME, PROJECT_PURPOSE, PRODUCT_BOUNDARIES, PROJECT_CONSTRAINTS | User-approved goals and current design |
| AGENT_HINT, REPOSITORY_MAP | Live Agent discovery and opened canonical directories; map each repository independently |
| WORKING_LANGUAGE | Existing project convention or user's working language |
| AGENTS_PATH, DESIGN_SOURCE, DEVELOPMENT_SOURCE, JOURNAL_PATH, PROJECT_INSTRUCTIONS_SOURCE | Actual repository source map; use repository-relative paths where applicable |

Save a repository-maintained instruction source at `docs/chatgpt-project.md`
when repository writing is authorized and no existing source already serves that
role. Treat the ChatGPT UI text as its deployed copy. After a source change,
report whether that copy was updated, user-confirmed, or remains pending. Keep
machine-specific private settings out of a public repository; use a private
workspace copy when real paths or organizational details cannot be published.

## Open the actual environment

Resolve the desired Agent and directory from live `project.list` results and the
workspace map. If several targets remain plausible, ask for the one distinction
that changes the target. Do not infer an absolute path from a product name.
When creating a directory, first open an authorized existing parent and confirm
the new destination does not already contain user work.

Use `project.open` before Files/Process operations. An `authorization_required`
response needs its actual approval flow; do not work around it with another
command. An offline Agent or unavailable connector blocks local claims. Report
the missing capability while completing only work supported by available data.

## Verify skill loading separately from GitHub delivery

Read the current Nexum-discovered skill metadata and the actual `SKILL.md` path.
Follow the supported discovery/install mechanism for that environment; GitHub
availability alone does not install or activate a skill in ChatGPT. Do not
assume Codex `$skill` syntax or `agents/openai.yaml` controls this Web session.

For an installation request, inspect the existing destination and preserve its
user changes. Use a verified skill-discovery root, then refresh `project.open`
and confirm the skill's name, description, root, and readable references. Report
discovery and successful task execution separately. If installation is not part
of the request, provide the location/use instructions without changing personal
skill directories or connector settings.

Setup evidence consists of the repository mapping, readable instructions/source
map, actual baseline results, and the observed or user-confirmed UI state. Mark
unknowns individually; do not call the whole workspace configured when its
required UI or environment step is still pending.
