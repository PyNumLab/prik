---
title: Compiler Stage
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, native compiler toolchain
related: ../architecture.md, index.md, pipeline.md, runtime.md, ../workflows/quality-assurance.md
status: maintained
publication: draft
---

# Compiler Stage

## Purpose And Boundaries

`prik/compiler/` receives explicit source, object, include, library, flag, and
link inputs and turns them into native commands. It owns compiler-family
profiles, command construction and execution, and native-support installation.
It does not preprocess source, discover build order, probe datatype meaning,
or decide wrapper policy.

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
explicit ObjectFile and link inputs from prik.pipeline
  -> coherent compiler-family profile
  -> compile/link argv
  -> recorded or executed native process
  -> object file or shared extension
```

The selected Fortran compiler family supplies its matching C driver and
family-specific switches. The pipeline owns dependency-ready batches; the
compiler executes one request at a time.

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/compiler/compiler_profiles.py`](../../../prik/compiler/compiler_profiles.py) | Profile data and `fortran_compiler_family()` map a Fortran executable to its compatible C driver and flags. | Supporting a compiler family or changing family-specific build settings. |
| [`prik/compiler/objects.py`](../../../prik/compiler/objects.py) | `ObjectFile` is the immutable description of one source-to-object request. | A compilation input needs another explicit field or validation rule. |
| [`prik/compiler/compilers.py`](../../../prik/compiler/compilers.py) | `Compiler` builds, records, runs, and reports compile/link commands; `get_condaless_search_path()` isolates environment lookup. | Command spelling, subprocess execution, or command reporting changes. |
| [`prik/compiler/native_support.py`](../../../prik/compiler/native_support.py) | `install_native_support()` copies the bundled support payload and creates the NumPy API-version header. | The pipeline needs a different support-installation result; edit the payload itself under `runtime/native_support/`. |

## Execution Examples

Compiler-family selection:

```bash
python3 prik/compiler/compiler_profiles.py
```

```text
Selected family: gfortran
Compiler profile: GNU
Matching C executable: gcc
Fortran module-output flag: -J
```

One immutable compilation request:

```bash
python3 prik/compiler/objects.py
```

```text
Compile input: generated/bridge.f90 -> build/bridge.o
Language: fortran
Flags: ('-O2',)
Include directories: build/modules
```

Record-only command construction:

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

Bundled runtime installation:

```bash
python3 prik/compiler/native_support.py
```

```text
Installed directory: binding_support
Binding header present: True
NumPy version header present: True
```

Together these outputs prove that profile selection, request construction,
native command mechanics, and support installation remain separate operations.

## Tests And What They Prove

- [Compiler construction tests](../../../tests/fortran/building_shared_library/compiling/) cover profile selection and compile/link argv.
- [Build pipeline tests](../../../tests/fortran/building_shared_library/pipeline/) cover compiler handoff from a build plan.
- [Source build modes](../../../tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py) covers real source-build outcomes.
- [Runtime ABI compatibility](../../../tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py) covers installed support used by a compiled extension.

## Change Routes

- Change driver families or flags in `compiler_profiles.py`.
- Change compile/link argv or subprocess reporting in `compilers.py`.
- Change build order, parallel scheduling, manifests, or artifact names in
  `prik/pipeline/build.py`.
- Change native payload contents in `prik/runtime/native_support/`; change only
  their installation here.

## Invariants And Common Mistakes

- Never infer ownership, dtype, Python API shape, or wrapper support here.
- Never silently mix a selected Fortran driver with an unrelated C profile.
- Each invocation receives explicit inputs; hidden project discovery belongs
  upstream.
