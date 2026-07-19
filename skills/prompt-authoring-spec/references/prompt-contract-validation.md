# Prompt Contract Validation

Use this reference when reviewing model-visible instructions, deriving
counterexamples, or deciding what evidence a quality or behavior claim requires.

In read-only mode, report a required text change as a finding and proposed
correction without modifying the reviewed text.

## Review the Text as a Closed Contract

Review using only the context available to the intended executor. Do not repair
omissions from author intent or general model knowledge.

| Check | Defect exists when |
| --- | --- |
| Removal | Deleting the text changes no behavior, interpretation, or evidence requirement. |
| Actor and action | The responsible actor or required action cannot be identified directly. |
| Strength | Two reasonable readers can disagree whether a rule is required, preferred, or optional. |
| Scope | The condition, target, stopping point, or exception has more than one consequential interpretation. |
| Terminology | One concept has multiple names, one name has multiple meanings, or a label has no clear target. |
| Structure | Formatting implies a false order, grouping, priority, or equivalence. |
| Conflict | Applicable instructions cannot all be satisfied and no precedence resolves them. |
| Dependency | A required input, capability, authority, or context item is absent and unhandled. |
| Decision coverage | A source requirement or reachable dependency or failure state never became an authoring decision. |
| Branch coverage | A set, quantitative bound, branch, or default has an open or ambiguous edge that changes compliance. |
| Authority | Data can be mistaken for governing instructions, or untrusted content is placed at higher authority. |
| Placeholder | A governing rule depends on an unresolved value, assumption, or reference with no behavior until resolution. |
| Layer | The prompt claims to enforce behavior owned by a schema, host, policy, or runtime. |
| Evidence | A completion or quality claim is stronger than the obtainable evidence. |
| Example | An example contradicts the rule or supplies the only statement of required behavior. |
| Traceability | A requirement or authoring decision appears only in analysis, rationale, or review notes and is absent from the text the executor receives. |

Find a request within the prompt's declared scope and a reachable state that exposes each suspected defect. One
concrete counterexample requires revision. Finding none proves only that no
textual contract defect was identified in the reviewed scope.

When source requirements or confirmed authoring decisions are available, compare
the final instruction with the available material. If neither is available,
continue the closed-contract review and mark source traceability unverified; do
not invent the missing material. Remove a decision that is not required, or
express it in the text the executor receives; analysis and review notes do not
govern runtime behavior.

For every required input, capability, authority, or instructed action, test each
reachable missing, invalid, conflicting, unavailable, denied, and post-start
failure state that would change the result. Treat objects named by actions such
as `read`, `inspect`, `compare`, or `transform` as candidate inputs. Do not
assume a state away without a supplied value or explicit host guarantee.

For every list that governs behavior, decide whether it is exhaustive or illustrative and
mark it when the difference changes the executor's choices. For every judgment
qualifier, hold the facts constant and test whether two opposite choices still
comply; if they do, replace the qualifier with its deciding condition.

For each finding, identify the exact text or omission, the behavior it permits,
the impact in the supported execution path, the correction that closes the defect without changing
unrelated behavior, and the evidence level.
Do not judge meaning from keyword presence or combine unrelated
concerns into an uncalibrated score.

## Match Validation Claims to Evidence

Choose the minimum evidence that directly supports each claim. The table is an
evidence map, not a quality score or a mandatory sequence; combine rows when a
claim has separate parts:

| Evidence | Supported conclusion |
| --- | --- |
| Text review | The visible instruction has no identified ambiguity, contradiction, or responsibility defect for the inspected scope. |
| Source review | Source-dependent rules and claims trace to evidence whose authority, scope, and freshness were inspected. |
| Scenario walkthrough | An ideal executor can derive a coherent decision for the stated cases. |
| Independent model evaluation | The named model and host exhibited the observed behavior on the tested cases. |
| Runtime validation | The named tools, schemas, permissions, side effects, and integrations behaved as observed in the tested environment. |

Keep expected behavior hidden from an independent model evaluation unless the
target prompt legitimately supplies it. Freeze cases and observable success
criteria before inspecting outputs. Before claiming that a phrase causally
improves behavior, repeat the same cases with and without that phrase while
keeping the model, host, surrounding instructions, and environment unchanged.
Before inspecting those outputs, define in the evaluation fixture how many runs
will be compared and what observed result will count as improvement. If the
fixture omits that rule or the observed result does not meet it, report only the
observed difference and do not claim causal improvement.

A prompt that cannot run can still receive a valid text review. Report that
limited conclusion instead of calling it operationally validated or treating
the absence of runtime evidence as a textual defect.
