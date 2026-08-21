---
title: Semantics Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, parsing-stage guide
related: ../architecture.md, index.md, parsers.md, policy.md
status: maintained
publication: reviewed
---

# Semantics Stage

## Purpose And Boundaries

`prik/semantics/` converts Fortran parser models or semantic-`.pyi` AST into a
shared, language-neutral `SemanticModule` graph. It owns stable types, native
and public identities, shapes, storage contracts, projections, provenance, and
raw contract metadata. It does not complete ownership, choose lowering
actions, plan wrappers, or emit source.

`c2ir.py` is preparatory work for a future C frontend. C support is not yet
complete and is outside the current Fortran-wrapper route, so this guide covers
the supported Fortran and semantic-`.pyi` paths.

## Inputs And Shared Representation

```text
FortranFile or FortranProject
  -> collect unresolved kind and storage requirements when needed
  -> preprocessing probes provide compile-time values and type facts
  -> FortranToIRConverter
  -> SemanticModule graph

parsed semantic .pyi ast.Module
  -> convert_pyi_to_ir
  -> local overload, prototype, and declaration-expression resolution
  -> batch external-reference reconciliation when multiple contracts are loaded
  -> native-contract preparation and validation
  -> SemanticModule graph

SemanticModule graph + raw metadata
  -> policy completion
```

Both frontend routes produce the same vocabulary. `SemanticModule` contains
functions, prototypes, overload sets, classes, variables, imports, and module
origin. `SemanticType` carries a stable type identity, rank, shape, storage,
constraints, metadata, and source origin. `SemanticFunction`, `SemanticClass`,
and `ProjectionMapping` retain callable and public-to-native correspondence.
`SemanticStorageContract` and `SemanticArrayContract` describe the declared
storage and shape; `SemanticOrigin` retains where a fact came from.

