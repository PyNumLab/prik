---
title: Code Generation Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed wrapper plan
related: ../architecture.md, index.md, planning.md, printers.md, pipeline.md
status: maintained
publication: reviewed
---

# Code Generation Stage

## Purpose And Boundaries

`prik/codegen/` consumes a validated wrapper plan and produces typed C and
Fortran syntax nodes plus the planned Python facade source embedded in the
extension. It owns emitted mechanisms such as temporaries, conversions,
bridge bodies, module initialization, and class assembly. It must not complete
ownership, change wrapper support, print final native source, or compile it.

## Local Structure

```text
prik/codegen/
├── __init__.py
├── nodes.py
├── primitive_scalar_types.py
├── docstrings.py
├── overloads.py
├── checks.py
├── visitor.py
├── c/
│   ├── binding.py
│   ├── python_surface.py
│   └── naming.py
└── fortran/
    └── bridge.py
```

## What This Stage Receives And Produces

```text
editable ModulePlan
  -> plan-driven public docstrings
  -> WrapperGenerator freezes and validates the handoff
  -> CBindingGenerator + PythonSurfaceEmitter
  -> FortranBridgeGenerator
  -> typed C/Fortran nodes and Python facade text
  -> language printers
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/codegen/__init__.py`](../../../prik/codegen/__init__.py) | Re-exports generators, selected node records, scalar lowering, and generic codegen visitor support. | The supported backend API changes. |
| [`prik/codegen/nodes.py`](../../../prik/codegen/nodes.py) | `StageRecord`-based C and Fortran node families represent source before text serialization. | Existing nodes cannot express a plan-selected native construct. |
| [`prik/codegen/primitive_scalar_types.py`](../../../prik/codegen/primitive_scalar_types.py) | `PrimitiveScalarTypeRegistry` and `NumpyDtypeRegistry` map resolved semantic scalars to C, Fortran, NumPy, CFI, and CPython spellings. | An established semantic scalar needs a backend spelling or dtype projection. |
| [`prik/codegen/docstrings.py`](../../../prik/codegen/docstrings.py) | `WrapperDocstringBuilder` renders public Python documentation from a completed plan. | Plan-derived wrapper documentation changes. |
| [`prik/codegen/overloads.py`](../../../prik/codegen/overloads.py) | `OverloadPlanQueries` answers structural questions about completed overload plans. | Shared overload-plan inspection is needed without re-deciding overload policy. |
| [`prik/codegen/checks.py`](../../../prik/codegen/checks.py) | Shared code-generation validation and complexity-check support. | A codegen invariant or its repository gate changes. |
| [`prik/codegen/visitor.py`](../../../prik/codegen/visitor.py) | `ClassVisitor` and `UnsupportedWrapperCodegenNodeError` provide backend-node dispatch and explicit unsupported-node failure. | Generic codegen visitor behavior changes. |
| [`prik/codegen/c/binding.py`](../../../prik/codegen/c/binding.py) | `CBindingGenerator` lowers completed binding-plan views into CPython/NumPy C nodes. See [C Binding Lowering](codegen/c-binding.md). | A plan-selected Python boundary, lifecycle, error, or module mechanism changes. |
| [`prik/codegen/c/naming.py`](../../../prik/codegen/c/naming.py) | Binding-local generated names that should not become global naming policy. | A C-binding private symbol convention changes. |
| [`prik/codegen/c/python_surface.py`](../../../prik/codegen/c/python_surface.py) | `PythonSurfaceContext` and `PythonSurfaceEmitter` produce planned classes, holders, and module proxies embedded in the extension. | Generated Python facade behavior changes. |
| [`prik/codegen/fortran/bridge.py`](../../../prik/codegen/fortran/bridge.py) | `FortranBridgeGenerator` lowers bridge-plan views into Fortran modules with `bind(C)` entrypoints, accessors, descriptors, and native calls. See [Fortran Bridge Lowering](codegen/fortran-bridge.md). | A plan-selected ABI declaration, conversion, call slot, or native bridge mechanism changes. |

