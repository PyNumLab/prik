---
title: Printers Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, formed source representations
related: ../architecture.md, index.md, codegen.md, pipeline.md, parsers.md
status: maintained
publication: draft
---

# Printers Package

## Purpose And Boundaries

`prik/printers/` is the representation-to-text boundary. C and Fortran
printers serialize backend nodes; the semantic `.pyi` printer serializes
semantic IR. Printers own formatting, escaping, indentation, declaration
order, and safe line wrapping. They do not invoke generators, choose filenames,
complete policy, or compile output.

## Local Structure

```text
prik/printers/
├── c.py
├── fortran.py
└── pyi.py
```

## Internal Workflow

```text
formed C or Fortran node tree -> matching source printer -> native text
SemanticModule graph          -> PyiPrinter             -> editable .pyi
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `c.py` | `CSourcePrinter` | Serializes C translation units, headers, declarations, functions, tables, and statements. |
| `fortran.py` | `FortranSourcePrinter` | Serializes bridge modules, interfaces, declarations, procedures, and statements with free-form line wrapping. |
| `pyi.py` | `PyiPrinter`, `emit_module()`, `_PyiEmissionContext` | Serializes semantic modules and scopes imports, aliases, class names, namespaces, and default order for one emission. |

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

## Tests

- [Printer infrastructure](../../../tests/fortran/infrastructure/printers/)
- [Semantic `.pyi` round trips](../../../tests/fortran/semantic_pyi_format/)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Change formatting or serialization in the matching printer.
- If information is missing from a native node, add it in generation or the
  plan rather than consulting semantic IR from the printer.
- Change filenames or multi-source artifact order in the pipeline.

## Invariants And Common Mistakes

- Native source printers accept backend nodes, not semantic models.
- The `.pyi` printer accepts semantic IR, not wrapper plans.
- Emission contexts are per-operation and restored safely after failures.