These are semantic facts, not completed policy. In particular, raw ownership
metadata and a declared storage contract do not decide who owns an object or
which bridge mechanism implements it.

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
├── native_contract.py
└── c2ir.py                     incomplete future C frontend
```

## Directory Tour

| Module | Public boundary and result | Change it when |
| --- | --- | --- |
| [`prik/semantics/__init__.py`](../../../prik/semantics/__init__.py) | Re-exports frontend-conversion helpers. Its C exports are preparatory, not a supported C wrapper route. | The semantic-conversion import surface changes. |
| [`prik/semantics/models.py`](../../../prik/semantics/models.py) | Defines the shared `SemanticModule` graph, its declarations, types, contracts, projections, origins, and equality rules. | A later stage needs a new language-neutral fact. |
| [`prik/semantics/scalar_types.py`](../../../prik/semantics/scalar_types.py) | `SemanticScalarSpec` and the scalar catalogue define stable scalar identities, families, and intrinsic storage widths without backend spellings. | Stable scalar vocabulary or intrinsic scalar facts change. |
| [`prik/semantics/fortran2ir.py`](../../../prik/semantics/fortran2ir.py) | `FortranToIRConverter` and file/module/project helpers convert parser models with optional compiler facts into semantic modules. | A Fortran source fact needs different semantic meaning. |
| [`prik/semantics/pyi2ir.py`](../../../prik/semantics/pyi2ir.py) | `convert_pyi_to_ir()` interprets one parsed contract; `reconcile_external_type_refs()` resolves a converted batch's cross-module references. | A supported `.pyi` construct or cross-contract reference needs different meaning. |
| [`prik/semantics/metadata.py`](../../../prik/semantics/metadata.py) | Defines generic cross-stage metadata keys. | A generic semantic metadata key or its canonical spelling changes. |
| [`prik/semantics/pyi_metadata.py`](../../../prik/semantics/pyi_metadata.py) | Defines `.pyi` loading-state metadata keys. | A `.pyi` loading-state key changes. |
| [`prik/semantics/ownership_metadata.py`](../../../prik/semantics/ownership_metadata.py) | Validates and stores raw ownership and pointer-contract metadata without completing it. | A frontend ownership or pointer request needs preservation before policy completion. |
| [`prik/semantics/native_array_handles.py`](../../../prik/semantics/native_array_handles.py) | Marks allocatable or pointer array descriptors and derives their ordinary data and element facets. | Semantic facts for native descriptor-backed arrays change. |
| [`prik/semantics/native_contract.py`](../../../prik/semantics/native_contract.py) | Prepares `.pyi` native origins and reports invalid source-free native contracts. | Native contract placement, validation, or diagnostics change. |

## Module Algorithms

### `fortran2ir.py`: parser facts to semantic modules

`fortran_module_to_semantic_module()`,
`fortran_file_to_semantic_modules()`, and
`fortran_project_to_semantic_modules()` select the appropriate input shape,
then dispatch it through `FortranToIRConverter`.

The converter uses a class visitor: each Fortran parser model reaches its
matching `_visit_<ClassName>` method. It normalizes intrinsic base type and
kind into a semantic scalar identity, applies supplied compiler `type_facts`
where a target measurement is required, preserves source shapes and origins,
and creates semantic storage and projection records. It never chooses an
ownership or lowering action.

For a module, conversion builds procedures first, then callback prototypes,
derived classes, overload sets, variables, enum constants, imports, and
visibility. File and project conversion extend this context with known derived
types, callback interfaces, and procedures before converting each source unit
in parser order. Standalone procedures become a synthetic semantic module.

`collect_fortran_type_storage_requirements()` and
`collect_semantic_compile_time_requirements()` are the inspection half of
target-dependent conversion: they identify the expressions that preprocessing
must measure. Pass the resulting values and type facts back to conversion.
`resolve_semantic_compile_time_values()` is separate: it copies already-built
IR and substitutes known symbolic text without mutating the original.

### `pyi2ir.py`: contract AST to semantic modules

`convert_pyi_to_ir()` accepts only an `ast.Module` from `parsers/pyi`. It
creates `_PyiAstParser`, whose `_ModuleVisitor` first records user type names,
then converts imports, variables, classes, functions, prototypes, decorators,
annotations, and projections in source order.

After every local declaration is available, the parser resolves pending
overloads, local prototype references, and declaration-expression callables.
It then marks imported types as unresolved external references. When a pipeline
loads several contract modules, `reconcile_external_type_refs()` matches those
references against the batch: prototypes become callback references and classes
become wrapped or opaque external types.

The converter validates the supported contract subset and preserves declared
native facts. For a Fortran contract, `@native_abi("c")` records an original
procedure's C ABI independently from its `@bind(...)` link label, placement,
and route-neutral `@native_call(...)` projection. It does not execute
declarations, load native code, infer a wrapper route, or complete ownership
policy.

### `models.py` and `scalar_types.py`: the shared vocabulary

`models.py` is deliberately a data vocabulary. `SemanticModule` is the
convergence object consumed by policy and planning. `SemanticType` describes a
value or object shape; `SemanticStorageContract` and `SemanticArrayContract`
preserve storage and array declarations; `SemanticOrigin` preserves native
identity and source provenance. Functions, classes, methods, prototypes, and
overload sets organize those facts without deciding how they will be lowered.

`scalar_types.py` maps stable names such as `Float64` and `Int32` to a scalar
family and, when fixed by the name, storage width. Names such as `Int` remain
target-dependent. NumPy dtypes and emitted C or Fortran spellings belong to
later boundary owners.

### Raw metadata, descriptors, and native contracts

`metadata.py` and `pyi_metadata.py` contain canonical key names only. They
prevent frontend and later-stage code from inventing equivalent spellings.

`ownership_metadata.py` validates raw owner, transfer, destruction, and
pointer-contract requests before storing them on semantic metadata. This
normalizes frontend input but does not resolve the completed policy that
`policy/` owns.

`native_array_handles.py` marks an array semantic type as an allocatable or
pointer descriptor. `native_array_data_type()` returns a copied ordinary-array
facet with handle-only metadata removed; `native_array_handle_facts()` derives
that data facet and its rank-zero element facet.

`native_contract.py` applies native origins to `.pyi` modules and validates the
declared module scope, projection ordering, type completeness, and callback
references. `native_contract_issues()` returns all issues; `validate_pyi_native_contract()`
raises the first one. This is contract validation, not wrapper-policy
completion.

## Run The Workflows

The model example shows the shared representation assembled without a frontend:

```bash
python3 prik/semantics/models.py
```

```text
Semantic module: geometry
Function: scale -> native SCALE
Argument: values: Float64, rank=1, shape=('n',), order=F
Source provenance: fortran real
```

The script constructs the module, function, argument, and storage records
directly. The output shows that one semantic type can retain shape, order, and
Fortran provenance without containing a C or Fortran backend spelling.

The scalar catalogue separates stable identity from backend spelling:

```bash
python3 prik/semantics/scalar_types.py
```

```text
Float64: family=real, storage=64 bits
Int: family=signed_integer, storage=target-dependent
Backend spelling stored here: False
```

It looks up one fixed-width real and one target-dependent integer identity.
The final line is the boundary: language-specific spelling is deliberately a
later code-generation concern.

The two frontend converters reach the same kind of semantic declaration:

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

The Fortran example converts a parser-level declaration; the `.pyi` example
converts a parsed contract declaration. Their matching `math.scale` records
show the two frontends converging on the same semantic vocabulary, while their
source-specific details remain attached as provenance and metadata.

Raw ownership and pointer requests remain distinct from completed policy:

```bash
python3 prik/semantics/ownership_metadata.py
```

```text
Raw ownership request: owner=caller, transfer=in_place, destruction=caller
Pointer contract: nullable=True, lifetime=owner, reassociation=forbidden
Completed lowering action present: False
```

The script attaches raw ownership and pointer requests to a semantic value.
Those fields describe what the contract asks for; `False` confirms that policy
completion has not yet selected a lowering action.

Native array handles retain the descriptor separately from its data and element
facets:

```bash
python3 prik/semantics/native_array_handles.py
```

```text
Descriptor kind: allocatable
Data facet: Float64, rank=2, shape=('rows', 'columns')
Element facet: Float64, rank=0
Handle marker retained by data facet: False
```

The example creates a descriptor-backed array type and reads its separate data
and element facets. The final line confirms that the handle marker stays on the
descriptor boundary instead of leaking into the ordinary data value.

Native-contract preparation reports declared contract errors before policy or
generation:

```bash
python3 prik/semantics/native_contract.py
```

```text
Prepared origin: fortran module math
Valid contract issues: 0
Invalid contract issue: pyi_native_type_missing at math.broken.value
```

The script prepares one valid and one invalid contract declaration. Zero valid
issues and the named invalid issue show that contract diagnostics are attached
before policy completion or any backend lowering begins.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Semantic IR conversion](../../../tests/fortran/infrastructure/semantic_ir/semantics/) | Fortran-model conversion, compile-time requirements, specialization, and semantic graph properties. |
| [Fortran datatype semantics](../../../tests/fortran/data_types/semantics/) | Stable scalar identities, storage facts, and compiler-measurement handoffs. |
| [Semantic `.pyi` conversion](../../../tests/fortran/infrastructure/semantic_pyi/semantics/) | Contract constructs, imports, external references, projections, classes, overloads, and round trips. |
| [Native array handles](../../../tests/fortran/infrastructure/policy/test_native_array_handles.py) | Descriptor marking and separation of handle, data, and element facts. |
| [Native contract validation](../../../tests/fortran/infrastructure/semantic_pyi/semantics/test_types_and_values.py) | Native-contract preparation, validation, and diagnostic ownership. |

## Change Routes

- Change the shared IR graph, equality, or a language-neutral representation
  in `models.py`.
- Change stable primitive vocabulary in `scalar_types.py`.
- Change Fortran parser-fact interpretation, compile-time requirement
  collection, or semantic specialization in `fortran2ir.py`.
- Change `.pyi` contract interpretation or batch reference reconciliation in
  `pyi2ir.py`; path-set loading remains in `pipeline/pyi.py`.
- Change raw metadata canonicalization in the matching metadata module.
- Change descriptor facts in `native_array_handles.py` and source-free native
  contract validation in `native_contract.py`.
- Change ownership, transfer, lifecycle, projections, support, or lowering
  actions in `policy/`, not in semantic conversion.

## Boundaries And Invariants

- Parser spellings, target compiler facts, semantic scalar identities, and
  backend spellings are different representations.
- Preserve native names, scope, and source provenance while normalizing a
  frontend fact.
- Raw ownership metadata is not completed ownership policy.
- Batch reference reconciliation requires all participating `.pyi` modules;
  single-module conversion leaves external references unresolved by design.
- A semantic declaration is not automatically wrapper support.

## Failure Boundary

This stage reports unsupported frontend facts, invalid semantic contracts,
missing target facts needed for semantic conversion, unresolved local contract
relationships, and invalid source-free native placement. It delegates source
syntax to `parsers/`, compiler measurement to `preprocessing/`, completed
interoperability choices to `policy/`, and lowering to later stages. Start with
the first incorrect parser fact, compiler fact, or semantic record—not a later
policy, build, or generated-code failure.
