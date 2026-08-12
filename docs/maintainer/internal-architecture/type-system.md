---
title: Datatype Lifecycle
audience: maintainers
prerequisites: pipeline map, semantic IR
related: pipeline-map.md, wrapper-generation-pipeline.md, ownership-tracking.md, ../../user/reference/semantic-ir.md
status: maintained
publication: draft
---

# Datatype Lifecycle

This page is the implementation contract for datatype handling inside PRIK. It
traces native declarations from compiler measurement and parsing through
semantic normalization, policy completion, wrapper planning, generated NumPy
boundaries, and runtime validation. It also identifies the separate registries
used at those stages and explains why they must not be collapsed into one
bidirectional type map.

The central rule is:

> Compiler probes describe the selected native target, semantic IR gives those
> facts stable language-neutral identities, policy completes behavior for each
> use site, and code generation selects emitted representations from the
> completed plan.

NumPy is a Python-boundary representation. It is not the authority for native
storage, semantic identity, ownership, mutability, or lifetime.

## End-To-End Datatype Flow

```text
native source declaration
  -> compiler preprocessing
  -> parser-native datatype, kind, shape, and attribute facts
  -> compiler probes for target-dependent kind and storage values
  -> source-to-IR conversion
       -> stable semantic name and resolved dtype
       -> origin and native spelling
       -> rank, shape, storage category, and source provenance
  -> post-IR policy completion
       -> ownership, transfer, destruction, mutability, and projection
       -> boundary storage mode and supported/blocked decision
  -> wrapper planning
       -> datatype family plus completed transfer/result/access plans
  -> backend scalar registry and specialized datatype lowering
  -> generated native bridge and Python/NumPy binding nodes
  -> language printers
  -> native compilation and linking
  -> exact runtime boundary validation
```

Each arrow changes the representation for a reason. The parser preserves what
the source declared. Probing supplies facts the source spelling alone cannot
determine. Semantic conversion normalizes equivalent source forms. Policy adds
context-dependent behavior. Planning freezes that behavior into an
implementation contract. Codegen then chooses syntax and runtime operations;
it does not reinterpret the datatype.

## The Four Datatype Authorities

PRIK deliberately has four related but non-interchangeable authorities.

| Authority | Owner | Key | Value | Purpose |
| --- | --- | --- | --- | --- |
| Native target facts | `prik/probes/` | compiler expression or native spelling | measured kind, storage, precision, signedness, or availability | Describe the selected compiler target. |
| Semantic scalar catalogue | `prik/semantics/scalar_types.py` | stable semantic name such as `Float64` | family and intrinsic storage facts | Define language-neutral scalar vocabulary without importing NumPy. |
| Runtime contract factories | `prik/contracts/__init__.py` | semantic contract name | real NumPy scalar factory or an explicit constructor error | Make public semantic `.pyi` symbols safely usable at runtime where supported. |
| Backend datatype catalogues | `prik/codegen/primitive_scalar_types.py` | resolved semantic name | emitted NumPy expressions plus native spellings, NumPy type macros, Python parse/result behavior, and descriptor spelling | Project semantic dtypes for reporting and lower implemented primitive scalar plans without coupling the two generators. |

The same semantic name appears in more than one table because each table owns
different facts. Consistency tests compare their overlapping keys, but one
stage must not import a later stage merely to avoid repeating an invariant it
owns independently.

## Native Target Probing

### Why probing exists

Source spelling is insufficient for target-dependent datatypes. A default
integer kind, a selected real kind, a legacy star-width declaration, and a
named interoperable kind can denote different storage on different compiler
targets or under different target-changing flags.

The build pipeline therefore uses the same effective compiler configuration
for preprocessing, datatype measurement, native compilation, and generated
bridge compilation. Flags that change kinds, widths, ABI, or target architecture
must reach probing. A report measured under one target must not be reused as if
it described another.

`prik/probes/fortran_types.py` compiles generated measurement programs and
returns `FortranTypeProbeReport`. Its cache identity includes the generated
source, compiler identity, flags, working directory, target environment, and
optional runner. The two main outputs are:

