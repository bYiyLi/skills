# Software usage documentation

Create, revise or review documentation for readers learning, operating, querying
or understanding the product. Establish the reader goal, interface/product scope,
version/environment and factual sources. A purely mechanical typo/link edit uses
the main doc-management route without an interface/body-content audit.

## Select the reader result

| Reader goal | Content contract |
| --- | --- |
| Learn a capability from a supported starting point | Tutorial: progressive steps with observations and final verification |
| Complete a known task | How-to: concise prerequisites, dependency-ordered actions and observable result |
| Operate/manage a system | Operator guide: environment, permissions, impact, checks and actual recovery/escalation |
| Query commands/interfaces/fields/errors | Reference: locatable facts for the applicable baseline |
| Understand a product-use concept or behavior | Explanation: supported why and user-visible boundaries, not internal architecture |

Concepts, steps and necessary parameter lookup can serve one continuous task in
one document. Preserve a single-file request; different content types alone do
not justify extra documents. FAQ is an arrangement, not a type. Multiple distinct
reader results may need separate navigation; reuse effective current structure.

## Write from the actual contract

Inspect source/interfaces and relevant runtime results. Preserve accurate syntax
when execution is unavailable; label its validation limit rather than calling
unrun content invalid. A proposed command or old guide is not current runtime
evidence. Give each applicable step an action and observable result, failure
symptoms and evidence-based diagnostic/recovery entry where failure matters.

For controlled access, state reader permissions. For high-impact, irreversible
or state-changing operations, put applicable environment checks, impact and
recovery/escalation before the risky step. Do not imply that writing or reading
instructions grants the executing agent authority to perform those operations.
Do not add approval/rollback rituals to ordinary read-only queries merely because
their server is production. Verify examples only in authorized safe environments.

Tutorials introduce only concepts needed by the current step and distinguish
unexecuted learning paths from verified ones. How-to troubleshooting starts with
a symptom and ends with recovery or escalation. Operator guides include state
checks and meaningful stop/recovery boundaries. Explanations distinguish evidence
from interpretation and do not expand into unrelated design or implementation.

## Check the CLI/API reference surface

Make applicable information recoverable, using shared context rather than
repeating every field on every entry:

- Canonical identifier/purpose and version/availability.
- Syntax/endpoint and method, inputs/parameters or explicit no-input state.
- Outputs, observable results, known errors, failure semantics and exit/status.
- Locatable evidence for each fact group; include provenance in the delivered
  document when required or needed by its reader, not as automatic decoration.

Add authentication/authorization for controlled access; headers, request bodies,
response schemas, pagination/rate limits for applicable APIs; environment,
configuration, interactive behavior and exit codes for applicable CLIs. Include
supported examples, limits, compatibility or deprecation when they change use.
A conceptual glossary needs no endpoint schema. State non-applicability only
when omission would mislead; unknown fields remain explicit gaps.

## Templates and completion

For new documents without a suitable repository template, optionally adapt
[../assets/tutorial-template.md.tmpl](../assets/tutorial-template.md.tmpl),
[../assets/how-to-template.md.tmpl](../assets/how-to-template.md.tmpl), or
[../assets/reference-template.md.tmpl](../assets/reference-template.md.tmpl)
for the corresponding reader result. Operator guides and explanations follow
the contracts above; do not force them into an unrelated template. Substitute
inspected reader, applicability, action, syntax and evidence facts; remove
inapplicable sections, not known limitations.

Review all applicable information for a full review, or only specified content
and necessary dependencies for a limited one. Check examples match the contract,
inputs/returns are accurate and prerequisites/safety boundaries are usable.
Report concrete reader errors and minimum corrections. Content, persisted file,
source review, actual execution and publication are different completion claims.
Unresolved information that would mislead the reader keeps that part draft or
partial, without erasing accurate independent content.
