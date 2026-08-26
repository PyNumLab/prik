---
title: Compiler Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, native compiler toolchain
related: ../architecture.md, index.md, pipeline.md, runtime.md, ../workflows/quality-assurance.md
status: maintained
publication: reviewed
---

# Compiler Stage

## Purpose And Boundaries

`prik/compiler/` turns explicit native-build requests into compiler commands.
It owns coherent compiler-family profiles, command construction and execution,
and conditional installation of the bundled native support. It does not
preprocess source, discover build order, probe datatype meaning, or decide
wrapper policy.

## Local Structure

```text
prik/compiler/
├── compiler_profiles.py
├── objects.py
├── compilers.py
└── native_support.py
```

## What This Stage Receives And Produces

```text
selected Fortran executable -> compatible vendor profile and C driver
selected C executable       -> measured C-only vendor profile
explicit ObjectFile         -> compile argv -> object file
ordered objects + link args -> link argv    -> shared extension

generated imports + output directory -> conditional native-support installation
```

The pipeline supplies dependency-ready batches and decides when native support
is needed. This component executes one explicit request at a time. Selecting a
Fortran compiler identifies its compatible C driver and family-specific flags.
A mixed build may name that family's C executable explicitly so C probing and
C compilation use the same driver; a C executable from another family is
rejected. A C-only build selects its C driver directly and does not discover or
require a Fortran compiler.

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/compiler/compiler_profiles.py`](../../../prik/compiler/compiler_profiles.py) | Profile data and `fortran_compiler_family()` map a Fortran executable to its compatible C driver and flags. | Supporting a compiler family or changing family-specific build settings. |
| [`prik/compiler/objects.py`](../../../prik/compiler/objects.py) | `ObjectFile` is the immutable description of one source-to-object request. | A compilation input needs another explicit field or validation rule. |
| [`prik/compiler/compilers.py`](../../../prik/compiler/compilers.py) | `Compiler` builds, records, runs, and reports compile/link commands; `get_condaless_search_path()` isolates environment lookup. | Command spelling, subprocess execution, or command reporting changes. |
| [`prik/compiler/native_support.py`](../../../prik/compiler/native_support.py) | `install_native_support()` copies the bundled support payload and creates the NumPy API-version header. | The pipeline needs a different support-installation result; edit the payload itself under `runtime/native_support/`. |

## Module Algorithms

### `compiler_profiles.py`: select one coherent toolchain

`available_compilers` records the C and Fortran settings for each supported
vendor. While constructing those profiles, `_toolchain()` attaches the active
Python and NumPy include and link settings required for a CPython extension.

`fortran_compiler_family()` only classifies a Fortran executable name: it
returns the identifying token, vendor profile, and matching C executable name.
It does not locate executables or run a command.
`Compiler.from_fortran_executable()` performs the lookup, first beside the
selected Fortran executable and then on the configured search path. A caller
may instead provide the exact C executable used by the preceding C stages; it
must identify the same vendor family. The constructor rejects an unknown
family, a missing executable, or a mixed-vendor pair.

`Compiler.from_c_executable()` is the C counterpart. It resolves the
selected C executable, identifies its vendor from the executable name or its
own version banner, and constructs a C-only profile. If the native build plan
also contains Fortran, the pipeline selects the Fortran-led paired profile
instead so the final link uses the required native-language driver.

### `objects.py`: carry one complete compilation request

`ObjectFile` is a frozen record for one source-to-object operation. It
normalizes paths and iterable fields, accepts only C or Fortran, and carries
the source, output path, flags, include and library directories, libraries,
and requested tools. Compilation order and dependency discovery remain in the
pipeline.

### `compilers.py`: construct and run explicit argv commands

`Compiler` loads a built-in profile, a JSON profile, or an installed profile.
Its `compile_object()` method creates the declared output directory, selects
the correct language driver, combines profile flags with the request's flags,
adds include paths, and adds the vendor-specific Fortran module-output flag.
It then records the exact argv and either executes it or returns it in
record-only mode.

`link_extension()` requires a nonempty ordered object list. It selects the
linker for the requested language, adds shared-library, profile, Python, and
library inputs, preserves the supplied object and link-argument order, and
returns the extension path. It does not reorder dependencies or search for
additional objects. `get_condaless_search_path()` is the isolated compiler
lookup helper for environments whose Conda paths should be ignored.

### `native_support.py`: install support only when generated imports need it

`install_native_support()` does nothing unless generated imports request
`binding_support` or one of its files. When needed, it locks the destination,
replaces the copied header-only payload, and writes `numpy_version.h` for the
active NumPy API level. The pipeline owns the generated imports and destination
directory; this module only performs that installation.

## Run The Workflows

Compiler-family selection:

`compiler_profiles.py` classifies an example `gfortran-13` executable name and
reads the matching built-in profile; it does not locate or invoke a compiler.

```bash
python3 prik/compiler/compiler_profiles.py
```

```text
Selected family: gfortran
Compiler profile: GNU
Matching C executable: gcc
Fortran module-output flag: -J
```

The vendor, C driver, and module-output flag are one coherent family choice.
They are profile facts that `Compiler.from_fortran_executable()` later uses for
real executable lookup.

One immutable compilation request:

`objects.py` constructs one `ObjectFile` for a generated Fortran bridge. It
does not create the source or invoke a compiler.

```bash
python3 prik/compiler/objects.py
```

```text
Compile input: generated/bridge.f90 -> build/bridge.o
Language: fortran
Flags: ('-O2',)
Include directories: build/modules
```

These fields are the complete explicit input for one compilation request; the
pipeline, not `ObjectFile`, decides when that request is compiled.

Record-only command construction:

`compilers.py` creates a temporary C request and a GNU compiler configured to
record commands without executing them.

```bash
python3 prik/compiler/compilers.py
```

```text
Compiler profile: GNU
Compile input: demo.c -> demo.o
Recorded without execution: True
Contains compile switch: True
Contains requested flag: True
Commands recorded: 1
```

The missing object file and recorded `-c` command show that command construction
is independently inspectable. The requested flag appears after profile flags,
and no native subprocess ran.

Bundled runtime installation:

`native_support.py` requests `binding_support/prik_binding.h` into a temporary
directory, which is enough to trigger conditional support installation.

```bash
python3 prik/compiler/native_support.py
```

```text
Installed directory: binding_support
Binding header present: True
NumPy version header present: True
```

The two `True` lines show that the payload and active-NumPy header were written
only after the generated import requested them. Together the examples cover
toolchain classification, explicit request representation, command creation,
and conditional support installation.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Compiler profile and command construction](../../../tests/fortran/infrastructure/building/compiling/test_compiler_verbose.py) | Coherent C/Fortran driver selection, explicit overrides, profile and user-flag order, optional-flag probing, record-only mode, and preserved link-input order. |
| [Generated-wrapper build handoff](../../../tests/fortran/infrastructure/building/pipeline/test_generated_wrapper_build.py) | Generated sources, conditional support installation, explicit C and Fortran object requests, and the final ordered link request passed from the pipeline. |
| [Source build modes](../../../tests/fortran/infrastructure/building/end_to_end/test_source_build_modes.py) | The selected source-build mode produces an importable native extension. |
| [Native-support surface](../../../tests/fortran/infrastructure/runtime/test_native_support.py) | The bundled payload remains header-only and exposes the small native binding API expected by generated sources. |
| [C build integration](../../../tests/c/infrastructure/building/pipeline/test_c_build_cli.py) | C-only builds use the selected C compiler; mixed-language inputs select the required Fortran link driver. |

## Change Routes

- Change driver families or flags in `compiler_profiles.py`.
- Change compile/link argv or subprocess reporting in `compilers.py`.
- Change build order, parallel scheduling, manifests, or artifact names in
  `prik/pipeline/build.py`.
- Change native payload contents in `prik/runtime/native_support/`; change only
  their installation here.

## Boundaries And Invariants

- Never infer ownership, dtype, Python API shape, or wrapper support here.
- Never silently mix a selected Fortran driver with an unrelated C profile.
- Each invocation receives explicit inputs; hidden project discovery belongs
  upstream.

## Failure Boundary

This component reports invalid object requests, unknown or incomplete
toolchains, unavailable compiler executables, and failed compiler processes.
It delegates dependency order, artifact selection, and build manifests to
`pipeline/`; generated imports and output locations are also pipeline facts.
Start with the selected profile or the first recorded argv whose inputs are
wrong, rather than with the extension that fails later.
