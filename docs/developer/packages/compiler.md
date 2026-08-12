---
title: Compiler Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, native compiler toolchain
related: ../architecture.md, index.md, pipeline.md, runtime.md, ../workflows/quality-assurance.md
status: maintained
publication: draft
---

# Compiler Package

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

## Internal Workflow

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

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `compiler_profiles.py` | compiler profile records, `fortran_compiler_family()` | Resolves GNU, Intel, LLVM, NVIDIA, or PGI language families and matching drivers. |
| `objects.py` | `ObjectFile` | Immutable input for one source-to-object command. |
| `compilers.py` | `Compiler` | Constructs, records, executes, and reports native compile/link commands. |
| `native_support.py` | `install_native_support()` | Installs the bundled header runtime and NumPy API-version header into a generated wrapper directory. |

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

## Tests

- [Compiler construction tests](../../../tests/fortran/building_shared_library/compiling/)
- [Build pipeline tests](../../../tests/fortran/building_shared_library/pipeline/)
- [Source build modes](../../../tests/fortran/building_shared_library/end_to_end/test_source_build_modes.py)
- [Runtime ABI compatibility](../../../tests/fortran/building_shared_library/end_to_end/test_runtime_compatibility.py)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

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