- compile-time values used to resolve kind and specification expressions;
- storage facts for intrinsic datatype/kind pairs used by semantic conversion.

`prik/pipeline/build.py` collects requirements from the parsed project, asks the
probe service only for required facts, and supplies the evaluated values and
type facts to `FortranToIRConverter`. Probes never decide ownership, Python
visibility, output projection, or wrapper support.

<!-- PRIK_C_DOCS_START
The C inspection path follows the same separation. `prik/probes/c_types.py`
measures width, signedness, precision, availability, and opaque-handle facts
for standard C spellings. `CToIRConverter` consumes the report and maps known
facts to stable semantic dtypes. Missing or unsupported facts remain explicit
instead of being guessed from the host Python process.
PRIK_C_DOCS_END -->

### Probe reports are evidence, not semantic models

A probe report records reproducible compiler observations. It may be serialized
or cached, but it does not become semantic IR and it does not contain wrapper
policy. Source-to-IR conversion owns the interpretation of those observations.

The Markdown datatype report lives in `prik/pipeline/type_mapping_report.py`
because it intentionally combines several stages:

```text
probe facts -> semantic conversion -> backend NumPy projection -> Markdown
```

That report is documentation and inspection output. It is not an alternative
conversion path and must reuse the normal converters and backend catalogue.

## Parsing And Semantic Normalization

Parsers preserve native declarations rather than prematurely replacing them
with Python or NumPy types. Relevant parser facts include:

- native base type and kind spelling;
- declaration or measured storage width;
- scalar versus array shape and rank;
- pointer, allocatable, target, optional, and value attributes;
- character kind and length syntax;
- derived-type identity and scope;
- procedure/callback signature structure;
- source coordinates and the original native spelling.

The source-to-IR converters combine those facts with target measurements and
produce `SemanticType` plus `SemanticOrigin` and `SemanticStorageContract`.
`SemanticType.name` is the public semantic identity. `SemanticType.dtype` is
the resolved storage dtype used by later stages. They can differ when a stable
public concept has target-specific storage.

For example, an unresolved native default integer can begin as `Int`, then
resolve to `Int32` or `Int64` after compiler measurement. The converter records
the source spelling and target provenance; it does not replace those facts with
`numpy.int32` or `numpy.int64`.

## Semantic Scalar Catalogue

`prik/semantics/scalar_types.py` is the single semantic vocabulary for
primitive scalar names. Its immutable `SemanticScalarSpec` records only facts
that are intrinsic to the semantic identity:

- datatype family;
- storage width when the semantic identity fixes one;
- whether the name represents a Boolean storage contract.

The module exposes checked helpers for scalar membership and Boolean storage
width. It does not import NumPy and contains no emitted source spelling.
Extended `Float128` and `Complex256` catalogue entries intentionally leave
`storage_bits` unresolved because supported targets can store them in 80/96/128
or 160/192/256 bits respectively; compiler facts select the actual storage.

Boolean names demonstrate why the semantic and NumPy layers are distinct:

| Semantic name | Native storage contract | NumPy boundary dtype |
| --- | --- | --- |
| `Bool` | default or interoperable Boolean, normalized to 8-bit boundary storage | `numpy.bool_` |
| `Bool8` | 8 bits | `numpy.bool_` |
| `Bool16` | 16 bits | `numpy.bool_` |
| `Bool32` | 32 bits | `numpy.bool_` |
| `Bool64` | 64 bits | `numpy.bool_` |

The binding normalizes Boolean values at the boundary, while the generated
bridge uses the compiler-resolved native logical representation. A NumPy dtype
alone therefore cannot reconstruct the original semantic Boolean contract.

## Runtime Contract Factories

`prik/contracts/__init__.py` owns the public names used by generated and edited
semantic `.pyi` contracts. Its private contract-factory catalogue maps a
semantic name to a real NumPy scalar factory where a portable runtime value
exists. This lets expressions such as `Float64()` create the exact scalar type
required by a generated wrapper and lets typed descriptor contracts retain a
concrete `numpy.dtype`.

