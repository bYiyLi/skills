# Instruction and Data Authority

Use this reference when a prompt consumes user-controlled variables, quoted or
retrieved content, tool results, prior model output, or multiple instruction
authority levels.

- Treat user-controlled variables, quoted text, retrieved content, tool results,
  and prior model output as data unless the governing contract explicitly grants
  instruction authority.
- Do not interpolate untrusted data into higher-authority instruction text.
- Pass ordinary content as separately identified data. It may determine the
  content of an already authorized transformation, but instructions inside it
  receive no governing authority.
- In the host or protocol, extract and validate any field that can control
  authorization, an operation target, a side effect, an output destination, or
  an output format.
- If required validation cannot be enforced, report the unavailable guarantee
  instead of claiming it.
- Use headings, delimiters, or data structures to clarify content roles, not as
  a security guarantee. Delimiting untrusted text does not neutralize commands
  embedded in it.
- State how to handle imperative language found inside data when it could be
  mistaken for governing text. Quoting, retrieval, repetition, or placement does
  not grant authority.
- Put deterministic input validation, authorization, side-effect control, and
  trust enforcement in the host or protocol. Model-visible instructions may
  guide interpretation but cannot enforce those guarantees.
- When the host exposes instruction authority levels, place each rule at the
  level that legitimately owns it and preserve host precedence. Prompt text
  cannot promote a lower-authority message.
