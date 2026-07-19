# Naming and Selection Contracts

Use this reference when choosing or reviewing a Skill name, description,
prerequisite, sibling boundary, or collection-level selection contract.

## Define the Target Collection

Use the Skill collection explicitly supplied by the task. If the task supplies
none, use the collection actually exposed on the intended selection surface. Do
not substitute the directory containing the specification or the current working
directory unless the task identifies it as the target collection.

If the target collection cannot be inspected, mark name collision, sibling
overlap, and selection conclusions unverified. Treat the name and description as
provisional only in those dimensions and continue decisions that do not depend
on the collection.

## Name by Primary Type

| Type | Preferred form | Examples |
| --- | --- | --- |
| `capability` | `<canonical-subject>` or `<domain>-<subject>` | `linear`, `agent-browser` |
| `workflow` | `[<scope>-]<verb>-<object>`; for a transformation, `[<scope>-]<source>-to-<target>` | `gh-fix-ci`, `spec-to-backlog` |
| `guidance` | `<scope>-spec`, `<scope>-standards`, or `<scope>-guidelines` | `skill-authoring-spec`, `react-performance-guidelines` |
| `router` | `<domain>-router` | `slack-router` |

Choose a guidance suffix by authority:

1. Use `-spec` for the complete authoritative contract for a scope.
2. Otherwise use `-standards` for mandatory, auditable constraints within a
   scope.
3. Otherwise use `-guidelines` for contextual recommendations whose authority
   is not established.

Do not infer a suffix from request words such as `rules`, `best practices`, or
`requirements`. For mixed content, use the authority of the rules carrying the
primary responsibility. Split the responsibility when one suffix would
misrepresent peer rule sets with different authority.

Check every candidate name:

1. Use lowercase letters, digits, and single hyphens, with fewer than 64
   characters.
2. Do not start or end with a hyphen or use consecutive hyphens.
3. When the verified native format maps a Skill name to a directory, require the
   directory name to match.
4. Use domain terms present in observed requests or written selection cases.
5. Use the shortest name that still identifies the primary responsibility.
6. Add a product, domain, or tool prefix only to remove ambiguity, prevent a
   collision, or improve selection.
7. Search the target collection before accepting the name. Exclude the target's
   current directory when revising it.
8. Keep trigger conditions, prerequisites, scope boundaries, and exclusions in
   `description`, not in the name.

Avoid generic role or container suffixes such as `-skill`, `-agent`,
`-assistant`, `-helper`, `-manager`, `-workflow`, `-process`, and `-toolkit`.
Retain one only when it is part of the canonical subject or product identity.

Avoid vague modifiers such as `advanced`, `smart`, `ultimate`, `best`, and
`pro`. Do not encode an implementation term such as `cli`, `api`, `mcp`,
`script`, `plugin`, `local`, or `remote` unless it changes which requests should
select the Skill.

Do not add metadata merely to persist the primary type. Express the type through
the responsibility, name, and description.

## Write the Description as a Selection Contract

Build the description from:

```text
description =
  responsibility
  + applicability
  + [hard prerequisite]
  + [nearest-sibling boundary]
```

Always include:

- **Responsibility**: the concrete result, capability, routing decision, or
  guidance the Skill contributes.
- **Applicability**: observable request signals such as intent, subject,
  artifact, state, or desired result.

Emphasize the primary type:

| Type | Description emphasis |
| --- | --- |
| `capability` | Canonical subject and representative independently invocable operations or results. |
| `workflow` | Starting intent or state and the bounded result owned. |
| `guidance` | Host task and the rules, knowledge, or method contributed without implying ownership of the host result. |
| `router` | Broad or unresolved intent and the point where responsibility passes to a leaf Skill. |

For a gate, state the assessed state, decision or evidence returned, and the
no-remediation boundary when assessment could be confused with repair.

Add a hard prerequisite only when no compliant path exists without it. Put it in
the description only when it controls selection of the whole Skill. Keep
operation-specific authorization and state checks in the body.

Add the nearest-sibling boundary only when two written descriptions can select
the same observable request. Prefer a positive responsibility split over an
open-ended exclusion list. Omit a boundary whose removal changes no expected
selection.

Use terms users express in requests. Mention a tool, format, product, protocol,
or execution surface only when it changes selection. Keep detailed steps,
output schemas, completion branches, and validation procedures in the body
unless they determine eligibility. Avoid promotional quality claims and keyword
lists. Do not repeat the same meaning in multiple languages solely to add
triggers.

## Validate Selection

Build cases for every distinct selection edge:

1. **Should trigger**: direct and indirect requests needing the Skill.
2. **Should not trigger**: requests sharing vocabulary but belonging to a
   sibling or unrelated Skill.
3. **Ambiguous**: requests matching multiple Skills, with an expected single
   target, clarification, ordered pair, or intentional co-use.

These are written selection cases, not evidence of actual model selection. To
claim observed selection, evaluate independently without naming the target Skill
or exposing the intended answer.

Delete or shorten a description phrase and rerun the cases. Keep it only when
removal creates a missed trigger, false trigger, incorrect order, or unresolved
sibling ambiguity. Call a phrase causally necessary only after repeated
comparisons hold cases, model, host, surrounding instructions, and environment
constant while changing only that phrase.

When the selection surface may shorten metadata, verify that the opening still
identifies responsibility and applicability before optional detail is lost.