Specialized emitter methods remain local because each makes the selected
mechanism auditable. Shared code must never reconstruct policy from datatype,
source `intent`, dotted shape, aliases, or local memory checks.

## Module Algorithms

### Generation handoff: document, freeze, validate, lower

The canonical route begins in `pipeline/wrapper.py`, at
`WrapperGenerator.generate()`. It fills plan-derived docstrings while the
`ModulePlan` remains editable, freezes that exact graph, validates its
cross-backend consistency, and asks the specialized lowerers to preflight their
selected primitive mechanisms before producing nodes for `printers/`.

`codegen/` owns the presentation and lowering work in that sequence. It does
not own plan freezing, policy completion, source-file writing, or compilation.

### `nodes.py`, `visitor.py`, and scalar spelling

`nodes.py` defines the editable C and Fortran syntax vocabulary passed to
printers: modules, includes and declarations, functions and procedures,
control flow, calls, assignments, interfaces, types, and raw leaf
expressions. A node adds a representable language construct; it does not
choose whether the construct is safe or required.

`ClassVisitor` dispatches a node to the nearest `_visit_<ClassName>` method.
Missing handlers raise `UnsupportedWrapperCodegenNodeError`, which makes an
unimplemented lowering case explicit rather than silently emitting a nearby
form.

`PrimitiveScalarTypeRegistry.type_for()` and
`NumpyDtypeRegistry.expression_for()` provide C, Fortran, NumPy, CPython, and
descriptor spellings for already-resolved semantic scalars. Registry lookups
fail for unknown names, and scalar lookup returns a fresh editable node.

### `docstrings.py` and `overloads.py`: plan readers

`WrapperDocstringBuilder.render()` fills only unset documentation fields on a
plan. It renders child callables and fields before their class and namespace
summaries, while preserving an explicitly supplied string, including `""`.
It presents completed signatures, shapes, optionality, results, and errors; it
does not derive new wrapper behavior.

`OverloadPlanQueries` exposes the structural facts already fixed in an
`OverloadPlan`, such as the visible passed-object receiver. It is shared
inspection, not overload matching or dispatch policy.

### Specialized lowerings

The C binding and Fortran bridge lower separate, completed views of the same
plan. Their algorithms, source-printing examples, and failure boundaries are
described in [C Binding Lowering](codegen/c-binding.md) and [Fortran Bridge
Lowering](codegen/fortran-bridge.md). Neither page assigns policy completion to
code generation.

### `checks.py`: maintainability recommendations

`check_codegen_package()` and `check_codegen_paths()` inspect generator,
printer, and wrapper-orchestration Python for focused methods, explicit
visitor dispatch, registries, and forbidden printer calls. The command reports
maintainability recommendations for review; behavior, ABI, and safety tests
remain the enforcing evidence.

## Run The Workflows

Typed nodes before printing:

`nodes.py` constructs one minimal C module and one minimal Fortran module,
each with a single typed body node. It does not call a printer.

```bash
python3 prik/codegen/nodes.py
```

```text
C node tree: CModule -> wrap_ping -> CReturn
Fortran node tree: FortranModule -> bind_c_ping -> FortranCall
Source text rendered: False
```

The two paths name node classes rather than source text, confirming that this
layer has formed a language representation but has not yet formatted it.

Primitive backend representations:

`primitive_scalar_types.py` looks up `Float64` twice and asks the scalar and
NumPy catalogues for its selected spellings.

```bash
python3 prik/codegen/primitive_scalar_types.py
```

```text
Float64: C=double; Fortran=real(c_double); NumPy=numpy.float64
NumPy C macro: NPY_FLOAT64
Fresh editable node per lookup: True
```

The first two lines connect one semantic identity to C, Fortran, NumPy, and
NumPy-C spellings. `True` confirms that callers receive fresh editable nodes
instead of sharing mutable syntax objects.

Plan-driven docstrings:

