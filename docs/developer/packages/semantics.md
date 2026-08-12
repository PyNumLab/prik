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
├── __init__.py
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

## What This Stage Receives And Produces

```text
Fortran parser models + measured target facts ─┐
                                               ├─> SemanticModule graph
semantic .pyi AST ─────────────────────────────┘
  -> raw ownership/native contract metadata
  -> prik.policy completion
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/semantics/__init__.py`](../../../prik/semantics/__init__.py) | Re-exports supported Fortran conversion and `.pyi` conversion entrypoints. | The supported semantic-conversion import API changes. |
| [`prik/semantics/models.py`](../../../prik/semantics/models.py) | `SemanticModule`, `SemanticFunction`, `SemanticClass`, `SemanticArgument`, `SemanticType`, storage/array contracts, and `SemanticOrigin` form the shared language-neutral graph. | A downstream consumer needs a new language-neutral fact. |
| [`prik/semantics/scalar_types.py`](../../../prik/semantics/scalar_types.py) | `SemanticScalarSpec` and the scalar catalogue give stable identities and intrinsic family/storage facts without backend spelling. | Stable scalar vocabulary or intrinsic facts change. |
| [`prik/semantics/fortran2ir.py`](../../../prik/semantics/fortran2ir.py) | `FortranToIRConverter` combines parser models and measured facts into semantic IR; public helpers handle files, modules, and projects. | A Fortran source fact needs a different semantic interpretation. |
| [`prik/semantics/pyi2ir.py`](../../../prik/semantics/pyi2ir.py) | `convert_pyi_to_ir()` interprets parsed Python AST as an editable semantic contract and reconciles external type references. | A supported `.pyi` construct needs semantic meaning. |
| [`prik/semantics/metadata.py`](../../../prik/semantics/metadata.py) | Passive keys shared by semantic owners. | A generic semantic metadata key or its canonical spelling changes. |
| [`prik/semantics/pyi_metadata.py`](../../../prik/semantics/pyi_metadata.py) | Passive keys specific to `.pyi` interpretation. | Parsed `.pyi` metadata needs a canonical key. |
| [`prik/semantics/ownership_metadata.py`](../../../prik/semantics/ownership_metadata.py) | Normalizes raw ownership and pointer requests without resolving them. | A frontend request needs preservation before policy completion. |
| [`prik/semantics/native_array_handles.py`](../../../prik/semantics/native_array_handles.py) | `NativeArrayHandleFacts` keeps descriptor, data, and element facets separate. | Semantic description of a native descriptor-backed array changes. |
| [`prik/semantics/native_contract.py`](../../../prik/semantics/native_contract.py) | `NativeContractIssue` and helpers prepare and validate source-free native placement and ABI facts. | Native contract validation or diagnostics change. |

Combined multi-file `.pyi` loading belongs to `prik/pipeline/pyi.py`. Completed
ownership, projection, and lowering actions belong to `policy/`, never here.

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

## Tests And What They Prove

- [Semantic IR conversion](../../../tests/fortran/semantic_ir/semantics/) covers Fortran-model conversion and graph shape.
- [Semantic `.pyi` behavior](../../../tests/fortran/semantic_pyi_format/) covers contract interpretation and external references.
- [Datatype semantics](../../../tests/fortran/data_types/semantics/) covers stable type and storage facts.
- [Native handle semantics](../../../tests/fortran/infrastructure/semantics/test_native_array_handles.py) covers descriptor/data/element separation.
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py) fixes the seven stage demonstrations above.

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
