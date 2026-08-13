---
title: Code Generation Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, completed wrapper plan
related: ../architecture.md, index.md, planning.md, printers.md, pipeline.md
status: maintained
publication: draft
---

# Code Generation Package

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
│   ├── __init__.py
│   ├── binding.py
│   ├── python_surface.py
│   └── naming.py
└── fortran/
    ├── __init__.py
    └── bridge.py
```

## What This Stage Receives And Produces

```text
validated ModulePlan
  -> plan-driven public docstrings
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
| [`prik/codegen/c/__init__.py`](../../../prik/codegen/c/__init__.py) | Boundary for C/CPython binding mechanics. | Establishing a deliberate C-backend import API. |
| [`prik/codegen/c/binding.py`](../../../prik/codegen/c/binding.py) | `CBindingGenerator` lowers completed binding-plan views into CPython/NumPy C nodes. | A plan-selected Python boundary, lifecycle, error, or module mechanism changes. |
| [`prik/codegen/c/naming.py`](../../../prik/codegen/c/naming.py) | Binding-local generated names that should not become global naming policy. | A C-binding private symbol convention changes. |
| [`prik/codegen/c/python_surface.py`](../../../prik/codegen/c/python_surface.py) | `PythonSurfaceContext` and `PythonSurfaceEmitter` produce planned classes, holders, and module proxies embedded in the extension. | Generated Python facade behavior changes. |
| [`prik/codegen/fortran/__init__.py`](../../../prik/codegen/fortran/__init__.py) | Boundary for Fortran bridge mechanics. | Establishing a deliberate bridge-backend import API. |
| [`prik/codegen/fortran/bridge.py`](../../../prik/codegen/fortran/bridge.py) | `FortranBridgeGenerator` lowers bridge-plan views into `bind(C)` modules, accessors, descriptors, and native calls. | A plan-selected ABI declaration, conversion, call slot, or native bridge mechanism changes. |

Specialized emitter methods remain local because each makes the selected
mechanism auditable. Shared code must never reconstruct policy from datatype,
source `intent`, dotted shape, aliases, or local memory checks.

## Execution Examples

Typed nodes before printing:

```bash
python3 prik/codegen/nodes.py
```

```text
C node tree: CModule -> wrap_ping -> CReturn
Fortran node tree: FortranModule -> bind_c_ping -> FortranCall
Source text rendered: False
```

Primitive backend representations:

```bash
python3 prik/codegen/primitive_scalar_types.py
```

```text
Float64: C=double; Fortran=real(c_double); NumPy=numpy.float64
NumPy C macro: NPY_FLOAT64
Fresh editable node per lookup: True
```

Plan-driven docstrings:

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

The Python facade:

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

The binding and bridge files also have direct examples:

```bash
python3 prik/codegen/c/binding.py
```

The complete output is 22 lines. These exact selected lines identify the plan
and the native call inside the generated binding node tree:

```text
Native procedure: DOUBLE_VALUE
Native call slots: implicit:value
C module: binding_demo_wrapper
Header guard: BINDING_DEMO_WRAPPER_H
Header prototypes: wrap_double_value
Binding wrapper: wrap_double_value
...
  CExpressionStatement(expression=CodeExpression(text='result = bind_c_double_value(bound_value)'))
...
  CReturn(expression=CodeExpression(text='result_obj'))
```

```bash
python3 prik/codegen/fortran/bridge.py
```

The complete output is 17 lines. Its exact selected lines show the matching
slot and bridge call:

```text
Native procedure: DOUBLE_VALUE
Native call slots: implicit:value
Bridge module: bind_c_bridge_demo_wrapper
...
Bridge procedure: bind_c_double_value
Binding name: bind_c_double_value
Procedure kind: function
Result: result :: real(c_double)
...
  FortranAssignment(target='result', expression=CodeExpression(text='native_double_value(value)'))
Internal procedures: (none)
```

Together the outputs demonstrate that both backends lower one shared plan
without asking the other backend to decide policy.

## Tests And What They Prove

- [Codegen infrastructure](../../../tests/fortran/infrastructure/codegen/) covers nodes, generators, planning handoffs, and validation.
- [Feature-local codegen suites](../../../tests/fortran/) cover emitted mechanisms for each supported feature.
- `python3 tools/check_codegen_complexity.py` reports generator-maintainability recommendations for contributor review.

## Change Routes

- Add a mechanism to the narrow binding, bridge, or Python-surface emitter that
  owns it.
- Add a node only when the existing syntax vocabulary cannot represent the
  mechanism.
- Extend primitive lowering only for an established semantic scalar identity.
- If the change requires choosing ownership, storage, projection, setter
  exposure, or support, stop and add the missing upstream policy/plan fact.

## Invariants And Common Mistakes

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
