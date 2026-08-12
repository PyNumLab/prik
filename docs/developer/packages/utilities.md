---
title: Utilities Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, index.md, semantics.md, planning.md, codegen.md
status: maintained
publication: draft
---

# Utilities Package

## Purpose And Boundaries

`prik/utilities/` contains small mechanisms that are genuinely independent of
one compiler stage. A helper belongs here only while it avoids stage-owned
semantic policy, syntax grammar, and workflow orchestration.

## Local Structure

```text
prik/utilities/
├── __init__.py
├── declaration_expressions.py
├── strings.py
└── visitor.py
```

## What This Stage Receives And Produces

```text
stage-owned caller facts
  -> reusable expression, local-name, or visitor mechanism
  -> requesting stage
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/utilities/__init__.py`](../../../prik/utilities/__init__.py) | Package boundary for small stage-neutral mechanisms. | Establishing a deliberate package-level utility API. |
| [`prik/utilities/declaration_expressions.py`](../../../prik/utilities/declaration_expressions.py) | `ResolvedDeclarationExtent`, `DeclarationExpressionCall`, and `ArrayExpressionSource` translate, validate, resolve, evaluate, and render declaration extents at explicit handoffs. | An extent representation or its stage-owned translation changes. |
| [`prik/utilities/strings.py`](../../../prik/utilities/strings.py) | Collision-safe local-name helpers allocate deterministic temporary identifiers. | Generic local name allocation changes; public name policy belongs in `naming/`. |
| [`prik/utilities/visitor.py`](../../../prik/utilities/visitor.py) | `ClassVisitor` provides exact-class dispatch with intentional MRO fallback. | Shared generic dispatch changes, not a stage's visitor methods. |

## Execution Examples

```bash
python3 prik/utilities/declaration_expressions.py
```

```text
Fortran extent: ubound(source, 1) - lbound(source, 1) + 1
Public expression: source.shape[0]
Role-bound expression: __prik_extent_source_0
Fortran rendering: native_source_extent_0
Compile-time product: 6
```

The expression changes representation at explicit stages. Backend rendering
uses a plan-supplied substitution and does not rediscover argument ownership.

```bash
python3 prik/utilities/strings.py
```

```text
First available name: temporary_4
Next counter: 5
```

```bash
python3 prik/utilities/visitor.py
```

```text
Exact handler: literal:42
MRO fallback: expression:Expression
```

## Tests And What They Prove

- [Utility infrastructure](../../../tests/fortran/infrastructure/utilities/) covers local-name and visitor behavior.
- [Declaration-expression semantics](../../../tests/fortran/arrays/semantics/test_declaration_expression_utilities.py) covers role resolution and expression rendering.
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py) fixes the three demonstrations above.

## Change Routes

- Keep parsing, role resolution, evaluation, and backend rendering separate in
  declaration-expression code.

## Invariants And Common Mistakes

- Consumers define their own visitor handlers; `ClassVisitor` does not merge
  frontend or backend visitor responsibilities.
- Move a helper out of utilities as soon as it starts selecting semantic
  policy or a pipeline action.
