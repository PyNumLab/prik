# Pipeline Package

This package coordinates complete workflows without taking ownership of
language semantics, policy rules, backend lowering, language printing, or
native compiler mechanisms.

| File | Owns |
| --- | --- |
| `pyi.py` | Semantic `.pyi` loading, package assembly, and reference reconciliation. |
| `type_mapping_report.py` | Compiler-target facts converted through semantic IR and backend NumPy projection into inspection Markdown. |
| `wrapper.py` | One completed-plan-to-rendered-wrapper generation workflow. |
| `build.py` | Generated-source output, native compilation, linking, and extension results. |

`WrapperGenerator` in `wrapper.py` completes plan-driven documentation,
validates the editable plan, invokes the C and Fortran node generators, prints
their results through `../printers/`, assigns stable filenames, and returns one
`GeneratedWrapper`. It does not write files or invoke a compiler.

Source preparation and target measurement live in `../preprocessing/`.
Reusable compiler execution, compile objects, and linking live in
`../compiler/`. This package imports those services only while coordinating a
complete workflow.

For cross-stage navigation, see `docs/developer/source-map.md` and
`docs/developer/feature-to-code-map.md`. The canonical package reference is
`docs/developer/packages/pipeline.md`.
