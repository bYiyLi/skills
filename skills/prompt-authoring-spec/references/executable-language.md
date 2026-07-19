# Executable Language

Use this reference when authoring or reviewing sentence construction,
terminology, requirement strength, prohibitions, sets, quantitative bounds,
branches, or prompt structure.

## Use Direct Sentences

- Use active voice and direct verbs. Prefer `Inspect the repository` over `The
  repository should be inspected`.
- Make the actor, action, and object recoverable from each instruction.
- Put one primary rule or decision in each sentence or list item.
- Keep a condition next to the action it controls. Put it first when that lets
  the executor skip an irrelevant rule.
- Put prerequisites, authorization checks, and warnings before the action they
  gate. Define the result when a failed check changes the outcome.
- Use present tense unless another tense is required for accuracy.

## Use Stable Terms

- Prefer common, short words and concrete verbs over formal, promotional, or
  abstract alternatives.
- Use one term for one concept. Do not vary terminology for style.
- Define a technical term or abbreviation at first use when its meaning is not
  already available in prompt context.
- Replace noun strings and noun forms that hide actions with direct verbs.
- Replace a pronoun when it can refer to more than one nearby subject.
- Identify each target with a stable label, identifier, or selection criterion
  available to the executor.

## Express Requirement Strength

Use four requirement levels. The English tokens are optional; preserve their
meaning in the artifact's language.

| Level | Meaning |
| --- | --- |
| `must` | Required within the stated scope; every allowed exception is explicit. |
| `must not` | Prohibited within the stated scope; every allowed exception is explicit. |
| `should` | The default; deviation requires a stated reason. |
| `may` | Optional; either choice remains compliant. |

An imperative is a requirement within its stated scope. Use `must` or `must not`
when an imperative could be mistaken for preference or description.

- Do not use hard requirement terms for preferences or methods whose
  alternatives are equally valid.
- Do not weaken a requirement with `try to`, `if possible`, `ideally`,
  `generally`, or `where appropriate`.
- When judgment is intentional, state the deciding criterion.
- Replace quality adjectives such as `excellent`, `careful`, `deep`,
  `professional`, `robust`, `safe`, or `best` with observable behavior,
  evidence, or acceptance criteria.
- Replace a qualifier such as `recent`, `fast`, `minimal`, `relevant`, or
  `appropriate` when two executors can choose opposite actions from the same
  facts and both comply.
- Do not define a decision with the same undecided word or a vague synonym.

## Handle Prohibitions and Exceptions

- Prefer the required action when it fully defines the desired behavior.
- Use a prohibition when the forbidden behavior is itself a material boundary.
- Pair a prohibition with the valid alternative when the executor still needs
  to choose an action.
- Rewrite double negatives and nested exceptions as a positive condition and
  result.
- State the base rule before its exception and keep them adjacent.
- An exception must apply to fewer states than its base rule. If it applies
  whenever the base rule applies, replace the base rule with the exception's
  behavior.

Prefer:

```text
Report the result, supporting evidence, and unresolved limitations.
```

Avoid:

```text
Do not be unnecessarily verbose.
```

Keep a hard boundary explicit:

```text
Do not report a check as passed unless it ran successfully.
```

## Close Sets, Bounds, and Branches

- Mark a governing list as exhaustive or illustrative when that distinction
  changes choices.
- Do not use `etc.`, `and so on`, `and/or`, or `including but not limited to` in
  a governing rule. Name the set, give a discovery rule, or state the criterion
  preserving judgment.
- Attach `all`, `any`, and `only` to an identifiable set. If the set must be
  discovered, state its source or stopping condition.
- When a numeric limit affects compliance, state the unit, counting basis,
  boundary direction, and endpoint inclusion.
- Define what happens when conditional branches overlap or none match whenever
  those states are reachable and change the result.
- Do not leave a governing `TODO`, `TBD`, placeholder, or assumption unresolved.
  Identify the missing fact, its source, who resolves it, and behavior until
  resolution.

Prefer:

```text
Return at most five findings in source order. If no actionable finding exists,
state that none was identified.
```

Avoid:

```text
Return a few important findings, recommendations, etc.
```

## Structure Only for Meaning

- Add structure only when it separates roles the executor could confuse.
- Use headings or consistent delimiters to distinguish instructions, source
  material, variable input, examples, or output contracts.
- Put a rule before its rationale or example. Keep rationale only when it changes
  interpretation or decision-making.
- Use numbered steps only when order or completeness matters. Use bullets for
  unordered peer rules and prose for a single rule.
- Keep parallel list items grammatically parallel.
- State a rule once within each model-visible instruction unit. Treat a unit as
  independent when the host can deliver or update it separately and the model
  may interpret it without other units. Repeat a rule in another unit only when
  that unit must independently preserve the same boundary.
- Use descriptive headings rather than containers such as `Overview`, `Notes`,
  `Details`, or `Miscellaneous` when the heading must aid navigation.

Delete language that adds tone or ceremony without changing behavior, including
flattering roles, prestige claims, hype, motivational language, courtesy
padding, figurative slogans, emotional intensifiers, and filler such as `use
best practices`. Keep tone or emphasis only when it changes the required output
or a real decision.
