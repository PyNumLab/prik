---
title: Semantics Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, parser package guide
related: ../architecture.md, index.md, parsers.md, policy.md, ../concepts/datatype-lifecycle.md
status: maintained
publication: draft
---

# Semantics Package

## Purpose And Boundaries

`prik/semantics/` converts Fortran parser facts or semantic `.pyi` AST into the
same language-neutral `SemanticModule` graph. It owns stable types, public and
native identities, shapes, projections, provenance, storage contracts, and raw
metadata. It does not complete ownership, select lowering actions, plan
wrappers, or emit source.

## Local Structure

```text
prik/semantics/
├── models.py
├── scalar_types.py
├── fortran2ir.py
├── pyi2ir.py
├── metadata.py
├── pyi_metadata.py
├── ownership_metadata.py
├── native_array_handles.py
└── native_contract.py
```

The deferred C-to-IR path is intentionally excluded from the published
Fortran contributor workflow.

## Internal Workflow

```text
Fortran parser models + measured target facts ─┐
                                               ├─> SemanticModule graph
semantic .pyi AST ─────────────────────────────┘
  -> raw ownership/native contract metadata
  -> prik.policy completion
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `models.py` | `SemanticModule`, `SemanticFunction`, `SemanticClass`, `SemanticArgument`, `SemanticType`, array/storage contracts, `SemanticOrigin` | Defines the language-neutral graph. |
| `scalar_types.py` | `SemanticScalarSpec` and scalar catalogue | Defines stable scalar identities and intrinsic family/storage facts without backend spellings. |
| `fortran2ir.py` | `FortranToIRConverter` | Resolves Fortran models and probed facts into semantic IR. |
| `pyi2ir.py` | `convert_pyi_to_ir()` | Interprets parsed Python AST as an editable semantic contract. |
| `ownership_metadata.py` | normalized ownership and pointer request setters | Stores unresolved frontend requests for later policy completion. |
| `native_array_handles.py` | `NativeArrayHandleFacts` | Separates descriptor, array-data, and element facets. |
| `native_contract.py` | `NativeContractIssue` and validation helpers | Prepares and validates source-free native placement and ABI facts. |

`metadata.py` and `pyi_metadata.py` are passive shared-key registries. Combined
multi-file `.pyi` loading belongs to `prik/pipeline/pyi.py`.

## Execution Examples

```bash
python3 prik/semantics/models.py
```

```text
Semantic module: geometry
Function: scale -> native SCALE
Argument: values: Float64, rank=1, shape=('n',), order=F
Source provenance: fortran real
```

```bash
python3 prik/semantics/scalar_types.py
```

```text
Float64: family=real, storage=64 bits
Int: family=signed_integer, storage=target-dependent
Backend spelling stored here: False
```

```bash
python3 prik/semantics/fortran2ir.py
```

```text
math.scale(value): Float64 via reference storage
```

```bash
python3 prik/semantics/pyi2ir.py
```

```text
math.scale(value): Float64 -> Float64
```

```bash
python3 prik/semantics/ownership_metadata.py
```

```text
Raw ownership request: owner=caller, transfer=in_place, destruction=caller
Pointer contract: nullable=True, lifetime=owner, reassociation=forbidden
Completed lowering action present: False
```

```bash
python3 prik/semantics/native_array_handles.py
```

```text
Descriptor kind: allocatable
Data facet: Float64, rank=2, shape=('rows', 'columns')
Element facet: Float64, rank=0
Handle marker retained by data facet: False
```

```bash
python3 prik/semantics/native_contract.py
```

```text
Prepared origin: fortran module math
Valid contract issues: 0
Invalid contract issue: pyi_native_type_missing at math.broken.value
```

These examples show stable semantic representation and raw contract facts.
None contains a completed binding or bridge action.

## Tests

- [Semantic IR conversion](../../../tests/fortran/semantic_ir/semantics/)
- [Semantic `.pyi` behavior](../../../tests/fortran/semantic_pyi_format/)
- [Datatype semantics](../../../tests/fortran/data_types/semantics/)
- [Native handle semantics](../../../tests/fortran/infrastructure/semantics/test_native_array_handles.py)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Change graph shape in `models.py` only when downstream contracts need a new
  language-neutral fact.
- Change stable primitive vocabulary in `scalar_types.py`.
- Change frontend interpretation in the matching converter.
- Change lifetime, transfer, setter, projection, or support decisions in
  policy, never in semantic conversion.

## Invariants And Common Mistakes

- Parser source spellings and backend dtype spellings are not semantic type
  identities.
- Raw ownership metadata is not completed ownership policy.
- Preserve provenance when normalizing language-specific facts.
