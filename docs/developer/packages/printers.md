---
title: Printing Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, formed source representations
related: ../architecture.md, index.md, codegen.md, pipeline.md, parsers.md
status: maintained
publication: draft
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

## Execution Examples

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
formed nodes. The `.pyi` example proves that required contract imports and
native identity are derived without attaching wrapper policy.

## Tests And What They Prove

- [Printer infrastructure](../../../tests/fortran/infrastructure/printers/) covers native syntax serialization and formatting.
- [Semantic `.pyi` round trips](../../../tests/fortran/semantic_pyi_format/) cover contract emission and re-parsing.

## Change Routes

- Change formatting or serialization in the matching printer.
- If information is missing from a native node, add it in generation or the
  plan rather than consulting semantic IR from the printer.
- Change filenames or multi-source artifact order in the pipeline.

## Invariants And Common Mistakes

- Native source printers accept backend nodes, not semantic models.
- The `.pyi` printer accepts semantic IR, not wrapper plans.
- Emission contexts are per-operation and restored safely after failures.
