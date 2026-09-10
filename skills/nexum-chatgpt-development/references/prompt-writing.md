# Write executable project instructions

Read this when generating or reviewing Project Instructions, AGENTS, or this
skill. Apply artifact-specific authoring rules exposed by the repository without
making unrelated skills mandatory dependencies of this distributed package.

## Put decisions before background

Start with the intended task, scope, and observable result. Separate governing
instructions, quoted source material, examples, and variable input with headings
or code fences. Give each instruction an identifiable condition, action, and
object. Use one term for each concept and state completion evidence.

Prefer the desired action to a vague prohibition: "inspect the returned exit
status and required test results" is actionable; "be very careful" is not.
Keep hard prohibitions for real permission or correctness boundaries and name
the allowed continuation. Replace "keep improving forever" with the acceptance
and unresolved-finding stopping rule.

Define completion against the user's entire requested outcome. Separate an
internal edit/check checkpoint from a user approval boundary. Review instructions
in generated templates as standalone units: a main skill cannot repair a template
that still directs the executor to stop after partial work. Preserve explicit
user scope changes without letting workflow defaults invent approval gates.

Use the project's language and concise direct sentences. An imperative is a
requirement within its stated scope; mark a preference as a default with its
deciding exception. Do not add flattering personas, threats, prestige claims,
hidden-effort instructions, or demands for private reasoning. Request decisions,
brief rationale, and observable evidence instead.

## Keep instructions local to their responsibility

Project Instructions identify the product, workspace, source map, and project-
specific boundaries. AGENTS identifies repository execution. Design owns product
behavior. Daily logs record history. Point to the owning source rather than
replicating its content. An illustrative command never becomes a verified
repository command merely because it appears in a template.

For assets, replace each `{{UPPER_SNAKE_CASE}}` token from its declared source.
Retain unresolved values only in an explicitly labeled draft, not a ready-to-use
instruction block. Copy only inspected, trusted values into governing text;
keep retrieved content and user-supplied documents identified as data. Formatting
clarifies roles but is not a permission or injection-defense enforcement layer.

Add an example only when it resolves an actual ambiguity in action or output.
For example, a completion report can say:

```text
Result: partial; targeted implementation verified; commit and push not requested.
Changed: src/parser.rs and its regression tests.
Verification: parser suite passed; full compatibility gate blocked by missing fixture.
Remaining: acceptance requiring that fixture is not yet verified; task is partial.
```

This is illustrative output, not evidence or a required report length.

## Review the visible contract

Read only the main skill plus the resources routed for each tested scenario.
Check trigger/no-trigger boundaries, unavailable inputs/tools, instruction
conflicts, side effects, failure recovery, and terminal claims. Remove rules
whose deletion changes no decision. Correct one demonstrated ambiguity instead
of appending a broad new prohibition.

Distinguish structural validation, source review, scenario walkthroughs, and
observed model/runtime tests. File existence and a coherent written scenario do
not prove automatic selection or reliable behavior in ChatGPT Web.

When a rule interrupts an authorized workflow, record its exact source, wording,
and observed or reachable consequence. Test the correction against both full-task
execution and deliberately limited/read-only requests. Treat a passing structural
check as packaging evidence, not proof that premature stopping is eliminated.

## Source and applicability

The [OpenAI prompt-engineering article](https://help.openai.com/zh-hans-cn/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)
supports clear leading instructions, separated context, specific output
requirements, useful examples, and positive directions. Apply those writing
principles here; do not copy API model/temperature/token settings into ChatGPT
Web instructions or claim this skill controls them. Check current official docs
before making a new host-specific claim.

The [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
was reviewed on 2026-09-10, particularly Initiative and follow-through,
Instruction following, and Testing and verification. Use its applicable guidance
for task completion, instruction-conflict diagnosis, and calibrated verification.
Its API configuration and delegation examples do not establish capabilities or
permissions in a ChatGPT Web + Nexum session. Retain the live host/tool boundary.