Names without a portable runtime factory remain explicit contract symbols and
raise a focused constructor error. Examples include unresolved `Int`, `UInt`,
`CEnum`, `Char`, `String`, and `Void`. The contracts package does not perform
source-to-IR conversion and its factories do not define native ABI storage.

## Backend Primitive Scalar Catalogue

`prik/codegen/primitive_scalar_types.py` owns two readable mappings.
`NumpyDtypeRegistry.TYPES` maps every resolved semantic dtype with a maintained
NumPy projection to its emitted expression. `PrimitiveScalarTypeRegistry.TYPES`
contains the narrower set with implemented native wrapper lowering. Each
`BackendScalarType` entry uses keyword arguments so a maintainer can audit one
row without remembering positional field order.

The fields cover:

| Field | Meaning |
| --- | --- |
| `semantic_name` | Resolved semantic key consumed from the wrapper plan. |
| `c_spelling` | Native binding-side storage spelling. |
| `fortran_spelling` | Generated bridge declaration spelling. |
| `python_parse_unit` | Python argument parsing unit used by the binding. |
| `numpy_type_macro` | NumPy array dtype identity checked or allocated in generated code. |
| `python_result_kind` | Result-conversion path for an ordinary procedure result. |
| `python_type_name` | Python/NumPy scalar expression shown in validation diagnostics or constructors. |
| `python_module_result_kind` | Result-conversion path for module state. |
| `cfi_type_spelling` | Descriptor element type identity for descriptor-based boundaries. |

The catalogue contains only implemented primitive scalar lowering lanes.
Adding a semantic name to the semantic catalogue does not automatically enable
wrapper generation. Unsupported entries must continue to fail during policy or
planning rather than acquiring guessed backend spellings.

<!-- PRIK_C_DOCS_START
The C and Fortran generators call the checked `type_for()` accessor and receive
a detached record. Neither generator chooses a different semantic type from a
NumPy macro, native spelling, source `intent`, rank, or local storage check.
PRIK_C_DOCS_END -->

## Why There Is No Universal NumPy-To-Semantic Map

The maintained lookup direction is:

```text
resolved semantic dtype -> stage-owned NumPy or backend facts
```

The reverse direction is not generally valid:

- every Boolean storage contract projects to `numpy.bool_`;
- `numpy.longdouble`, `numpy.clongdouble`, and `numpy.uintp` vary by platform;
- source concepts such as unresolved `Int`, `CEnum`, and fixed-length native
  character storage require context that a NumPy dtype does not carry;
- ownership, mutability, rank, layout, pointer association, allocation state,
  and callback identity are not dtype properties.

Runtime validation may compare an actual NumPy dtype with the exact dtype in a
completed plan. It must not use the observed dtype to infer semantic meaning or
select a different lowering path. If a future frontend accepts NumPy types as
source annotations, that frontend must own an explicitly contextual and
possibly lossy input mapping.

## Non-Primitive Datatype Families

### Arrays

An array is not a separate scalar dtype. Semantic IR stores its element dtype,
rank, shape expressions, bounds provenance, layout/order, contiguity, and
pointer or allocatable attributes in `SemanticArrayContract`. Policy completes
copy/alias behavior, writeback, nullability, descriptor ownership, and result
projection. The plan then records exact validation and transfer actions.

Generated bindings validate dtype, rank, shape, layout, alignment,
writeability, and permitted stride forms from that plan. They do not silently
cast or transpose unless policy selected an explicit copy path.

### Characters And Strings

Character handling combines element kind, declared or resolved length, scalar
versus array rank, and ABI byte storage. `String` is the stable semantic family,
but `numpy.str_` is only a Python-facing representation; fixed native character
storage may instead use exact byte buffers. Length and encoding constraints
must therefore survive semantic IR and policy completion.

### Derived Types

