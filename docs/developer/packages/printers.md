---
title: Printing Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, formed source representations
related: ../architecture.md, index.md, codegen.md, pipeline.md, parsers.md
status: maintained
publication: reviewed
---

# Printing Stage

## Purpose And Boundaries

`prik/printers/` is the representation-to-text boundary. C and Fortran
printers serialize backend nodes; the semantic `.pyi` printer serializes
semantic IR. Printers own formatting, escaping, indentation, declaration
order, and safe line wrapping. They do not invoke generators, choose filenames,
complete policy, or compile output.

## Local Structure

```text
prik/printers/
├── __init__.py
├── c.py
├── fortran.py
└── pyi.py
```

## What This Stage Receives And Produces

```text
formed C or Fortran node tree -> matching source printer -> native text
SemanticModule graph          -> PyiPrinter             -> editable .pyi
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/printers/__init__.py`](../../../prik/printers/__init__.py) | Re-exports `CSourcePrinter`, `FortranSourcePrinter`, `PyiPrinter`, and `emit_module()`. | The supported printer import surface changes. |
| [`prik/printers/c.py`](../../../prik/printers/c.py) | `CSourcePrinter` serializes C translation units, headers, declarations, functions, tables, and statements. | C syntax layout, escaping, or formatting changes. |
| [`prik/printers/fortran.py`](../../../prik/printers/fortran.py) | `FortranSourcePrinter` serializes bridge modules, interfaces, declarations, procedures, and free-form wrapped statements. | Fortran source layout or line-wrapping changes. |
| [`prik/printers/pyi.py`](../../../prik/printers/pyi.py) | `PyiPrinter`, `emit_module()`, and `_PyiEmissionContext` serialize semantic modules and scope imports, aliases, namespaces, and defaults for one emission. | Editable contract spelling or emission-context behavior changes. |

The fact that code generation calls a printer at the end of wrapper rendering
does not make printing part of codegen ownership. `pipeline/wrapper.py`
coordinates both distinct stages.

## Module Algorithms

### `c.py`: C nodes to C text

`CSourcePrinter.doprint()` is the public entrypoint. It freezes a supplied
`StageRecord`, dispatches it through the C node visitor, and returns text. A
`CModule` is rendered in compiler order: macro definitions, includes,
declarations, then functions. A `CHeader` adds its guard around includes and
prototypes.

The remaining visitors add C punctuation, indentation, signatures, and string
escaping to node-selected values. CPython method tables and module-property
support are serialized from their C nodes; no semantic model or wrapper plan is
consulted.

### `fortran.py`: Fortran nodes to free-form text

`FortranSourcePrinter.doprint()` likewise freezes a supplied node and renders
it through the Fortran visitor. A module is emitted in Fortran specification
and body order: uses, type definitions, interfaces, declarations, then
procedures and standalone procedures.

After rendering, the printer wraps overlong free-form lines at safe whitespace
or comma boundaries. It can continue string literals without changing their
value, never splits comments or doubled-quote escapes, and rejects an
unsplittable line that remains above the 132-column compiler-safe limit.

### `pyi.py`: semantic IR to an editable contract

`PyiPrinter.emit()` creates a fresh `_PyiEmissionContext` for every call. The
context records contract imports, aliases, public-name reservations, source
array defaults, and nested namespaces without mutating a reusable printer or
the semantic IR.

For a module, the printer first renders public classes, prototypes, variables,
functions, and overload sets into body sections. As visitors use contract
symbols, the shared context records imports; final import sections are then
placed before the body. Visitors preserve semantic native identity,
projections, storage, imports, and contract annotations, but do not complete
wrapper policy. `emit_module()` is the normal one-module convenience entrypoint
and still creates a fresh context.

## Run The Workflows

`c.py` constructs one small C module containing a `wrap_ping` function and
passes that already formed node tree to `CSourcePrinter`.

```bash
python3 prik/printers/c.py
```

```text
Rendered C binding source:
#include <Python.h>

static PyObject * wrap_ping(PyObject * self) {
    Py_INCREF(Py_None);
    return Py_None;
}
```

The include, C signature, indentation, and semicolons are printer work. The
example contains no semantic model or wrapper plan for the printer to inspect.

`fortran.py` constructs one bridge module with explicit `iso_c_binding` and
native-module uses, then prints its one bridge function.

```bash
python3 prik/printers/fortran.py
```

```text
Rendered Fortran bridge source:
module bind_c_printer_demo_wrapper
  use iso_c_binding, only: c_double
  use printer_demo, only: native_double_value => DOUBLE_VALUE
  implicit none
contains
  function bind_c_double_value(value) result(result) bind(c, name="DOUBLE_VALUE")
    real(c_double), value :: value
    real(c_double) :: result
    result = native_double_value(value)
  end function bind_c_double_value
end module bind_c_printer_demo_wrapper
```

The result preserves the declared use order and native alias, then applies
Fortran declaration, procedure, and indentation syntax to the supplied nodes.

`pyi.py` constructs one semantic `double_value` function with `Float64` types
and a native `DOUBLE_VALUE` identity, then emits one contract module.

```bash
python3 prik/printers/pyi.py
```

```text
Semantic module: printer_demo
from prik.contracts import Float64, bind

@bind("DOUBLE_VALUE")
def double_value(
    value: Float64
) -> Float64: ...
```

The native examples prove that punctuation and layout are added to already
formed nodes. The `.pyi` import and `@bind` line show that required contract
imports and native identity are derived from semantic IR without attaching
wrapper policy.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Native source printers](../../../tests/fortran/infrastructure/printers/test_source_printers.py) | C and Fortran serialization, rejection of wrapper plans, line wrapping, literal preservation, and unsplittable-line diagnostics. |
| [Semantic `.pyi` conversion smoke](../../../tests/fortran/semantic_pyi_format/pipeline/test_pyi_printer_conversion_smoke.py) | Emitted contract fixtures can be parsed and converted through the normal semantic-`.pyi` route. |
| [`.pyi` imports and packages](../../../tests/fortran/semantic_pyi_format/pipeline/test_pyi_printer_imports_and_packages.py) | Isolated emission state, imports, aliases, packages, name collisions, and opaque dependencies. |

## Change Routes

- Change formatting or serialization in the matching printer.
- If information is missing from a native node, add it in generation or the
  plan rather than consulting semantic IR from the printer.
- Change filenames or multi-source artifact order in the pipeline.

## Boundaries And Invariants

- Native source printers accept backend nodes, not semantic models.
- The `.pyi` printer accepts semantic IR, not wrapper plans.
- Each `.pyi` emission owns fresh context, so one failure cannot leak imports
  or reserved names into the next emission.

## Failure Boundary

Native printers report unsupported node types and, for Fortran, a line that
cannot be safely wrapped. The `.pyi` printer reports unsupported semantic
models or invalid contract-emission facts. Printers delegate missing node facts
to `codegen/` and missing semantic facts to earlier stages; they delegate file
names and writing to `pipeline/`. Start with the first invalid node or semantic
record, not the rendered text that exposes it.
