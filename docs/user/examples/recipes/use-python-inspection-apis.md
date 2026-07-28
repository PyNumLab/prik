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

<!-- x2py-doc-test: exact -->
```python
from x2py import parse_fortran_file

parsed = parse_fortran_file(
    "subroutine ping(n)\n"
    "  integer, intent(in) :: n\n"
    "end subroutine ping\n",
    filename="inline.f90",
)

print(parsed.procedures[0].name)
```

Expected output:

<!-- x2py-doc-test-output -->
```text
ping
```

<!-- X2PY_C_DOCS_START
## Parse Inline C
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: exact -->
<!-- X2PY_C_DOCS_START
```python
from x2py import parse_c_file

parsed = parse_c_file("int add(int a, int b);", filename="inline.h")

print([function.name for function in parsed.functions])
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Expected output:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test-output -->
<!-- X2PY_C_DOCS_START
```text
['add']
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
## Convert C To Semantic IR
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test: exact -->
<!-- X2PY_C_DOCS_START
```python
from x2py import (
    c_file_to_semantic_modules,
    emit_module_stubs,
    parse_c_file,
)

parsed = parse_c_file("int add(int a, int b);", filename="inline.h")
modules = c_file_to_semantic_modules(parsed)

print(emit_module_stubs(modules)["inline"])
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
Expected output:
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_DISABLED: x2py-doc-test-output -->
<!-- X2PY_C_DOCS_START
```text
def add(
    a: Int,
    b: Int
) -> Int: ...
```
X2PY_C_DOCS_END -->

## Notes

- Use the CLI when project headers, macros, include directories, or compiler
  target flags matter.
- Use these APIs when your test already owns a small source string or parsed
  fixture.