Derived-type identity is scoped and semantic. Generated wrappers keep native
objects opaque and use holders, accessors, and completed lifecycle policy
instead of mirroring an arbitrary native layout in Python. Field datatypes pass
through the same semantic and policy stages as ordinary variables.

Arrays of derived types remain unsupported unless the language-support matrix
states otherwise. A primitive scalar registry entry must never be fabricated
for a derived identity.

### Pointers And Allocatables

Pointer and allocatable arrays combine an element semantic dtype with descriptor
kind, association/allocation state, ownership, nullability, and release
responsibility. Policy completes those decisions before planning. Runtime
handles expose descriptor-backed operations, while generated code uses the
planned element dtype for validation and descriptor metadata.

A live zero-copy NumPy view can become stale after native deallocation,
reallocation, or pointer reassociation. Datatype matching does not solve that
lifetime boundary; see [Ownership Tracking](ownership-tracking.md).

### Callbacks

A callback datatype is a full prototype: argument types, result type, calling
convention, value/reference storage, rank, and mutability. It is not reducible
to a scalar function-pointer token. Semantic conversion resolves the prototype,
policy completes callback handoff and result behavior, and planning freezes the
native slots used by codegen.

## Policy And Planning Boundaries

Datatype facts answer questions such as “this is a rank-two `Float64` array.”
They do not answer:

- who owns it;
- whether it is borrowed, copied, moved, or aliased;
- whether native mutation is visible or discarded;
- whether an output is hidden and projected into the Python result;
- whether storage is stack, heap, or alias;
- whether destruction or descriptor release is required;
- whether a getter or setter is exposed.

Those decisions belong to post-IR policy completion. `WrapperPlanner` projects
the completed facts into typed transfer, result, field, module-variable, and
lifecycle plans. Backend generators dispatch from those records into named
mechanisms and must fail if a required datatype lowering is absent.

## Failure Rules

| Failure | Stage that should reject it |
| --- | --- |
| Compiler cannot measure a required target fact | probe service |
| Native declaration is syntactically unsupported | parser |
| Native fact cannot map to a stable semantic datatype | source-to-IR conversion |
| Datatype is known but unsafe or unsupported in its use-site context | policy completion |
| Completed datatype/policy combination has no plan representation | wrapper planner |
| Planned datatype has no backend mechanism | codegen checked dispatch |
| Runtime value has the wrong exact dtype, rank, layout, or mutability | generated binding validation |

No stage should silently replace a failed mapping with a nearby width, host
default, NumPy coercion, or different ownership path.

## Change Workflow And Evidence

When adding or changing a datatype:

1. Add parser coverage for every accepted source spelling and source location.
2. Add probe coverage when storage or kind depends on the compiler target.
3. Add or update `SemanticScalarSpec` only for stable semantic vocabulary.
4. Verify source-to-IR conversion records the resolved dtype and native
   provenance.
5. Complete use-site behavior in policy and add explicit blockers for
   unsupported combinations.
6. Extend wrapper-plan records only when existing transfer/result records
   cannot represent the completed behavior.
7. Add one backend catalogue entry or a specialized lowering mechanism.
8. Add generated-source assertions and an end-to-end runtime case when emitted
   behavior changes.
9. Update the semantic datatype reference, feature matrix, and this page when
   support boundaries change.

Primary evidence owners are:

| Concern | Tests |
| --- | --- |
| Target measurement | `tests/fortran/data_types/probes/` and `tests/c/probes/` |
| Semantic scalar catalogue and conversion | `tests/fortran/data_types/semantics/`, semantic conversion tests |
| Public contract factories | semantic `.pyi` contract tests |
| Backend scalar catalogue | `tests/fortran/data_types/codegen/` |
| Generated datatype report | `tests/fortran/data_types/pipeline/test_type_mapping_report.py` |
| Runtime scalar and array behavior | feature-local end-to-end datatype and array tests |

The report and registry tests should assert readable representative mappings,
not preserve obsolete public helpers or duplicate every internal dictionary as
an external API.
