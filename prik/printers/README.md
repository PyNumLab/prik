# Printers Package

This package serializes already-formed language representations into text. It
is the output-side counterpart of `../parsers/` and owns no semantic policy,
wrapper planning, cross-language orchestration, filenames, or build behavior.

| File | Owns |
| --- | --- |
| `c.py` | C translation-unit and header node serialization. |
| `fortran.py` | Fortran bridge node serialization and free-form line wrapping. |
| `pyi.py` | Semantic IR serialization as editable semantic `.pyi`. |

`../pipeline/wrapper.py` coordinates C and Fortran node generation, calls the
two native source printers, assigns stable wrapper filenames, and returns one
generated-wrapper result. `../pipeline/build.py` writes or compiles that
result.
