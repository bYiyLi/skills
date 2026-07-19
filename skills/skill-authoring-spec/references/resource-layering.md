# Resource Layering

Use this reference when deciding where Skill content belongs or when auditing an existing Skill's resource set.

The labels `SKILL.md`, `references/`, `scripts/`, and `assets/` below name semantic roles used by formats that support those paths. Inspect the native Skill format before applying a path or layout requirement. For another format, map each role to its native instruction and resource surfaces; if the format cannot be inspected, assess role and necessity while leaving path and layout conclusions unverified.

## Contents

- [Decide Whether the Content Should Exist](#decide-whether-the-content-should-exist)
- [Keep Always-Needed Behavior in SKILL.md](#keep-always-needed-behavior-in-skillmd)
- [Use References for Conditional Knowledge](#use-references-for-conditional-knowledge)
- [Use Scripts for Deterministic Execution](#use-scripts-for-deterministic-execution)
- [Use Assets as Output Material](#use-assets-as-output-material)
- [Account for the Primary Type](#account-for-the-primary-type)
- [Route Resources Conditionally](#route-resources-conditionally)
- [Validate the Resource Set](#validate-the-resource-set)

## Decide Whether the Content Should Exist

Evaluate each proposed file or block in this order:

1. Verify that source-dependent mandatory rules and domain claims are grounded in applicable project sources, authoritative documentation or policy, representative artifacts or task traces, failure records, or explicit user decisions. A user decision establishes policy only within that user's authority and the stated task scope; an artifact or trace proves only observed behavior; external format, host, and runtime guarantees require a source or runtime evidence with matching authority and scope.
2. Name the concrete task failure the content's absence would cause. Omit it when no supported invocation would fail without it.
3. Put core behavioral instructions in `SKILL.md` when every supported invocation needs them before choosing an operation or branch.
4. Put agent-readable knowledge or detail in `references/` when it is conditional, or when keeping it in `SKILL.md` would obscure the core decisions and routing. If every path needs a large reference, route to it unconditionally and explain why the body cannot carry the content directly.
5. Put it in `scripts/` when the agent should execute stable logic instead of reconstructing an error-prone or repeated implementation.
6. Put it in `assets/` when the file becomes part of an output through copying, filling, transforming, packaging, or embedding.
7. Split mixed content by runtime role instead of choosing a directory by its current extension or source location.

Classify by runtime consumer rather than extension. A JSON schema read by the agent is a reference; JSON copied into a generated project is an asset; JSON used only by a bundled script belongs with that implementation.

Treat product interface metadata and runtime policy as native integration
material, not as bundled Skill resources. Do not use them as the only location
for post-trigger rules the executor must follow.

Do not create placeholder files, empty resource directories, speculative variants, research history, or standalone guides, quick references, and changelogs with no declared runtime role. Put installation instructions in a reference when a supported path requires them; otherwise omit them. Add a resource only for a current responsibility and a demonstrated use path.

## Keep Always-Needed Behavior in SKILL.md

Keep the smallest set of post-trigger instructions needed to preserve responsibility and route the current task:

- operation or branch selection rules used on most invocations;
- shared invariants, priorities, authorization boundaries, and stopping rules;
- conditions and exact paths for bundled resources;
- completion or handoff evidence that prevents false success.

Do not turn the body into a domain encyclopedia, duplicate detailed references, or hide initial trigger conditions there. If a body section applies only after one optional branch is selected, prefer a direct conditional reference.

## Use References for Conditional Knowledge

Use `references/` for material the agent must read and reason about but that does not belong in the core body. Most references are conditional, such as:

- detailed policies, protocols, schemas, and domain rules;
- provider-, framework-, format-, or operation-specific instructions;
- large examples that resolve non-obvious decisions;
- volatile facts whose source, version, or freshness must be checked at execution time.

A large authoritative source may be required on every path. In that case, keep
only its unconditional route and the decisions needed before loading it in
`SKILL.md`; do not copy the source into the body merely to avoid a reference.

Give each reference one coherent subject. State authority, scope, version, or freshness where confusion would change a decision. If live retrieval is required, define the authoritative source and the behavior when retrieval fails; do not present stale embedded knowledge as current.

Bundling a document does not make its claims authoritative. Inspect the source before deriving mandatory instructions, resolve material conflicts, and preserve uncertainty when the available evidence does not support one rule.

Keep the reference reachable by an exact path from `SKILL.md`. Avoid chains in which one reference must be discovered through another. Do not repeat the same rule in the body and reference; keep the decision or routing rule in the body and the conditional detail in the reference.

## Use Scripts for Deterministic Execution

Use `scripts/` when execution benefits from determinism, repeatability, or a tested implementation, including:

- structured parsing, conversion, validation, or normalization;
- fragile transformations with stable inputs and outputs;
- logic that would otherwise be rewritten in multiple tasks;
- checks whose result must be machine-verifiable.

Define the script's inputs, outputs, exit behavior, side effects, and behavior when it fails. Keep policy and judgment in the body or a reference unless the script is itself the authoritative executable policy. Do not hide permissions, destructive behavior, network writes, or fallback decisions inside an unexplained script.

Do not add a script when one stable existing command performs the same task without repeated logic. Add one only when repeated rewriting, a demonstrated implementation failure, a stable executable interface, or a machine-verifiable result gives it a concrete role. When that evidence is absent or equally supports a script and omission, choose `Omit`. Test each implementation whose inputs, outputs, side effects, or failure behavior differ. When several scripts share those properties, test one sample for each distinct behavior and identify the scripts that were not run. Verify the produced artifact or state, not only exit code zero.

If the required runtime is unavailable, keep the script's declared interface explicit but report runtime correctness as unverified. Do not infer executable behavior from the surrounding prompt.

Keep machine-readable support data used only by a script with that implementation. Do not ask the agent to load it separately unless the agent must reason about it.

## Use Assets as Output Material

Use `assets/` for files consumed as part of the result rather than as instructions, such as:

- document, code, or project templates;
- icons, images, fonts, themes, and media;
- boilerplate copied into a generated output;
- sample artifacts transformed into the requested deliverable.

Place output templates under `assets/` rather than inventing a separate top-level `templates/` contract. Keep instructions, policies, and decision rules out of assets. If the agent must read a template to understand a rule, move that rule into the body or a reference.

State how the asset is selected and used, whether it may be modified, and which output properties must be preserved. To claim runtime usability, verify that the asset exists, opens in its intended consumer, and produces a result that meets those documented output properties through the documented path. If the intended consumer is unavailable, report that claim as unverified.

## Account for the Primary Type

Type changes likely resource boundaries but never determines a directory by itself:

| Type | Common resource pressure | Boundary to preserve |
| --- | --- | --- |
| `capability` | Operation-specific references and scripts | Load or execute resources only for requested independently invocable operations. |
| `workflow` | Fragile step scripts, provider variants, and output templates | Resources support one owned result and do not extend the stopping point. |
| `guidance` | Detailed standards, policies, schemas, and examples | References supply rules to the host task; scripts must not silently take over the host result. |
| `router` | Large or changing downstream maps | Keep routing criteria visible; do not copy downstream procedures or package leaf resources. |

Routing among files inside the same Skill does not change its primary type. Responsibility still depends on who owns the final result.

## Route Resources Conditionally

Prefer a direct condition, exact path, and concrete action. The paths and file
names in the examples below are illustrative; they are not files required by
this Skill.

An unconditional route is valid when every declared invocation needs the resource. If every resource is required on that path, load all of them; do not infer that requirement from directory membership alone.

Positive reference route:

```text
For tracked-change editing, read references/redlining.md before modifying the
document. Do not load it for plain text extraction.
```

Negative reference route:

```text
Read every file in references/ before starting because it is in that directory.
```

Positive script route:

```text
For structural validation, run scripts/validate_document.py against the output.
Treat a nonzero exit as a blocker and return the reported violations.
```

Negative script route:

```text
Use the scripts when useful.
```

Positive asset route:

```text
For a project status report, copy assets/status-report.md.tmpl and replace every
declared placeholder; verify that no placeholder remains in the output.
```

The negative routes either waste context or leave resource selection and failure behavior unresolved.

## Validate the Resource Set

Validate the resource set at these Skill-specific levels:

1. **Contract integrity**: Verify exact paths and casing, a real routing condition for every resource, no unreferenced files, and no duplicated or contradictory rules across the body and references. If a resource required by the selected path is missing, unreadable, or case-mismatched, report a blocker for that path and do not claim the contract is complete.
2. **Content validity**: Parse structured references; verify the grounding, authority, scope, version, and freshness of non-obvious claims where they change decisions; and inspect declared script or asset interfaces for inputs, outputs, side effects, and failure behavior.
3. **Observed use**: When claiming that an agent loads or avoids a resource correctly, obtain model-evaluation output or trace evidence. A path and routing sentence alone prove only the intended route.
4. **Runtime correctness**: Run scripts on representative success and failure cases and inspect the produced artifact or state. Open, render, or consume assets through their documented path. Mark unavailable runtime checks as unverified.

For necessity, distinguish removing the resource route from the written contract
from comparing model behavior with and without that route. A resource is
textually necessary when removing its route loses a required decision, fact, or
output material; claim causal behavior improvement only after a controlled model
evaluation compares the same cases with and without the route.

Verify that scripts and assets do not broaden side effects beyond the declared responsibility. Test failure paths without writing to live or production systems unless the user explicitly authorizes that scope.

Do not use frontmatter validation, file existence, a large resource count, or the author's description of expected behavior as evidence of runtime quality. Report each conclusion at the strongest evidence level actually obtained.
