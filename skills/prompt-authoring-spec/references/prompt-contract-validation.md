# Prompt Contract Validation

Use for reviewing or delivering instructions, self-review and behavior claims.

## Check the text that will govern execution

Review the actual prompt and context the executor receives, including independent
invocation prompts and generated instructions. Compare them with the task and
applicable sources. Do not complete the contract from author intent or review notes.

Check necessity and ownership before correcting wording. Then check:

| Question | Find |
| --- | --- |
| Does each requirement have a basis here? | Misplaced rules, guessed causes, accidental example requirements or scope expansion. |
| Can the executor choose and act? | Unidentifiable conditions, missing inputs/tools, ambiguous actors, targets, strength, sets or bounds. |
| Do all required paths remain valid? | Conflicting priorities, promoted data, missing results, exceptions, recovery or completion evidence. |
| Can any text be removed without loss? | Duplicate rules, unused context, explanatory padding or unnecessary procedure. |

For a behavioral finding, show a reachable request/state and the wrong action
allowed or valid action blocked. For a density finding, identify the redundant
text and a shorter equivalent that preserves meaning. A style preference or two
intentionally valid choices are not defects. Keep required details, including
those supplied by context; do not invent a missing-input error when the input exists.

Check reachable missing, invalid, conflicting, denied and interrupted dependencies.
For side effects, distinguish known failure from unknown outcome before specifying
retries. Pair a demonstrated failure with a nearby valid case; a fix must close
the former without prohibiting the latter. Validate the result after trimming,
not merely the longer draft it came from.

Report findings with location, consequence, minimum correction and evidence level.
With none, state scope and unverified claims. Review-only ends with that report.
For authorized revision, fix supported defects and recheck affected decisions;
finish when required checks pass and no actionable finding remains. Preserve
unresolved blockers rather than weakening acceptance or iterating for its own sake.

## Apply the same standard to this Skill

Review every model-facing file: description, entrypoint, routed references and
invocation text. Give this specification no exemption. Judge a questioned rule
against the user's requirements and a concrete defect, not against the rule's
own claim to correctness. Correct the rule or its application within authorization;
do not waive a violated rule merely to pass the draft. Self-review checks the
package; it does not recursively require reviewing the review forever.

## Distinguish validation from claims of improvement

| Evidence | Supported conclusion |
| --- | --- |
| Text/source review | Identified contract corrections and claims grounded in inspected sources. |
| Scenario walkthrough | Coherent decisions for the stated cases. |
| Independent model run | Observed behavior of the named model and host on those inputs. |
| Runtime test | Observed behavior of the tested tools and integrations. |

Use text and source review for textual conclusions. Run independent model cases
when the task requires behavior verification or a claim depends on observed
behavior, and execution is available and authorized. Preserve text-only scope;
unavailable execution limits behavior claims, not the supported text result.
Give the executing model raw tasks and necessary inputs, not expected answers
or the author's findings. Freeze cases and acceptance before seeing results.
Select cases for the requested claim; for a rule correction, include nearby valid
behavior within the authorized test scope. Report a single-case check as such.

For causal behavioral claims, hold cases, model, host and surrounding context
constant while varying the claimed change. Define the comparison, repetitions
and success criterion before observing outputs; match repetitions to variability
and the claim's scope. Retain failures. One successful case does not establish
general improvement, and a whole revision does not isolate one phrase's effect.
Fewer words or self-consistency proves no behavioral gain. Repeat checks only for
changes, failures, unresolved findings or the agreed evaluation protocol.
