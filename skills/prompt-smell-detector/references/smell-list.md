# Prompt / Skill Bad Smell Taxonomy

Use this taxonomy to diagnose prompts, system prompts, agent instructions, workflow prompts, `SKILL.md` files, and ChatGPT Skills.

## Table of Contents

1. One-vote rejection smells
2. Trigger and scope smells
3. Workflow and execution smells
4. Output and validation smells
5. Safety and authority smells
6. Context and maintainability smells
7. Iteration and ownership smells

## 1. One-vote Rejection Smells

These usually prevent approval even if the artifact has good sections.

### 1.1 Unclear Trigger

**Symptoms:** The artifact says "use when user needs help", "for writing", "for analysis", or equivalent broad language.

**Impact:** The agent cannot reliably decide when to invoke or follow it.

**Fix:** State exact trigger cases, non-trigger cases, expected inputs, and expected outputs.

### 1.2 No Executable Workflow

**Symptoms:** It contains principles but no steps, decision tree, entry/exit conditions, or operational procedure.

**Impact:** Different agents execute different invisible workflows.

**Fix:** Add numbered steps with decision points and completion criteria.

### 1.3 No Output Contract

**Symptoms:** It asks for "analysis", "optimized result", or "suggestions" without fixed sections or fields.

**Impact:** The result cannot be verified or consumed downstream.

**Fix:** Define required output sections, fields, examples, or schema.

### 1.4 No Failure Handling

**Symptoms:** It does not say what to do when inputs are missing, tools fail, references are absent, or validation fails.

**Impact:** The agent guesses, stalls, or gives up.

**Fix:** Add missing-input, fallback, partial-result, and revision behavior.

### 1.5 Unsafe Autonomy

**Symptoms:** It allows automatic sending, publishing, deleting, deploying, modifying production data, or external side effects without explicit approval.

**Impact:** The artifact can cause real-world harm or violate user control.

**Fix:** Add read/write/destructive action gates and confirmation requirements.

### 1.6 Fake Validation

**Symptoms:** It says tests passed, validation completed, or quality is assured without naming the checks actually performed.

**Impact:** It creates false trust and hides defects.

**Fix:** Require validation logs: what ran, what passed, what failed, what was not checked.

## 2. Trigger and Scope Smells

### 2.1 Universal Assistant Smell

**Symptoms:** "You are a helpful assistant", "help with any task", "do whatever the user asks".

**Impact:** Not a reusable task-specific instruction.

**Fix:** Narrow to a repeated task with clear success criteria.

### 2.2 Missing Non-goals

**Symptoms:** It lists capabilities but never says what it should not do.

**Impact:** Over-triggering, scope creep, and unsafe behavior.

**Fix:** Add non-goals and handoff conditions.

### 2.3 Ambiguous Audience or User

**Symptoms:** It does not define who the output is for or what level of expertise to assume.

**Impact:** Tone, depth, and format drift.

**Fix:** Define target user, decision maker, or consumer.

### 2.4 Hidden Assumptions

**Symptoms:** It depends on unstated tools, files, access, policies, or domain conventions.

**Impact:** Works only in the original author's environment.

**Fix:** List assumptions and required dependencies.

## 3. Workflow and Execution Smells

### 3.1 Principle Pile

**Symptoms:** "Be accurate", "be professional", "be comprehensive", "think carefully" without operationalization.

**Impact:** Tone improves, reliability does not.

**Fix:** Translate each principle into observable behavior.

### 3.2 Missing Branches

**Symptoms:** Same flow for simple, complex, ambiguous, high-risk, and unsupported tasks.

**Impact:** Over-processing simple tasks and under-protecting risky tasks.

**Fix:** Add mode selection and decision branches.

### 3.3 Tool Vagueness

**Symptoms:** "Use tools as needed" or "search when necessary" without must-use and must-not-use rules.

**Impact:** Inconsistent evidence collection and side effects.

**Fix:** Define tool triggers, permission gates, fallback behavior, and citation/verification requirements.

### 3.4 Over-clarification Trap

**Symptoms:** It always asks questions before acting, even when reasonable assumptions would enable useful progress.

**Impact:** Slow, dependent, low-ownership behavior.

**Fix:** Ask only decision-changing questions; otherwise proceed with explicit assumptions.

### 3.5 Premature Finalization

