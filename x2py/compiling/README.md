# Compiling Package

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
`x2py/pipeline/build.py`, where the canonical rendered wrapper artifacts are
available. The compiling package does not import or regenerate wrapper plans,
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
plan before compilation starts. Their object stages remain separate: the bridge
is compiled after native objects so it can consume native module files; the
header-only native support is compiled with the binding that includes it; and
linking runs only after every required object exists. Each compiler invocation receives its
source, target, flags, includes, and ordered link inputs explicitly.

For CLI wrapper builds, the selected input-language compiler executable is
used for native source compilation, generated bridge compilation, and the
input-language link command, matching the executable used earlier for
preprocessing and datatype measurement. Generated C bindings continue to use
the C executable from the selected compiler profile. Build-wide `-I` paths are
carried into native and generated-source object inputs; they are also recorded
in semantic `.pyi` build manifests so replay has the same compilation inputs.

Compilation must not decide semantic ownership, Python API shape, or wrapper
policy completion. Those decisions happen before generated sources reach this package.

## Tests And Docs

- Wrapper reference: `docs/user/reference/fortran-wrapper.md`
- Build-system docs: `docs/developer/build-system.md`
- Quality and static checks: `docs/developer/quality-assurance.md`
- Source navigation: `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`
- Pipeline map: `docs/maintainer/internal-architecture/pipeline-map.md`
- Build-mode tests: `tests/fortran/test_build_modes.py`
- Runtime ABI tests: `tests/fortran/test_runtime_abi.py`
