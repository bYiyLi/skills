---
name: unified-object-design
description: Use when designing or reviewing software capability interfaces, domain objects, data models, or storage schemas where several proposed objects look similar, differ mostly by purpose or label, risk causing CRUD/interface explosion, or could be represented as one bounded object with a weak string type and strong responsibility constraints. Triggers include capability design, data model simplification, schema consolidation, "these objects look alike", "can we merge these", "avoid over-design", "referenceType", "weak type", "strong boundary", and WeaveNovel-style AI-assisted design.
---

# Unified Object Design

Use this skill to simplify capability and data-model designs by merging weakly different objects into one bounded object, while preventing the merged object from becoming a catch-all.

## Core Pattern

Apply:

```text
Unified object + weak type label + strong boundary definition
```

This means:

1. Merge objects when they have the same owner, lifecycle, operations, and boundary.
2. Preserve purpose differences with a plain string field such as `referenceType`.
3. Do not enforce pseudo-business categories with program enums unless the system truly acts on them.
4. Write a strong definition for the unified object so the weak type does not become a dumping ground.

## When To Merge

Merge candidate objects when most of these are true:

```text
1. They belong to the same parent aggregate or scope.
2. They are created, updated, deleted, and read in the same way.
3. They share the same persistence lifecycle and status semantics.
4. Their difference is mainly how a human or AI should interpret them.
5. The program does not need different invariants, permissions, indexes, workflows, or runtime behavior per subtype.
6. Keeping them separate would multiply nearly identical CRUD interfaces.
```

Do not merge when a candidate has independent lifecycle, strong validation, dedicated query needs, special permissions, separate scaling behavior, or the program must execute different logic for that type.

## Design Steps

1. List proposed objects and their interfaces.
2. Determine from the available requirements what each object answers in one sentence; ask the user only when a missing fact would change the proposed boundary.
3. Compare ownership, lifecycle, operations, and storage shape.
4. If they match, propose one unified object.
5. Add a weak type label:

```text
type: string
```

Prefer a domain-specific field name such as `referenceType`, `artifactType`, or `noteType`.

6. State explicitly that the program stores the string but does not validate it as an enum.
7. Define the unified object's hard boundary:

```text
It is ...
It can express ...
It cannot express ...
It does not own ...
It must not become ...
```

8. Collapse interfaces around the unified object's lifecycle:

```ts
createObject(scopeId, input): Object
updateObject(scopeId, objectId, patch): Object
deleteObject(scopeId, objectId): Object
```

9. Prefer reading small, high-frequency unified objects from the parent detail response. Add list/detail APIs only when data volume, search, pagination, authorization, or independent detail views require them.
10. In review, identify affected downstream storage and data-model documents and propose the needed edits. Update them only when the host task explicitly authorizes those changes. Return to the host task afterward; this guidance does not authorize implementation, commits, or pushes.

## Boundary Template

Use this template when defining the unified object:

```text
<ObjectName> is ...

It is used to ...

It only answers:
...

It does not answer:
...

It can express:
1. ...
2. ...
3. ...

It cannot express:
1. ...
2. ...
3. ...

<typeField> is only a string label written by callers.
The program does not restrict values and does not validate it as an enum.
<typeField> may help humans or AI interpret the object, but it cannot change the object's capability boundary.
```

## WeaveNovel Example

Old design:

```text
NovelBrief
NovelWritingRule
NovelMaterial
```

Problem:

```text
They all belong to one novel, provide creative reference context, use similar CRUD behavior, and do not require program-enforced subtype logic.
```

New design:

```text
NovelReference {
  id
  novelId
  referenceType
  title
  content
  tags
  source
  status
  createdAt
  updatedAt
}
```

Interfaces:

```ts
createNovelReference(novelId, input): NovelReference
updateNovelReference(novelId, referenceId, patch): NovelReference
deleteNovelReference(novelId, referenceId): NovelReference
```

Read path:

```text
getNovel(novelId) returns references: NovelReference[]
```

Storage projection:

```cypher
(:Novel)-[:HAS_REFERENCE]->(:NovelReference)
```

Boundary:

```text
NovelReference is creative reference material.
It is not prose content.
It is not a canon asset.
It is not a runtime story fact.
It is not a program-enforced validation rule.
```

## Review Checklist

Before accepting the design, verify:

```text
1. The merged object has one clear responsibility.
2. The type label is weak by design and not a hidden enum.
3. The system does not need different behavior per type today.
4. The "cannot express" list blocks adjacent-domain leakage.
5. Interface count actually decreases.
6. Storage model also becomes simpler.
7. Future split criteria are clear.
```

Split later only when one subtype gains independent lifecycle, strong program rules, dedicated query or indexing needs, or separate ownership.