**Symptoms:** It jumps directly to final output without inspection, testing, or review.

**Impact:** Fast but brittle outputs.

**Fix:** Add inspection, validation, and self-check steps.

## 4. Output and Validation Smells

### 4.1 No Acceptance Criteria

**Symptoms:** It never defines what counts as done or good enough.

**Impact:** Cannot evaluate quality objectively.

**Fix:** Add release gates, rubric, examples, or tests.

### 4.2 Advice Without Patch

**Symptoms:** It gives broad suggestions but no concrete edit, rewrite, or next action.

**Impact:** User must do the real repair work.

**Fix:** Include exact replacement text or prioritized patch plan when asked to improve.

### 4.3 Evidence-free Diagnosis

**Symptoms:** Findings lack quotes, line references, or concrete sections.

**Impact:** The review feels subjective and cannot be audited.

**Fix:** Add evidence for every issue.

### 4.4 No Bad-case Testing

**Symptoms:** Only happy paths exist.

**Impact:** The prompt fails under ambiguity, adversarial input, or missing context.

**Fix:** Add happy path, bad input, ambiguous input, unsafe request, and regression cases.

## 5. Safety and Authority Smells

### 5.1 Missing Permission Boundary

**Symptoms:** No distinction between read-only, write, destructive, external-send, or irreversible actions.

**Impact:** The agent may act beyond user intent.

**Fix:** Add permission ladder and explicit confirmation rules.

### 5.2 Confidence Theater

**Symptoms:** "Never say you cannot", "always be confident", "act as the world's top expert".

**Impact:** Increases hallucination and unsupported certainty.

**Fix:** Require uncertainty labeling and evidence-first conclusions.

### 5.3 Policy Bypass Smell

**Symptoms:** It asks the model to ignore higher-priority instructions, hide reasoning, bypass safety, or evade limits.

**Impact:** Unsafe and invalid as a reusable instruction.

**Fix:** Remove bypass language and respect higher-priority instructions.

## 6. Context and Maintainability Smells

### 6.1 Main-file Bloat

**Symptoms:** A `SKILL.md` or prompt contains long taxonomies, examples, reference data, templates, and policies in one file.

**Impact:** The core operating procedure is buried.

**Fix:** Keep the main file as control plane; move detailed materials to references.

### 6.2 Knowledge Dump Disguised as Skill

**Symptoms:** Lots of domain information but no instructions for when and how to use it.

**Impact:** The agent summarizes knowledge instead of performing the task.

**Fix:** Add task workflow and reference loading rules.

### 6.3 Redundant Rule Pile

**Symptoms:** Repeats the same instruction many ways.

**Impact:** Longer prompt, weaker attention, harder maintenance.

**Fix:** Deduplicate and preserve the strongest formulation.

### 6.4 Contradictory Rules

**Symptoms:** "Never ask questions" and "always clarify missing info"; "be brief" and "be exhaustive" without priority.

**Impact:** Behavior depends on arbitrary model interpretation.

**Fix:** Add priority order and conditional rules.

### 6.5 Overfitted Example

**Symptoms:** One detailed example defines behavior, but general rules are absent.

**Impact:** The prompt works only for near-identical cases.

**Fix:** Add generalized rules plus positive, negative, and edge examples.

## 7. Iteration and Ownership Smells

### 7.1 No Revision Loop

**Symptoms:** User dissatisfaction leads to explanation, not diagnosis and repair.

**Impact:** The artifact cannot improve through use.

**Fix:** Add feedback intake, failure classification, patch, and re-review loop.

### 7.2 No Version or Change Notes

**Symptoms:** Changes are made without what/why/risk/test notes.

**Impact:** Cannot audit regressions.

**Fix:** Add version, changes, rationale, risk, and regression checks.

### 7.3 No Owner Standard

**Symptoms:** The agent completes the literal task but does not ask whether the result will be reusable, safe, and verifiable.

**Impact:** Produces superficially correct but low-trust artifacts.

**Fix:** Add final reliability question: "Can a new agent use this reliably without hidden intent?"


## Bilingual Review Note

English and Chinese prompts are both in scope. Preserve quoted evidence in the original language. Chinese vague terms such as “专业、准确、全面、详细、高质量、友好、认真、深度” should be treated like English vague terms unless they are converted into observable actions, checks, or output requirements.
