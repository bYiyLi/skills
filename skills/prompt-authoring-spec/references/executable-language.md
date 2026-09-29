# Executable Language

Use for the expression of rules that belong in the target prompt.

## Make choices unambiguous

Make the actor, action and target clear from the sentence and available context.
Keep a condition next to its action and a prerequisite before the action it gates.
Split combined decisions only when combining them obscures who does what or when.

Use one term per concept and stable target names. Define unfamiliar terms only
when the executor needs them. For a qualifier that controls compliance, give a
criterion the executor can identify; replacing “important” with “significant”
does not resolve the decision. Different choices are allowed when the task leaves
them open. Request observable results or checks, not hidden effort or certainty.

## Preserve requirement strength

Use these meanings in the target language; no particular English token is required.

| Expression | Meaning |
| --- | --- |
| Imperative / must | Required within its scope. |
| Must not | Prohibited within its scope. |
| Should | Preferred default; deviations remain allowed. |
| May | Optional; either choice complies. |

State departure criteria when the task needs them constrained. Do not promote
preferences into requirements or weaken requirements with “try to.”
Keep a base rule and its exceptions together. If an exception applies everywhere
the base applies, replace the base with the intended behavior.

## Close boundaries without inventing policy

Keep a prohibition explicit when the forbidden action itself matters. An
alternative is optional unless the task needs one; any supplied alternative must
be identifiable and available, or its absence handled. Avoid nested negatives.

Give “all,” “any” and “only” an identifiable set or a discovery rule. Mark lists
as exhaustive or illustrative when it changes compliance. Specify numeric units,
counting rules and endpoints when not evident; do not invent thresholds for a
qualitative goal. Handle consequential branch overlaps and no-match states.
Resolve conflicts through applicable precedence or report the unresolved choice.
A ready-to-use prompt cannot rely on an unresolved governing placeholder; a draft
may mark the missing source and behavior pending resolution.

## Use structure to expose decisions

Separate instructions, source data, examples and output requirements where they
could be confused. Use numbered steps when their order or completeness matters;
do not let a heading or checkpoint invent priority, approval or a deliverable.

State each rule once within text read together. Repeat a boundary in separately
delivered text only when that text must preserve it independently. Prefer a
conditional pointer to lengthy specialized guidance when the executor can access
it; keep what must be known before following the pointer in the current text.
