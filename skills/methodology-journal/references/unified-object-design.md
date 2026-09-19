# Unified Object Design

## Problem Pattern

Several proposed domain objects or capability objects look different by name, but share the same parent scope, lifecycle, CRUD operations, status semantics, and storage shape.

Keeping them separate creates interface explosion, storage duplication, and fake program rules.

## Core Principle

Use one unified object, preserve caller intent with a weak string type label, and protect the design with a strong boundary definition.

## Use When

- Multiple objects differ mainly by how humans or AI interpret them.
- The program does not need different validation, authorization, workflow, indexing, or runtime behavior per type.
- The proposed interfaces are mostly repeated CRUD operations.
- The design benefits from future caller-defined categories.
- Skill, prompt, or project conventions can guide type usage better than program enums.

## Do Not Use When

- A type has an independent lifecycle or owner.
- A type needs hard program validation or workflow transitions.
- A type requires dedicated search, pagination, storage, permission, or scale behavior.
- The system must execute different logic based on the type today.
- Merging would blur a critical domain boundary.

## Steps

1. List candidate objects and their proposed interfaces.
2. Compare owner, lifecycle, operations, status, storage, and query needs.
3. If they match, replace them with one unified object.
4. Add a weak string label such as `referenceType`.
5. State that the program stores the string but does not validate it as an enum.
6. Collapse interfaces to unified lifecycle operations: create, update, delete.
7. Prefer returning small, high-frequency objects through the parent detail response.
8. Write a hard boundary definition: can express, cannot express, does not own.
9. Sync downstream storage and design docs.
10. Record split criteria for future evolution.

## Example

Old WeaveNovel design:

```text
NovelBrief
NovelWritingRule
NovelMaterial
```

Issue:

```text
All three are novel-scoped creative reference inputs.
They had similar read/write/delete behavior and did not need separate program enforcement.
```

New design:

```text
NovelReference
referenceType: string
```

Capability interfaces:

```ts
createNovelReference(novelId, input): NovelReference
updateNovelReference(novelId, referenceId, patch): NovelReference
deleteNovelReference(novelId, referenceId): NovelReference
```

Storage:

```cypher
(:Novel)-[:HAS_REFERENCE]->(:NovelReference)
```

Boundary:

```text
NovelReference is creative reference material.
It is not prose content, canon asset, runtime story fact, program schema, audit log, or consistency result.
```

## Checklist

- [ ] The unified object has one clear responsibility.
- [ ] The type field is intentionally weak.
- [ ] Type values are not program-enforced enums.
- [ ] Adjacent-domain leakage is blocked by explicit "cannot express" rules.
- [ ] Interface count decreases.
- [ ] Storage model becomes simpler.
- [ ] Future split criteria are clear.

## Split Later When

- One type gains independent lifecycle or owner.
- One type needs hard validation, workflow, permission, search, or indexing.
- One type becomes large enough to require pagination or separate loading.
- The program must branch behavior by that type.
