# Common software document contract

Use for document meaning, classification and engineering research records.
Apply the main entrypoint's type-specific route for specialized content; file or
state work uses doc-management. Preserve the requested single-/multi-file result.

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

When external research supports a software claim or decision, record its source
URL, version or access date, applicability and limitations. Missing provenance
remains a gap; an external implementation does not authorize a product commitment.

Use the project's language and preserve valid structure. Prefer its templates;
packaged templates are optional. Fill retained fields from inspected facts, repeat
records for real items and remove inapplicable sections and placeholders. Missing
inputs can remain explicit draft gaps, never ready-to-use template tokens.

For model-visible instructions, read a discovered `prompt-authoring-spec` and its
selected references when available or required. A required missing spec blocks
its dependent work. Otherwise, check the generated instructions independently:
clear conditions/actions, trusted rules separated from source data, supported
capabilities, scope/approval boundaries and observable completion. Do not claim
a specification review that was not performed.

Scope review to requested/changed content and necessary dependencies; a full review
covers all applicable elements. Check examples, sources, version consistency and
local link targets/casing. Unavailable targets remain unverified, not assumed
broken; classification alone does not require a navigation audit.
Report findings with location, reachable reader/implementation error, evidence and
minimum correction. Separate text/source review from executed examples and runtime
validation; do not operate production merely to verify documentation.
