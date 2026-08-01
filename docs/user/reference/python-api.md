---
title: Python API Reference
audience: users, developers
prerequisites: installation
related: cli-commands.md, ../../developer/development-workflow.md
status: maintained
publication: draft
---

# Python API Reference

This page documents the checked public symbols exported from `prik.__all__`.
The names below are the supported import surface for callers that use prik as a
library.

```python
import prik

sorted(prik.__all__)
```

## Package version

| Symbol | Purpose |
| --- | --- |
| `__version__` | Installed PRIK distribution version, read from package metadata. |

`pyproject.toml` is the only file that declares the release version. The public
attribute does not maintain a second version constant:

```python
import prik

assert prik.__version__ == "0.1.0"
```

## CLI entrypoint

| Symbol | Purpose |
| --- | --- |
| `main` | Runs the `python3 -m prik` command-line interface. Prefer the CLI for shell workflows and the functions below for Python workflows. |

<!-- PRIK_C_DOCS_START
## C parser API
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Symbol | Purpose |
| &#45;&#45;- | &#45;&#45;- |
| `parse_c_file` | Parses one C source or header into a `CFile`. |
| `parse_c_project` | Parses multiple C files into a `CProject`. |
| `CFile` | Parsed C file model. |
| `CProject` | Parsed C project model. |
| `CParseError` | Error raised for C parse failures. |
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The parser APIs expect already-selected inputs. CLI-only features such as
language inference, directory expansion, command-line validation, and compiler
preprocessing option parsing live in the CLI layer.
PRIK_C_DOCS_END -->

## Fortran parser API

| Symbol | Purpose |
| --- | --- |
| `parse_fortran_file` | Parses one Fortran file into a `FortranFile`. |
| `parse_fortran_project` | Parses multiple Fortran files into a `FortranProject`. |
| `FortranFile` | Parsed Fortran file model. |
| `FortranProject` | Parsed Fortran project model. |
| `FortranModule` | Parsed module model. |
| `FortranSubmodule` | Parsed submodule model. |
| `FortranProgram` | Parsed program model. |
| `FortranBlockData` | Parsed block-data unit model. |
| `FortranDerivedType` | Parsed derived-type model. |
| `FortranInterface` | Parsed interface model. |
| `FortranProcedureSignature` | Parsed function or subroutine signature model. |
| `FortranArgument` | Parsed procedure argument model. |
| `FortranParseError` | Error raised for Fortran parse failures. |

## Semantic conversion API

| Symbol | Purpose |
| --- | --- |
| `fortran_file_to_semantic_modules` | Converts a parsed Fortran file to semantic module models. |
| `fortran_project_to_semantic_modules` | Converts a parsed Fortran project to semantic module models. |
| `fortran_module_to_semantic_module` | Converts one parsed Fortran module to one semantic module. |
| `collect_semantic_compile_time_requirements` | Collects semantic values that must be known at compile time. |
| `resolve_semantic_compile_time_values` | Resolves collected compile-time requirements. |

<!-- PRIK_C_DOCS_START
| `CToIRConverter` | Stateful C-to-semantic-IR converter. |
| `c_file_to_semantic_module` | Converts one parsed C file to one semantic module. |
| `c_file_to_semantic_modules` | Converts one parsed C file to semantic modules. |
| `c_project_to_semantic_module` | Converts a parsed C project to one semantic module. |
| `c_project_to_semantic_modules` | Converts a parsed C project to semantic modules. |
| `c_function_to_semantic_function` | Converts one parsed C function to a semantic function. |
| `c_parameter_to_semantic_argument` | Converts one parsed C parameter to a semantic argument. |
| `c_struct_to_semantic_class` | Converts one parsed C struct to a semantic class. |
| `c_type_to_semantic_type` | Converts one parsed C type to a semantic type. |
PRIK_C_DOCS_END -->

Semantic conversion is the boundary between parser models and wrapper-facing
contracts. Run the default wrapper build to complete policy and validate
whether the wrapper plan supports the contract.

## Semantic `.pyi` contract API

| Symbol | Purpose |
| --- | --- |
| `parse_pyi_text` | Parses semantic `.pyi` source text into Python AST. |
| `parse_pyi_file` | Loads and parses one semantic `.pyi` file into Python AST. |
| `convert_pyi_to_ir` | Converts parsed semantic `.pyi` AST to semantic IR. |
| `pyi_text_to_semantic_module` | Parses inline semantic `.pyi` text and converts it to semantic IR. |
| `pyi_file_to_semantic_module` | Converts one semantic `.pyi` file to semantic IR. |
| `pyi_paths_to_semantic_modules` | Converts semantic `.pyi` files or directories to semantic IR and reconciles imports. |

Editable `.pyi` files are a contract surface. User-private declarations in a
`.pyi` file are distinct from source-private Fortran declarations omitted from
generated stubs.

## Stub emission API

| Symbol | Purpose |
| --- | --- |
| `emit_module_stubs` | Emits semantic Python `.pyi` text from semantic module models. |
| `opaque_dependency_modules` | Computes opaque dependency modules needed for emitted stubs. |

## Native array handle API

| Symbol | Purpose |
| --- | --- |
| `NativeArrayHandleBase` | Common runtime base for generated native array descriptor handles. |
| `AllocatableArray` | Runtime object for a native allocatable array descriptor. |
| `PointerArray` | Runtime object for a native pointer array descriptor. |

Generated wrappers use these handle classes when an allocatable or pointer array
descriptor is exposed as a Python object. Users can test for these classes when
they need to distinguish descriptor handles from ordinary NumPy arrays. Borrowed
handles do not own native storage. Owned handles expose `close()` and `closed`;
their finalizer attempts generated owner-storage destruction at most once.

