---
title: Python API Reference
audience: users, developers
prerequisites: installation
related: cli-commands.md, fortran-wrapper.md, ../../developer/packages/index.md
status: maintained
publication: draft
---

# Python API Reference

`prik` is a small normal-user facade. It exposes the installed version and the
three ways to build a wrapper. It does not re-export parser models, semantic
conversion, compiler probes, runtime handles, plans, or CLI implementation.
Import those advanced tools from the package that owns them.

```python
import prik

sorted(prik.__all__)
```

## Root API

| Symbol | Use it for |
| --- | --- |
| `__version__` | Read the installed PRIK distribution version. |
| `build_fortran_extension` | Build an extension from Fortran source plus optional native-only inputs. |
| `build_pyi_extension` | Build an extension from semantic `.pyi` contracts plus explicit native implementation inputs. |
| `build_pyi_extension_from_manifest` | Replay a saved semantic-`.pyi` build manifest or generate its Makefile. |

For normal builds, import directly from the root:

```python
from prik import build_fortran_extension

result = build_fortran_extension("solver.f90", output_dir="build/solver")
module = result.import_module()
```

The functions return `prik.pipeline.build.WrapperBuildResult`. Import result
models and native-build plan records from `prik.pipeline.build` only when you
need to inspect or construct those advanced values.

## Advanced Package Imports

| Need | Import from | Main entrypoints |
| --- | --- | --- |
| Fortran source facts and diagnostics | `prik.parsers.fortran` | `parse_fortran_file`, `parse_fortran_project`, `FortranParser`, parser models, `FortranParseError` |
| Raw semantic `.pyi` syntax | `prik.parsers.pyi` | `parse_pyi_text`, `parse_pyi_file` |
| Semantic conversion | `prik.semantics.fortran2ir` or `prik.semantics.pyi2ir` | Fortran conversion helpers or `convert_pyi_to_ir` |
| `.pyi` loading and stub emission | `prik.pipeline.pyi` | `pyi_*_to_semantic_module`, `emit_module_stubs` |
| Build records and results | `prik.pipeline.build` | `WrapperBuildResult`, `NativeBuildPlan`, `NativeCompilationUnit`, `NativePrebuiltArtifact`, `NativeLinkItem` |
| Target type probing | `prik.preprocessing.probes.fortran_types` | probe source, requirements, expressions, and report/error types |
| Runtime descriptor handles | `prik.runtime.handles` | `NativeArrayHandleBase`, `AllocatableArray`, `PointerArray` |
| Semantic `.pyi` vocabulary | `prik.contracts` | scalar, array, ownership, and native-call contract markers |
| CLI implementation | `prik.cli` | `main()`; shell users should run `python3 -m prik` instead |

The [Fortran wrapper reference](fortran-wrapper.md) documents the normal build
functions. The [package guides](../../developer/packages/index.md) explain
advanced module responsibilities and their focused tests.

## Current Boundaries

- Root imports are intentionally small and do not load parser or semantic
  implementation modules.
- A parser success is only a source fact. Semantic conversion, policy
  completion, planning, and generation are separate stages.
- The C-input frontend is deferred from the published workflow. Its internal
  parser package is not a root API.
