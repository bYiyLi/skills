# Product requirements and acceptance

Use for creating, revising or reviewing requirements, including PRD, feature
specifications and SRS. Establish the problem, goal, actors, boundary, applicable
baseline and authoritative decisions. Code describes the current implementation;
it cannot supply an unapproved product promise. Missing goals or sources can be
findings in review, not prerequisites for starting a text assessment.

## Choose the scale, not a mandatory template

Reuse the project's PRD or other established requirements source. A bounded
feature normally needs a feature spec; a system/subsystem baseline with broader
interfaces or long-term traceability may need SRS. Role counts or the word
security do not force an upgrade. Only an actual contract or project requirement
makes a particular format mandatory. Review does not itself convert the format.

For a new artifact with no suitable repository template, optionally adapt
[../assets/feature-spec-template.md.tmpl](../assets/feature-spec-template.md.tmpl)
or [../assets/srs-template.md.tmpl](../assets/srs-template.md.tmpl). Populate their
problem, actors, scope, records and acceptance from inspected sources. Expand
records for real requirements and remove inapplicable sections, not requirements.

A feature specification covers problem/evidence, goal, scope, actors, formal
requirements, constraints/dependencies, acceptance, assumptions and unresolved
issues. A system specification additionally establishes audience, stakeholders,
system context and cross-requirement traceability. Stakeholders include affected
or responsible parties who do not directly interact with the system; actors are
its interacting roles. Cover both from the supplied sources, even without a
packaged template. Equivalent semantic coverage needs no fixed headings.

## Preserve a recoverable requirement record

Each formal requirement has a stable unique identity, one normative statement,
a locatable source and an observable verification/acceptance entry. Existing
numbering or anchors may provide identity. Classify through sections or records.
Add priority only when actual prioritization exists; do not invent owners,
approval, dates or priorities to fill a template.

Check applicability of functional, interface, data, quality, security and
operational requirements. Cover applicable classes; explain non-applicability
only when omission could be mistaken for a gap. A constraint prescribing system
behavior is a formal requirement; an established external condition may remain
a sourced dependency. A mandated implementation choice is a sourced constraint,
not something the product goal necessarily implies.

For each in-scope formal requirement, check:

- Actor, behavior, object, conditions and exceptions are identifiable.
- Requirement strength is clear; preferences do not become obligations.
- Quantities have units, range, direction and endpoints, or an observable
  qualitative criterion when a numerical measure is inappropriate.
- Identity is stable; statements neither duplicate nor conflict.
- Source and verification support the stated claim and baseline.

## Revise and assess the actual scope

Reuse the owning source and preserve unaffected requirements. Full review checks
every formal requirement and overall consistency; limited review/revision checks
the specified or changed elements and necessary dependencies, not an undefined
subset of 'important' requirements or unrelated existing defects.

Keep facts, decisions, assumptions, examples and unresolved conflicts distinct.
Ensure requirements connect to sources and acceptance without relying on behavior
present only in an example. Interface/data boundaries, permissions, errors and
operational constraints must be covered where applicable. Product choices that
cannot be settled from authority remain unresolved; pause only dependent work.

A draft may name missing sources or undecided behavior. A formal baseline needs
clear scope, sourced verifiable requirements and consistency; writing it does
not establish approval. Acceptance criteria are expected results, not evidence
that implementation has passed. Report content coverage, actual delivery and
remaining gaps; continue implementation only when the user's task includes it.
