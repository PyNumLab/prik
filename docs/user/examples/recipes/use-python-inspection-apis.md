---
title: Use Python Inspection APIs
audience: users, developers
prerequisites: installation
related: ../../reference/python-api.md, ../../reference/semantic-ir.md
status: maintained
publication: draft
---

# Use Python Inspection APIs

Use this recipe when tests or tools need to inspect source declarations without
going through the CLI preprocessing path.

Direct parser APIs accept controlled source strings and paths. They do not run
the shared CLI compiler preprocessing pipeline.

## Parse Inline Fortran

<!-- prik-doc-test: exact -->
```python
from prik.parsers.fortran import parse_fortran_file

parsed = parse_fortran_file(
    "subroutine ping(n)\n"
    "  integer, intent(in) :: n\n"
    "end subroutine ping\n",
    filename="inline.f90",
)

print(parsed.procedures[0].name)
```

Expected output:

<!-- prik-doc-test-output -->
```text
ping
```

<!-- PRIK_C_DOCS_START
## Parse Inline C
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact -->
<!-- PRIK_C_DOCS_START
```python
from prik.parsers.c import parse_c_file

parsed = parse_c_file("int add(int a, int b);", filename="inline.h")

print([function.name for function in parsed.functions])
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Expected output:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
```text
['add']
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
## Convert C To Semantic IR
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test: exact -->
<!-- PRIK_C_DOCS_START
```python
from prik.parsers.c import parse_c_file
from prik.printers import emit_module
from prik.semantics.c2ir import c_file_to_semantic_modules

parsed = parse_c_file("int add(int a, int b);", filename="inline.h")
modules = c_file_to_semantic_modules(parsed)

print(emit_module_stubs(modules)["inline"])
```
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
Expected output:
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_DISABLED: prik-doc-test-output -->
<!-- PRIK_C_DOCS_START
```text
def add(
    a: Int,
    b: Int
) -> Int: ...
```
PRIK_C_DOCS_END -->

## Notes

- Use the CLI when project headers, macros, include directories, or compiler
  target flags matter.
- Use these APIs when your test already owns a small source string or parsed
  fixture.
