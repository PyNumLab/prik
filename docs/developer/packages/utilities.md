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
├── declaration_expressions.py
├── strings.py
└── visitor.py
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `declaration_expressions.py` | `ResolvedDeclarationExtent`, `DeclarationExpressionCall`, `ArrayExpressionSource` | Translates, validates, resolves, evaluates, and renders declaration extents across explicit stage boundaries. |
| `strings.py` | collision-safe local-name helpers | Allocates deterministic local names without owning a public naming policy. |
| `visitor.py` | `ClassVisitor` | Provides exact-class and intentional MRO fallback dispatch shared by independent visitors. |

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

## Tests

- [Utility infrastructure](../../../tests/fortran/infrastructure/utilities/)
- [Declaration-expression semantics](../../../tests/fortran/arrays/semantics/test_declaration_expression_utilities.py)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Keep parsing, role resolution, evaluation, and backend rendering separate in
  declaration-expression code.

## Invariants And Common Mistakes

- Consumers define their own visitor handlers; `ClassVisitor` does not merge
  frontend or backend visitor responsibilities.
- Move a helper out of utilities as soon as it starts selecting semantic
  policy or a pipeline action.