`Allocatable[T[...]]()` creates an owned, initially unallocated
`AllocatableArray`. `Pointer[T[...]]()` creates an owned, initially
unassociated `PointerArray`. The dtype and rank come from the annotation. On
the first writable descriptor call, the generated wrapper attaches
compiler-compatible persistent storage to the same handle. Closing an
allocatable handle also releases any allocation it still owns; closing a
pointer handle releases only its descriptor, not an associated target.

`p1.associate(p2)` makes `p1` refer to the same target as `p2`, or makes
`p1` unassociated when `p2` is unassociated. It replaces any current
association of `p1` without copying or deallocating target storage.

Owned writable handles carry a versioned record defined by prik's bundled
native binding support. Separately built prik extensions can accept the same
handle without linking to each other when their prik handle ABI and Fortran
compiler/runtime ABIs are compatible. Each receiving wrapper validates the
record's version, size, descriptor kind, dtype, and rank before direct
descriptor use.

These classes are array-only. Scalar `Allocatable[T]` and `Pointer[T]`
projections remain ordinary `T | None` values and never produce an
`AllocatableArray` or `PointerArray`.

`to_numpy()` returns `None` when the descriptor is currently unallocated or
unassociated. Otherwise, it returns a live NumPy view of the current allocation
or pointer target and never an automatic detached copy. Results must match the
handle's declared dtype and rank. Contiguous-view policy rejects non-contiguous
storage, while descriptor-view extraction can expose positive or negative
strides when generated standard descriptor support is available. Unsupported
descriptor extraction fails explicitly. Reallocation, deallocation, pointer
reassociation, or nullification may make an older view stale; accessing a stale
view is unsupported and may crash. Call `.copy()` explicitly when independent
storage is required, and call `to_numpy()` again to inspect current state.

When a generated wrapper accepts a handle for an ordinary `T[...]` argument, it
uses an internal native array-actual handoff rather than an implicit
`to_numpy()` call. Parameters annotated as `Allocatable[T[...]]` or
`Pointer[T[...]]` use descriptor handoff and require the matching handle class;
plain NumPy arrays are for ordinary array-data parameters.

## Wrapper build API

| Symbol | Purpose |
| --- | --- |
| `build_fortran_extension` | Builds a Python extension from semantic Fortran source inputs plus optional native-only sources, artifacts, compiler flags, include paths, libraries, and ordered link items. |
| `build_pyi_extension` | Builds a Python extension from semantic `.pyi` contracts plus explicit native artifacts. |
| `build_pyi_extension_from_manifest` | Replays a saved semantic `.pyi` wrapper build manifest, either building directly or regenerating `Makefile.prik`. |
| `WrapperBuildResult` | Result model returned by wrapper build functions. |
| `NativeBuildPlan` | Structured native implementation compile/link plan attached to a wrapper build result. |
| `NativeCompilationUnit` | Native source compilation unit and produced object recorded in a native build plan. |
| `NativePrebuiltArtifact` | Caller-supplied native object, archive, or shared library recorded in a native build plan. |
| `NativeLinkItem` | One ordered object, archive, shared library, named library, or linker argument in a native link plan. |

Fortran source wrapper builds own the normal source-to-extension workflow and
may augment their positional semantic sources with the same native compile and
link inputs used by contract builds. Semantic `.pyi` wrapper builds require at
least one explicit native implementation input such as native Fortran sources,
objects, libraries, or ordered link items. Inspect
`WrapperBuildResult.native_build_plan` when a caller needs the native
compilation units, produced objects, prebuilt artifacts, module/include
directories, library directories, or ordered native link items separately from
the semantic contract paths. Semantic `.pyi` build results also expose a
normalized replay `manifest`; Makefile mode writes that manifest to
`<out-dir>/prik-build.json` before generating `Makefile.prik`.

## Target type and NumPy helpers

| Symbol | Purpose |
| --- | --- |
| `FortranTypeProbeError` | Error raised for Fortran type probing failures. |
| `FortranTypeProbeReport` | Report model for Fortran type probing. |
| `build_fortran_type_probe_source` | Builds the source used to probe Fortran type properties. |
| `fortran_type_probe_expressions` | Produces expressions used by the Fortran type probe. |
| `probe_fortran_type_expressions` | Runs Fortran type probes for selected expressions. |
| `evaluate_fortran_type_requirements` | Evaluates semantic requirements against a Fortran type probe report. |
| `SEMANTIC_DTYPE_TO_NUMPY_DTYPE` | Default semantic dtype to NumPy dtype map. |
| `semantic_dtype_to_numpy_dtype` | Maps one semantic dtype to a NumPy dtype. |
| `semantic_dtype_to_numpy_dtype_map` | Returns a semantic dtype to NumPy dtype mapping. |
| `semantic_type_to_numpy_dtype` | Maps one semantic type to a NumPy dtype. |
| `numpy_dtype_expression` | Returns the generated expression for a NumPy dtype. |

These helpers are public because wrapper contracts need deterministic target
type and NumPy dtype mapping. The CLI type-probe flags are documented in
[CLI Commands Reference](cli-commands.md).

## Current boundaries

- Parser functions do not run CLI path expansion or command-line preprocessing
  validation.
- Generated module, function, class, and configuration references document the
  wrapper output surface; this page remains the maintained inventory for
  `prik.__all__`.

<!-- PRIK_C_DOCS_START
- Runtime wrapping of user-supplied C libraries is not part of the public
  wrapper-build API yet.
PRIK_C_DOCS_END -->
