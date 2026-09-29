# Evidence and Enforcement

Use for source-dependent claims, causal reasoning or runtime guarantees.

## Identify what the evidence establishes

Use applicable requirements and authorized decisions to establish project policy.
Ground external capabilities and guarantees in primary documentation or observed
runtime evidence; deciding to use a tool does not prove it exists. Qualify claims
whose evidence is unavailable. Check authority, scope and freshness when they
affect the decision. Resolve conflicts by precedence or leave them explicit.

A requirement can define a desired result without a prior failure. An observation
shows what happened, not necessarily why. To justify a corrective rule, trace the
proposed restriction to the failure mechanism it addresses and check whether it
belongs in this prompt. Keep unsupported causes provisional; do not invent facts,
permissions or capabilities to complete the explanation. A counterexample can
prove a textual gap without measuring its frequency in model behavior.

Public prompts and analogies provide candidates, not authority for local policy
or evidence that a technique works on the target model. This specification's own
rules are likewise policies to assess, not evidence that they are effective.

## Match guarantees to their enforcing layer

| Layer | Can establish |
| --- | --- |
| Model instructions | Requested decisions and reporting behavior, not guaranteed compliance. |
| Schema or protocol | Validated fields, types and structure. |
| Host controls | Enforced permissions, side effects, secrets and deterministic limits. |
| Runtime or tool results | Observed state and execution outcomes. |
| Evaluation | Recorded behavior under specified inputs and conditions. |

Keep model-visible boundaries the executor needs before acting, even when another
layer enforces them. Do not claim wording provides a machine guarantee or implement
host changes merely because the task asks for instructions.

Inspect model or host details only when they change instruction priority, visible
context, syntax, capabilities or a claimed guarantee. Assess the executor's access
at the decision point, not the author's access during development. Report missing
capabilities and limit dependent claims; availability never supplies permission.
