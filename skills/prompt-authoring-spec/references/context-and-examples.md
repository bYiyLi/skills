# Context and Examples

Use this reference when the target prompt includes or needs source context,
history, examples, placeholders, variable input, or illustrative data.

## Select Context by Decision Value

- Include a context item only when it can change the intended selection,
  interpretation, judgment, action, evidence, or output.
- Provide the actual fact, source, or constraint instead of referring to
  unidentified `relevant context`.
- Preserve source scope, version, freshness, or uncertainty when it changes a
  future decision.
- Keep governing instructions separate from source material and variable data.

## Add Examples Only for a Decision Edge

- Add an example only when it resolves an ambiguity, boundary, or output pattern
  that changes the executor's choice and the rule alone does not resolve it.
- Start without examples and add them in response to a concrete need, not a
  fixed quota.
- Keep every example consistent with its governing rule.
- Vary only details the rule leaves unconstrained. Do not let accidental details
  become unstated rules.
- Use consistent formatting across examples so formatting noise does not imply
  a behavioral distinction.

## Mark Placeholders and Example Data

- Give each runtime placeholder distinctive syntax. Define its source, type, and
  meaning when the surrounding contract does not already do so.
- Keep placeholders visibly separate from literal examples.
- Use synthetic, reserved, or redacted data in illustrative examples.
- Omit secrets and personal or proprietary data that does not change the
  example's decision. Use real values only when required, authorized, and
  explicitly marked as data.
