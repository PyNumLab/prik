# Preprocessing Package

This package owns operations performed before C, Fortran, or semantic
conversion parses declarations. It prepares source text, preserves provenance,
expands native includes, and measures compiler-dependent target facts.

## Entry Points

| File or package | Owns |
| --- | --- |
| `source.py` | Compiler-backed C/Fortran expansion, invocation configuration, line-marker provenance, dependencies, macros, and preprocessing recipes. |
| `c.py` | Safe raw C directive and include metadata collected before C grammar parsing. |
| `fortran.py` | Native Fortran `INCLUDE` expansion after compiler preprocessing. |
| `probes/c_types.py` | Compiler-derived C target ABI facts and reusable cache reports. |
| `probes/fortran_types.py` | Compiler-derived Fortran kind/storage facts and reusable cache reports. |

Import the shared public preprocessing API from `prik.preprocessing`. Import a
language-specific raw metadata or probe API from its canonical child module.
The previous pipeline-local, parser-local, and top-level probe paths are not
retained.

## Boundary

```text
compiler service
  -> source preprocessing and target probes
  -> parser-native facts
  -> semantic IR
```

This package does not parse declarations, construct semantic IR, decide
ownership or wrapper support, render wrapper sources, or compile a completed
extension. `prik.compiler` supplies reusable compiler mechanisms;
`prik.pipeline` coordinates workflows that consume preprocessing results.

## Tests And Docs

- `tests/c/preprocessing/`
- `tests/c/probes/`
- `tests/fortran/source_preprocessing/preprocessing/`
- `tests/fortran/data_types/probes/`
- `docs/developer/compiler-preprocessing.md`
- `docs/maintainer/internal-architecture/type-system.md`
- `docs/developer/source-map.md`
- `docs/developer/feature-to-code-map.md`
