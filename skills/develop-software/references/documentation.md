# Common software document contract

Use this for document content, classification, file placement or lifecycle work.
Type-specific requirements, design, plan and usage rules come from the main
entrypoint's matching route. Pure file/status or mechanical edits need no full
content review. Preserve the requested single-file or multi-file result.

## Identify the owning source and reader result

| Reader result | Content owner |
| --- | --- |
| Product scope, required behavior, constraints and acceptance | Requirements |
| Internal structure, interfaces, data, runtime and technical decisions | Design / ADR |
| Work, dependencies, deliverables, acceptance evidence and progress | Implementation plan / roadmap |
| Learn a use path, perform an operation or query an interface | Tutorial, guide or reference |
| Understand a product-use concept | Usage explanation |
| Establish repository execution policy | AGENTS / scoped repository instructions |
| Explain past decisions and checks | Journal, not current design or plan |

Classify by the actual reader goal, not names such as development, implementation
or FAQ. Installation steps are not an implementation plan. Concepts, steps and
parameter lookup serving one continuous task may share a document. Split only
when distinct reader results need separate navigation/maintenance; one truth may
span files behind an authoritative index. Do not force research or history into
another type. In read-only classification, report findings without reorganizing.

For facts affecting action or acceptance, identify the applicable version, branch,
release or decision and its evidence. Distinguish confirmed facts, accepted
decisions, assumptions, unresolved issues and examples without mandatory labels.
Resolve conflicts by authority, scope and applicable version/freshness; preserve
unresolved conflicts. Code proves implementation, not product authorization;
a proposed command is not evidence it ran. Traceability required by the content
contract must be recoverable; add other links only when they help a real consumer.

## Create, revise and manage files

Inspect repository instructions, document entrypoints, current files, templates
and generators. Reuse the source already owning the result; do not ask permission
again merely because revise is more appropriate than create. Use the user's
path, then repository convention, then a simple non-overwriting location.
A consequential conflict over ownership, a published entrypoint, compatibility
links or retention needs resolution; absent conventions alone do not.

Use the project's language and preserve valid structure. Existing templates take
precedence; packaged templates are optional for new artifacts. Their named
placeholders denote the corresponding inspected fact, requirement, design,
work item or evidence. Repeat records for actual items, remove inapplicable
sections and replace every retained placeholder. Missing inputs may remain
explicit gaps in a labeled draft, never as ready-to-use template tokens.

Keep established metadata and lifecycle expressions. Add no owner field,
frontmatter, approval state machine or fixed document tree without a consumer.
A document being written does not make it accepted, approved, released or
implemented. Meet the real conditions and authority for protected states.
When drafting model-visible instructions, separate trusted governing text from
source data, preserve host authority and use applicable authoring guidance.

Authorized moves/archives update references and preserve required history.
Deletion additionally needs authority for the actual targets and checks of
references, retention and recovery. An already-deleted target can be assessed
from its prior identity and Git/reference evidence; absence is not by itself a
missing input. For cross-document actions use the synchronization route.

## Validate the requested artifact

Reread the saved output when persistence was requested. Check the actual diff,
local links/casing, examples, source and version consistency, placeholders and
status relationships; in Git run `git diff --check` and separately inspect new
files. A pure metadata/path change must leave unrelated body content intact.
Scope content review to changed/requested elements and necessary dependencies;
full review covers all applicable elements of the chosen type.

Report actionable findings with location, reachable reader/implementation error,
evidence and minimum correction. Review completion need not mean the reviewed
subject passes. Distinguish source review, executed examples and reader/runtime
validation. Do not run production or external writes merely to verify a guide.
