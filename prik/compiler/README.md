# Compiler Package

This package owns native compiler command construction, compile objects,
generated wrapper compilation, native support installation, and shared-library
linking.

## Entry Points

| File | Owns |
| --- | --- |
| `objects.py` | Explicit source-to-object compilation inputs. |
| `compilers.py` | Compiler command execution and tool lookup helpers. |
| `compiler_profiles.py` | Built-in vendor compiler profiles and Python-link settings. |
| `native_support.py` | Writing the header-only native binding support. |

Generated-wrapper object assembly and shared-library orchestration live in
`prik/pipeline/build.py`, where the canonical rendered wrapper artifacts are
available. The compiler package does not import or regenerate wrapper plans,
infer semantic policy, or traverse an implicit dependency graph.

## Pipeline Position

```text
native source files
  -> native object files
generated Fortran bridge
  -> bridge object files
generated C/CPython binding and its header-only native support
  -> binding object files
all explicit object files and link inputs
  -> linked Python extension
```

The bridge and binding sources are rendered together from one completed wrapper
plan before compilation starts. Build orchestration derives module and
submodule dependencies for wrapped sources and compiles every dependency-ready
batch concurrently. The independent generated binding can overlap native
compilation; the bridge waits for all native objects so it can consume native
module files. The header-only native support is compiled with the binding that
includes it, and linking starts only after every required object exists. The
available CPU count is the default process limit and `--jobs` can reduce it.
Each compiler invocation receives its source, target, flags, includes, and
ordered link inputs explicitly.

For CLI wrapper builds, the selected input-language compiler executable
determines one coherent vendor profile. The exact executable is used for native
source compilation, generated bridge compilation, and the input-language link
command, matching the executable used earlier for preprocessing and datatype
measurement. Generated C bindings use the matching C executable from that same
profile:

| Selected Fortran family | Binding C family |
| --- | --- |
| GNU `gfortran` | GNU `gcc` |
| Intel `ifx` or `ifort` | Intel `icx` |
| LLVM `flang` | LLVM `clang` |
| NVIDIA `nvfortran` | NVIDIA `nvc` |
| Legacy PGI `pgfortran` | PGI `pgcc` |

Versioned and target-prefixed executable names retain their corresponding
prefix or version when a matching sibling C executable exists. Selection fails
when the Fortran family is unknown or its matching C compiler cannot be found;
it must not silently combine the selected Fortran compiler with GNU C flags or
`gcc`. The active Python interpreter contributes its headers, library inputs,
and extension suffix, but not the compiler-specific C flags with which that
interpreter happened to be built. Binding compile flags come from the selected
vendor profile. When the interpreter's public `pyconfig.h` delegates to a
target-qualified multiarch header, its advertised include root is added
explicitly so a non-system vendor C compiler resolves that header without
borrowing the interpreter's original compiler command. Build-wide `-I` paths
are carried into native and
generated-source object inputs; they are also recorded in semantic `.pyi` build
manifests so replay has the same compilation inputs.

The maintained Linux CI evidence pins IFX/ICX 2026.1.1 and Flang/Clang 22.1.8
and executes the same profile checks and strict eight-node runtime smoke for
both. These are reproducible evidence versions, not claimed compiler-family
minimums. The rootless Intel CI environment installs the separate
`ifx_linux-64` and `dpcpp_linux-64` compiler packages so both required drivers
are present.

Compilation must not decide semantic ownership, Python API shape, or wrapper
policy completion. Those decisions happen before generated sources reach this package.

## Tests And Docs

- Wrapper reference: `docs/user/reference/fortran-wrapper.md`
- Compiler package guide: `docs/developer/packages/compiler.md`
- Pipeline package guide: `docs/developer/packages/pipeline.md`
- Quality and static checks: `docs/developer/workflows/quality-assurance.md`
- Source navigation: `docs/developer/codebase-map.md`, `docs/developer/feature-to-code-map.md`
- Build-mode tests: `tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py`
- Runtime ABI tests: `tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py`
