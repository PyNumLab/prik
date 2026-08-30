---
title: Python API Reference
audience: users
prerequisites: installation
related: cli-commands.md, ../language-support/c-support.md, ../../developer/packages/index.md
status: maintained
publication: reviewed
---

# Python API Reference

`prik` is a small facade. The root package exposes the installed version and
the four ways to build a wrapper — nothing else. Parser models, semantic
conversion, compiler probes, runtime handles, and plans are imported from the
package that owns them.

<!-- prik-doc-test: exact -->
```python
import prik

print(sorted(prik.__all__))
```

<!-- prik-doc-test-output -->
```text
['__version__', 'build_c_extension', 'build_fortran_extension', 'build_pyi_extension', 'build_pyi_extension_from_manifest']
```

## Root API

| Symbol | Use it for |
| --- | --- |
| `__version__` | The installed PRIK distribution version. |
| `build_c_extension` | Build C extensions from source within the documented support boundary. |
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

source = Path("tests/fortran/infrastructure/building/end_to_end/fixtures/native/fruntime_abi_f90.f90")
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

### Build a supported C source

Use `build_c_extension` for C source builds. The source must fit the current
[C Support](../language-support/c-support.md) contract; broader C declarations
are not adapted automatically.

```python
import numpy as np

from prik import build_c_extension

build = build_c_extension("native_math.c", output_dir="build")
native_math = build.import_module()
print(native_math.add(np.float64(3.0), np.float64(2.5)))
```

For an authored C semantic contract, use `build_pyi_extension` with
`native_language="c"` and `native_c_sources=[...]`. The [C Support
guide](../language-support/c-support.md#author-a-contract-for-pointers-and-arrays)
shows the complete contract and build.

## Advanced package imports

Reach past the root facade when you need a single stage rather than a build.

| Need | Import from | Main entrypoints |
| --- | --- | --- |
| Fortran source facts and diagnostics | `prik.parsers.fortran` | `parse_fortran_file`, `parse_fortran_project`, `FortranParser`, parser models, `FortranParseError` |
| C source facts and diagnostics | `prik.parsers.c` | `parse_c_file`, `parse_c_project`, `CParser`, parser models, `CParseError` |
| Raw semantic `.pyi` syntax | `prik.parsers.pyi` | `parse_pyi_text`, `parse_pyi_file` |
| Semantic conversion | `prik.semantics.fortran2ir`, `prik.semantics.pyi2ir` | Fortran conversion helpers, `convert_pyi_to_ir` |
| C semantic conversion | `prik.semantics.c2ir` | `CToIRConverter`, `c_file_to_semantic_module`, `c_file_to_semantic_modules` |
| `.pyi` loading and stub emission | `prik.pipeline.pyi` | `pyi_*_to_semantic_module`, `emit_module_stubs` |
| Build records and results | `prik.pipeline.build` | `WrapperBuildResult`, `NativeBuildPlan`, `NativeCompilationUnit`, `NativePrebuiltArtifact`, `NativeLinkItem` |
| IPython/Jupyter integration | `prik.jupyter` | `%load_ext prik.jupyter`, then `%%fortran`, `%%c`, or `%%pyi` |
| Target type probing | `prik.preprocessing.probes.fortran_types` | probe source, requirements, expressions, report and error types |
| C target type probing | `prik.preprocessing.probes.c_types` | `probe_c_standard_types`, `probe_c_standard_types_cached`, and C probe records/error type |
| Runtime descriptor handles | `prik.runtime.handles` | `NativeArrayHandleBase`, `AllocatableArray`, `PointerArray` |
| Semantic `.pyi` vocabulary | `prik.contracts` | scalar, array, ownership, and native-call contract markers |
| CLI implementation | `prik.cli` | `main()` — shell users should run `python3 -m prik` instead |

## Boundaries

- Root imports stay small and do not load parser or semantic implementation
  modules.
- A parser success is only a source fact. Semantic conversion, policy
  completion, planning, and generation are separate stages that can each
  reject input the parser accepted.
- C source builds are limited to the documented supported subset recorded in
  [C Support](../language-support/c-support.md#what-is-supported). Other
  parser-accepted C forms fail before wrapper planning rather than falling back
  to a generated ABI-conversion adapter.

## Related pages

- [CLI Commands](cli-commands.md) — the same workflows from a shell.
- [IPython and Jupyter Notebooks](../guide/notebooks.md) — compile source cells and publish their APIs in the session.
- [C Support](../language-support/c-support.md) — C source, contract, CLI, and
  Python workflows.
- [Editing `.pyi` Contracts](pyi-contracts/index.md) — supported API-shaping
  edits.
- [Package guides](../../developer/packages/index.md) — module responsibilities
  and their focused tests.
