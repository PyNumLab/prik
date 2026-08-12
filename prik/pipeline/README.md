# Pipeline Package

This package coordinates complete workflows without taking ownership of
language semantics, policy rules, backend lowering, language printing, or
native compiler mechanisms.

| File | Owns |
| --- | --- |
| `preprocessing.py` | Compiler preprocessing recipes and source mappings. |
| `pyi.py` | Semantic `.pyi` loading, package assembly, and reference reconciliation. |
| `wrapper.py` | One completed-plan-to-rendered-wrapper generation workflow. |
| `build.py` | Generated-source output, native compilation, linking, and extension results. |

`WrapperGenerator` in `wrapper.py` completes plan-driven documentation,
validates the editable plan, invokes the C and Fortran node generators, prints
their results through `../printers/`, assigns stable filenames, and returns one
`GeneratedWrapper`. It does not write files or invoke a compiler.
