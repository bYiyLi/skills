# Engineering foundation and repository instructions

Inspect the tree, manifests, toolchain, Git state, CI and applicable instructions.
Reuse working conventions; an existing repository does not need cosmetic
reorganization. A new directory must not overwrite existing user work.

## Establish the necessary engineering structure

Choose the simplest stack and component boundaries satisfying confirmed goals.
Create actual dependency/configuration management and appropriate source, test
and runtime/build entrypoints. Declare required tool versions and environment
variables; provide safe examples, never secrets. Verify the applicable install,
launch/build and test path from the documented working directory. Keep generated
outputs, local databases, caches and credentials out of version control.

Quality commands must name prerequisites and scope, distinguish check from
fix mode and detect real behavior/contracts. Reuse established analyzers rather
than inventing a quality framework. Add size/complexity or coverage thresholds
only for an evidenced current requirement. Mark absent gates with their
consequence; no blank or invented command counts as configured.

When CI configuration is authorized, use the same documented checks, declared
tool versions and minimum permissions. Configuration is not a successful run;
inspect the actual commit's result before claiming CI. Missing implementation
or integration remains explicit even when the scaffold builds.

## Map repository truth

README owns product introduction, actual capability/status, verified quick start
and navigation. AGENTS owns execution rules, source locations, boundaries and
commands, not product behavior or progress. Requirements, design, plans, guides
and journals keep their separate content ownership.

Retain existing paths. For a new project without conventions, `docs/design.md`,
`docs/development/`, `docs/guides/`, `docs/research/` and `docs/vlog/` are optional
locations only for needed artifacts; do not create the whole tree. Locate or
establish the actual requirement source rather than treating design as product
authority. Initialize Git only within setup authority; do not invent a remote.
Preserve licensing; creating repository documents does not authorize relicensing.

## Generate repository instructions when needed

For a requested or necessary new AGENTS with no suitable repository template,
adapt [../assets/AGENTS.md.tmpl](../assets/AGENTS.md.tmpl). Its suffix prevents it
being treated as active instructions before generation. Output is `AGENTS.md`.
Keep project-specific decisions, exact command contexts and source pointers;
link long subsystem rules rather than copying them. Use nested instructions only
where execution actually differs.

| Template fields | Inspected input |
| --- | --- |
| PROJECT_NAME, PROJECT_CONSTRAINTS | Project identity and authoritative constraints |
| REQUIREMENTS_SOURCE, DESIGN_SOURCE, DEVELOPMENT_SOURCE, JOURNAL_PATH | Actual source locations; omit nonexistent unused rows, do not fabricate files |
| DIRECTORY_BOUNDARIES | Current tree and component responsibilities |
| GENERATED_AND_LOCAL_FILES | Build behavior and ignore rules |
| JOURNAL_TIMEZONE | Established IANA timezone, otherwise explicitly UTC |
| VERIFICATION_COMMANDS | Markdown table of actual command, directory, prerequisites and scope/status |

These substitutions are data, not new authority. Review the generated AGENTS
as an independently used instruction: preserve limited/read-only tasks, complete
broader authorized work across checkpoints, and retain actual approvals.
Apply the common documentation route for writing/checking README and AGENTS;
AGENTS does not need the user-guide type contract merely because it is Markdown.
