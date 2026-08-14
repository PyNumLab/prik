---
title: Utilities Component
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, index.md, semantics.md, planning.md, codegen.md
status: maintained
publication: reviewed
---

# Utilities Component

## Purpose And Boundaries

`prik/utilities/` contains mechanisms shared by more than one architecture
stage. A helper belongs here only while it remains independent of source
grammar, semantic policy, backend behavior, and build orchestration.

## Local Structure

```text
prik/utilities/
├── declaration_expressions.py
├── stage_values.py
├── strings.py
└── visitor.py
```

- [`declaration_expressions.py`](../../../prik/utilities/declaration_expressions.py)
  splits declaration text, translates Fortran extents, resolves references to
  wrapper roles, evaluates constant expressions, and renders completed C or
  Fortran expressions.
- [`stage_values.py`](../../../prik/utilities/stage_values.py) provides
  `StageRecord`, which a producer assembles before its consumer recursively
  freezes it. `FrozenStageRecordError` rejects later mutation.
- [`strings.py`](../../../prik/utilities/strings.py) provides
  `create_incremented_string()` for collision-free local names and
  `random_string()` for unconstrained temporary identifiers. Public and native
  name policy belongs in `prik.naming`.
- [`visitor.py`](../../../prik/utilities/visitor.py) provides `ClassVisitor`.
  It selects the most specific configured class handler, then deliberately
  follows the model's method-resolution order.

## Declaration-Expression Workflow

`declaration_expressions.py` keeps one expression in different forms at
explicit boundaries:

```text
Fortran declaration text
  -> parser-safe splitting
  -> public Python-style extent expression
  -> references bound to completed wrapper roles
  -> constant evaluation or backend rendering
```

The caller supplies array facts during translation, available roles during
resolution, and backend substitutions during rendering. The utility reports
unresolved blockers; it does not decide whether a wrapper can supply a value.

## Run The Module Demonstrations

The declaration-expression example follows one extent through translation,
role binding, and Fortran rendering:

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

The stage-value example shows that a producer can edit nested values until the
consumer freezes the record:

```bash
python3 prik/utilities/stage_values.py
```

```text
Editable parser output: geometry -> ['scale', 'norm']
Frozen consumer input: geometry -> ('scale', 'norm')
Mutation rejected: ParserOutput is frozen by its consuming stage
```

Wrapper generation freezes a completed plan, printers freeze generated nodes,
and build integration freezes the generated wrapper before writing it.

The remaining examples show collision-free local naming and exact-class/MRO
visitor dispatch:

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

## Change Routes And Evidence

- Keep declaration parsing, public normalization, role resolution, constant
  evaluation, and backend rendering as separate operations.
- Freeze a `StageRecord` at its consumer boundary, after its producing stage
  has completed local assembly.
- Put public or target-language name rules in `prik.naming`, not `strings.py`.
- Define semantic or backend visitor handlers in their owning stage; the
  shared visitor supplies dispatch only.

| Evidence | What it establishes |
| --- | --- |
| [Utility tests](../../../tests/fortran/infrastructure/utilities/) | Local-name allocation and generic visitor dispatch. |
| [Declaration-expression tests](../../../tests/fortran/arrays/semantics/test_declaration_expression_utilities.py) | Translation, validation, role resolution, evaluation, and rendering. |
| [Wrapper freeze-boundary tests](../../../tests/fortran/infrastructure/pipeline/test_wrapper_generator.py) | Plans and generated nodes reject mutation after consumption. |

Move a helper out of `utilities/` as soon as it starts selecting semantic
policy, emitted mechanisms, or a pipeline action.
