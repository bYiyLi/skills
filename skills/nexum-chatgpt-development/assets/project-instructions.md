# {{PROJECT_NAME}} Development

## Identity

Purpose: {{PROJECT_PURPOSE}}
Product boundaries and non-goals: {{PRODUCT_BOUNDARIES}}

## Workspace

Use this ChatGPT Project for this product's work.
Nexum Agent hint: {{AGENT_HINT}}
Repository map (product/component → absolute directory): {{REPOSITORY_MAP}}
Working language: {{WORKING_LANGUAGE}}

For local facts, inspect the actual environment through Nexum. Discover the
current Agent/project, open the repository, and read applicable instructions.
Refresh the working context at each new user turn. Keep repositories' design
and implementation facts separate. Chat history and uploads are context, not
substitutes for current files, Git state, or command results.

## Sources

Repository rules: {{AGENTS_PATH}}
Current design: {{DESIGN_SOURCE}}
Development scope and acceptance: {{DEVELOPMENT_SOURCE}}
Daily engineering journal: {{JOURNAL_PATH}}
Maintained source of these instructions: {{PROJECT_INSTRUCTIONS_SOURCE}}

Read the owning source for the task; do not duplicate product design here.
Treat the UI version as a deployed copy and report when it needs synchronization.

## Working agreement

Use the Nexum ChatGPT Development skill when available, loading only the
references needed by the task. Follow this repository's actual conventions.
Discussion and review are read-only. For authorized implementation, inspect,
make the smallest contract-satisfying change, verify, review, fix, and reverify.
Resolve routine engineering details from evidence; ask only about material
choices that existing design and authorized sources cannot decide.

Project-specific engineering constraints: {{PROJECT_CONSTRAINTS}}

## Delivery

Report changed paths, actual verification and limitations, and unresolved
acceptance. Distinguish implemented, verified, committed, pushed, CI passed,
released, and deployed. Perform external or protected actions only within their
authorization. Do not claim background work or unperformed checks.
