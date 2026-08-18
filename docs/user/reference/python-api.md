---
title: Python API Reference
audience: users, developers
prerequisites: installation
related: cli-commands.md, fortran-wrapper.md, ../../developer/packages/index.md
status: maintained
publication: draft
---

# Python API Reference

`prik` is a small facade. The root package exposes the installed version and
the three ways to build a wrapper — nothing else. Parser models, semantic
conversion, compiler probes, runtime handles, and plans are imported from the
package that owns them.

<!-- prik-doc-test: exact -->
```python
import prik

print(sorted(prik.__all__))
```

<!-- prik-doc-test-output -->
```text
['__version__', 'build_fortran_extension', 'build_pyi_extension', 'build_pyi_extension_from_manifest']
```

## Root API

| Symbol | Use it for |
| --- | --- |
| `__version__` | The installed PRIK distribution version. |
| `build_fortran_extension` | Build from Fortran source, plus optional native-only inputs. |
| `build_pyi_extension` | Build from semantic `.pyi` contracts, plus explicit native implementation inputs. |
| `build_pyi_extension_from_manifest` | Replay a saved `.pyi` build manifest, or generate its Makefile. |

## Building an extension

Every build entrypoint returns a `WrapperBuildResult`. Call `import_module()`
on it to load the extension without editing `sys.path`:

<!-- prik-doc-test: exact -->
```python
from pathlib import Path
from tempfile import TemporaryDirectory

from prik import build_fortran_extension

source = Path("tests/fortran/building_shared_library/end_to_end/fixtures/native/fruntime_abi_f90.f90")
with TemporaryDirectory() as output_dir:
    build = build_fortran_extension(source, output_dir=output_dir)
    print(build.module_name)
    print(type(build).__module__ + "." + type(build).__name__)
```

<!-- prik-doc-test-output -->
```text
fruntime_abi_f90
prik.pipeline.build.WrapperBuildResult
```

Import `WrapperBuildResult` and the native-build plan records from
`prik.pipeline.build` only when you need to inspect or construct them.

## Advanced package imports

Reach past the root facade when you need a single stage rather than a build.

| Need | Import from | Main entrypoints |
| --- | --- | --- |
| Fortran source facts and diagnostics | `prik.parsers.fortran` | `parse_fortran_file`, `parse_fortran_project`, `FortranParser`, parser models, `FortranParseError` |
| Raw semantic `.pyi` syntax | `prik.parsers.pyi` | `parse_pyi_text`, `parse_pyi_file` |
| Semantic conversion | `prik.semantics.fortran2ir`, `prik.semantics.pyi2ir` | Fortran conversion helpers, `convert_pyi_to_ir` |
| `.pyi` loading and stub emission | `prik.pipeline.pyi` | `pyi_*_to_semantic_module`, `emit_module_stubs` |
| Build records and results | `prik.pipeline.build` | `WrapperBuildResult`, `NativeBuildPlan`, `NativeCompilationUnit`, `NativePrebuiltArtifact`, `NativeLinkItem` |
| Target type probing | `prik.preprocessing.probes.fortran_types` | probe source, requirements, expressions, report and error types |
| Runtime descriptor handles | `prik.runtime.handles` | `NativeArrayHandleBase`, `AllocatableArray`, `PointerArray` |
| Semantic `.pyi` vocabulary | `prik.contracts` | scalar, array, ownership, and native-call contract markers |
| CLI implementation | `prik.cli` | `main()` — shell users should run `python3 -m prik` instead |

## Boundaries

- Root imports stay small and do not load parser or semantic implementation
  modules.
- A parser success is only a source fact. Semantic conversion, policy
  completion, planning, and generation are separate stages that can each
  reject input the parser accepted.
- The C frontend is inspection-only and is not part of the root API.

## Related pages

- [CLI Commands](cli-commands.md) — the same workflows from a shell.
- [Fortran Wrapper Reference](fortran-wrapper.md) — build options in depth.
- [Package guides](../../developer/packages/index.md) — module responsibilities
  and their focused tests.
