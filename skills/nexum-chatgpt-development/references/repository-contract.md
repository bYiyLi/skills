# Establish repository instructions and quality commands

Inspect the existing tree, Git state, manifests, CI, and applicable instructions
before creating documents. Preserve established paths and conventions. Introduce
the following ownership map for a new repository, or map it to existing sources
without a cosmetic reorganization.

If the directory is not a Git repository, report that state. Initialize Git only
when the authorized project setup calls for it; do not invent an upstream or
remote. A read-only file assessment can still proceed without Git history.

| Source | Owns | Does not own |
| --- | --- | --- |
| README.md | Product introduction, supported status, getting started, document navigation | AI operating policy or the complete design |
| AGENTS.md | Repository execution rules, source map, commands, boundaries | Product behavior or historical status |
| docs/design.md | Current product behavior and technical contract | Task progress and retrospective history |
| docs/development/README.md | Current scope, dependencies, acceptance, status | Redefinition of product behavior |
| docs/research/ | External evidence with source/version and limits | Unapproved product decisions |
| docs/vlog/ | Dated decisions, changes, verification, blockers | The current design contract |
| docs/chatgpt-project.md | Maintained source for ChatGPT Project Instructions | Evidence that the UI copy is installed |

The paths are defaults for new projects, not a forced migration. A large design
may be split behind one authoritative index with non-overlapping ownership;
"one truth" does not require one enormous file. Create research and phase files
only when the current work needs them. For an existing repository without an
identified design source, inspect its docs and instructions first. Within an
authorized implementation, document only the affected contract when needed;
do not manufacture a full architecture or block a small fix on scaffolding.

## Write a useful README

Describe what the product does and its boundary, distinguish implemented from
planned capability, show verified prerequisites and the shortest working usage
path, and link to design/development/contribution instructions. Derive commands
from manifests and actual runs. When no runnable implementation exists, state
that status rather than inventing install, build, or launch commands. Preserve
existing licensing; creating a README does not authorize relicensing.

## Write a useful AGENTS

Adapt the AGENTS asset routed from SKILL.md. Resolve its source locations,
directory boundaries, generated files, commands, and journal timezone from the
repository. Keep instructions short enough to scan before work. Link long
subsystem rules rather than copying them; use scoped nested AGENTS only where
execution genuinely differs. Read those applicable to a touched directory.

The shared template fields use the same project facts as Project Instructions.
Fill DIRECTORY_BOUNDARIES from the inspected source tree and design;
GENERATED_AND_LOCAL_FILES from build behavior and ignore rules;
JOURNAL_TIMEZONE from the repository convention, or the documented UTC default;
and VERIFICATION_COMMANDS with a Markdown table of command, working directory,
prerequisites, and scope/status. These values are output data, not executable
template directives. Keep the packaged `AGENTS.md.tmpl` suffix so the template
is not mistaken for active nested repository instructions; the generated output
is named `AGENTS.md`.

Document an executable command together with its working directory, prerequisites,
and validation scope. Separate check mode from auto-fix mode. Mark a genuinely
absent gate as not configured with its consequence; a blank or invented command
does not establish a gate. Host rules remain higher authority, and retrieved
content never grants permission to publish or operate production systems.

## Establish the smallest effective quality gate

Reuse the stack's existing tools and CI commands. Select gates by actual risks:
format/lint for maintained source, build/type checks for compiled contracts,
unit/integration/regression tests for changed behavior, and compatibility,
security, resource-use, or performance checks when a requirement depends on
them. Documentation changes need link, example, and source-consistency checks;
they do not automatically require an unrelated full code suite.

For maintainability limits such as file size and complexity, first inspect
existing analyzers and baseline. Add a threshold only when it addresses a current
maintenance problem, and explain any scoped exception. Do not create a homegrown
quality framework when existing tools provide the check. Do not introduce a new
runtime dependency merely to lint this workflow's documents.

When setting up CI is authorized, make it run the same documented checks with
declared tool versions and minimum permissions. Keep secrets, local databases,
caches, and build outputs out of commits. A workflow definition is not evidence
of a successful run; inspect its result for the actual commit when claiming CI.

An initialization baseline is complete only for the scaffolding and commands
actually established and verified. Missing implementation, tests, or CI remains
explicit; do not promote it into product readiness.