`docstrings.py` constructs one scalar semantic function, completes policy,
projects its plan, and fills the function's unset binding docstring.

```bash
python3 prik/codegen/docstrings.py
```

```text
double_value(value) -> float64

Parameters
----------
value : float64

Returns
-------
result : float64

Raises
------
TypeError
    If an argument has an incompatible Python type or dtype.
```

The signature, sections, and `TypeError` all come from completed plan facts;
the formatter does not infer a new calling rule.

The Python facade:

`python_surface.py` constructs a planned opaque `State` class with an absent
constructor and emits its small embedded Python facade.

```bash
python3 prik/codegen/c/python_surface.py
```

```text
Rendered Python facade:
_prik_unset = object()

_prik_ops_state = {}
class State:
    'Opaque native state.'
    __slots__ = ('_prik_capsule', '_prik_owner', '_prik_ops', '_prik_origin')
    def __new__(cls, *args, **kwargs):
        'Construction is disabled.'
        raise TypeError('State objects come from native code.')
def _prik_wrap_State(capsule, owner=None, ops=None, origin='direct'):
    ...
```

The slots, rejected constructor, and wrapper helper are generated from that
class plan. They show the planned Python surface without selecting its native
lifecycle policy.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Codegen infrastructure](../../../tests/fortran/infrastructure/codegen/test_binding.py) | C binding nodes, module assembly, source-independent lowering, and selected validation paths. |
| [Plan handoff and generated wrappers](../../../tests/fortran/infrastructure/pipeline/test_wrapper_generator.py) | Docstring rendering, plan freezing, cross-backend validation, node generation, and rendered-wrapper assembly. |
| [Primitive scalar lowering](../../../tests/fortran/data_types/codegen/test_primitive_scalar_type_catalogue.py) | Scalar spelling catalogue and exact C, Fortran, NumPy, and result representation selection. |
| [Array lowering](../../../tests/fortran/arrays/codegen/test_array_buffer_lowering.py) | Planned buffer handoff and emitted binding/bridge operations. |
| [Derived-type lowering](../../../tests/fortran/derived_types/codegen/test_derived_lowering.py) | Plan-selected native object, lifecycle, and bridge/binding mechanisms. |
| [Codegen review command](../../../tests/tools/test_check_codegen_complexity_cli.py) | The maintainability recommendation command and its command-line behavior. |

## Change Routes

- Add a mechanism to the narrow binding, bridge, or Python-surface emitter that
  owns it.
- Add a node only when the existing syntax vocabulary cannot represent the
  mechanism.
- Extend primitive lowering only for an established semantic scalar identity.
- If the change requires choosing ownership, storage, projection, setter
  exposure, or support, stop and add the missing upstream policy/plan fact.

## Boundaries And Invariants

- Generators dispatch from completed plan actions; no datatype/intent fallback
  may silently choose behavior.
- `WrapperDocstringBuilder` renders the plan and is not imported by planning.
- Large specialized emitters are acceptable when methods remain focused and
  policy-free.

Use one repeatable lowering sequence for every datatype family:

1. Validate the completed object kind and action combination.
2. Binding generation lowers Python extraction or result construction.
3. Bridge generation lowers ABI declarations, representation conversion,
   ordered native call slots, and native result production.
4. Function orchestration applies status handling and planned lifecycle
   actions before aggregating Python results.
5. Printers serialize the formed nodes without revisiting the plan's policy.

A new datatype should extend completed policy and one transfer/result shape,
then add one named validator and one named lowering method per affected
backend. It should not create a parallel module/function plan hierarchy or add
datatype branching to generic traversal.

## Failure Boundary

This stage reports an unsupported completed plan action, missing visitor
handler, unavailable backend spelling, inconsistent frozen plan, or unplanned
backend mechanism. It delegates ownership, lifetime, public projection, and
support decisions to `policy/` and `planning/`; it delegates source formatting
to `printers/` and build execution to `pipeline/` and `compiler/`. Start with
the first invalid plan record or unsupported lowering action, not the rendered
source or compiler error that follows.
