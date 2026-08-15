---
title: Pipeline Component
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, architecture component guides for participating stages
related: ../architecture.md, index.md, compiler.md, planning.md, codegen.md, printers.md
status: maintained
publication: reviewed
---

# Pipeline Component

## Purpose And Boundaries

`prik/pipeline/` coordinates complete build and inspection workflows across
established stage boundaries. It owns public build requests, artifact layout,
source writing, progress, and result records. It does not decide source
meaning, wrapper policy, emitted mechanisms, text formatting, or compiler
commands.

## A Source Build Through This Component

The source-first public entrypoint is `build_fortran_extension`. It delegates
each transformation to its owner, then carries the resulting objects forward:

```text
Fortran source
  -> preprocessing, parsing, and semantic conversion
  -> policy completion
  -> WrapperPlanner
  -> WrapperGenerator
  -> GeneratedWrapper: rendered C, optional Fortran, and header payloads in memory
  -> build.py: files, NativeBuildPlan, compiler execution, and linking
  -> WrapperBuildResult
  -> import_module(): imported extension
```

A contract-first build enters through `build_pyi_extension`. Its entry `.pyi`
contract supplies the public API and explicit native inputs supply the
implementation; after semantic modules are assembled, it shares the same
policy, planning, generation, output, and build path. The
`type_mapping_report.py` workflow is separate: it inspects target and semantic
datatype facts without creating a wrapper.

## Local Structure

```text
prik/pipeline/
├── pyi.py
├── type_mapping_report.py
├── wrapper.py
└── build.py
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/pipeline/pyi.py`](../../../prik/pipeline/pyi.py) | `pyi_*_to_semantic_module()` loads text, files, or path sets into semantic modules. `emit_module_stubs()` completes copied modules and renders `.pyi` stubs. | Contract loading, external-type reconciliation, per-operation cache behavior, or stub output. |
| [`prik/pipeline/type_mapping_report.py`](../../../prik/pipeline/type_mapping_report.py) | Converts compiler probe facts through semantic conversion and backend dtype projection into a Markdown report. | Datatype-report content or its cross-stage evidence. |
| [`prik/pipeline/wrapper.py`](../../../prik/pipeline/wrapper.py) | `WrapperGenerator.generate()` freezes and validates a `ModulePlan`, delegates backend generation and printing, and returns an in-memory `GeneratedWrapper`. | Plan-to-rendered-wrapper orchestration. |
| [`prik/pipeline/build.py`](../../../prik/pipeline/build.py) | `build_fortran_extension()`, `build_pyi_extension()`, and `build_pyi_extension_from_manifest()` write artifacts, prepare native inputs, compile/link, and return `WrapperBuildResult`. `NativeBuildPlan` records those native inputs. | Public build behavior, artifact layout, build modes, manifests, scheduling, linking, or extension import. |

## Module Workflows

- **`pyi.py` has two routes.** `pyi_*_to_semantic_module()` parses a contract
  and converts it to semantic IR; path-set loading also reconciles external
  type references. `emit_module_stubs()` deep-copies semantic modules, adds
  required opaque dependencies, completes policy, and renders `.pyi` text.
- **`wrapper.py` is the rendered-wrapper boundary.** `GeneratedSource` and
  `GeneratedWrapper` are the handoff records. `WrapperGenerator.generate()`
  freezes and validates the completed plan before either backend lowers it,
  then assembles printed C, optional Fortran, and header payloads with stable
  names. An all-direct Fortran module has no bridge payload; its retained
  native-language requirement still selects the Fortran link driver. Generated
  native-code groups retain adapter and support membership separately even
  when both groups share one physical Fortran payload.
- **`type_mapping_report.py` is inspection only.** Its fixed C and Fortran
  inventories pass through the normal target probes, semantic converters, and
  NumPy dtype registry before Markdown rendering. It does not create a wrapper.

## `build.py` Navigation

`build.py` is the orchestration hub. Its public records describe inputs and
results without executing a build: `NativeCompilationUnit`,
`NativePrebuiltArtifact`, `NativeLinkItem`, `NativeBuildPlan`, and
`WrapperBuildResult`. Its three public entrypoints are source-first builds,
contract-first builds, and replay of a saved contract-build manifest.

Read its private sections as grouped phases, not as independent helpers:

```text
source or .pyi contract plus native inputs
  -> source/contract preparation and semantic-module assembly
  -> policy completion -> WrapperPlanner -> WrapperGenerator
  -> generated-source materialization and native build plan
  -> dependency-aware compilation, linking, and WrapperBuildResult

.pyi builds additionally: contract graph/export projection
                          -> manifest serialization or replay
```

Generated wrapper membership is data, not a filename convention. The build
materializes and compiles only the paths listed by `GeneratedWrapper`; an empty
bridge-source tuple is a complete all-direct result. Link-driver selection
combines retained native-language requirements with generated and caller-native
object languages, so absence of a generated adapter never implies absence of
the Fortran runtime.

The same rule applies when a source-free direct Fortran contract resolves its
symbol from a prebuilt object, static archive, or shared library. Those inputs
remain ordered `NativeLinkItem` records; direct routing changes generated
adapter membership, not caller-supplied artifact order or the required Fortran
link runtime.

`WrapperBuildResult` and saved `.pyi` manifests report each generated native
group's kind, language, member keys, and physical source paths. This makes
zero-source, adapter-only, support-only, and mixed output factual in direct
builds, source-only output, Makefiles, and manifest replay. Progress and
compiler records are emitted only for physical sources that are present.

The source file groups helpers around build configuration, generated-wrapper
materialization, native compilation scheduling, `.pyi` contract loading and
exports, native planning and link inputs, manifest handling, wrapper-module
assembly, Makefile output, type probing, and semantic preparation. Start from
the matching public entrypoint at the bottom, then follow only the phase it
calls.

## Run The Workflows

The following commands are independent. Start with the source-build example:
it exercises the complete public path described above.

```bash
python3 prik/pipeline/build.py
```

```text
scale(3.0, 2.5) = 7.5
```

This command writes a temporary Fortran source, builds an extension, imports
it through `WrapperBuildResult.import_module()`, and calls its generated API.
`7.5` therefore confirms generation, native compilation, import, and the
public call—not merely that source files were written. It requires configured
C and Fortran compilers.

`WrapperGenerator` demonstrates the handoff immediately before disk output:

```bash
python3 prik/pipeline/wrapper.py
```

```text
Extension initializer: PyInit_generator_demo
Rendered sources: bind_c_generator_demo_wrapper.f90, generator_demo_wrapper.c, generator_demo_wrapper.h
Native support: binding_support
```

The result is a `GeneratedWrapper` in memory; this command does not write or
compile files. The initializer and three source names identify the exact
artifacts that the next build step would write and compile.

The contract-loading workflow produces semantic IR and re-emits a stub:

```bash
python3 prik/pipeline/pyi.py
```

```text
Loaded semantic module: math
Loaded contract marker: True
Functions: scale
Re-emitted module:
from prik.contracts import Float64

def scale(
    value: Float64
) -> Float64: ...
```

The script loads one in-memory contract. The marker confirms that the semantic
module retains its `.pyi` origin; the final text is a fresh stub emitted from
that semantic model rather than the original syntax tree.

The target-datatype report is an inspection route, not a wrapper build:

```bash
python3 prik/pipeline/type_mapping_report.py
```

```text
| `int` | signed 32-bit | `Int (Int32 storage)` | `numpy.int32` |
```

The exact width depends on the active C target. The row keeps native spelling,
measured fact, semantic identity, and NumPy projection separate.

## Tests And Evidence

| Evidence | What it establishes |
| --- | --- |
| [Pipeline infrastructure](../../../tests/fortran/infrastructure/pipeline/) | Plan-to-rendered-wrapper assembly and cross-stage records. |
| [Semantic `.pyi` pipeline](../../../tests/fortran/semantic_pyi_format/pipeline/) | Contract loading, reconciliation, and stub emission. |
| [Build pipeline](../../../tests/fortran/building_shared_library/pipeline/) | Artifact output, manifests, build modes, and build-plan handoffs. |
| [Compilation integration](../../../tests/fortran/building_shared_library/compiling/) | Native command integration. |
| [End-to-end builds](../../../tests/fortran/building_shared_library/end_to_end/) | Build, import, and generated-extension behavior. |

## Change Routes

- Change `.pyi` batch loading, reconciliation, or caching in `pyi.py`.
- Change cross-stage datatype reporting in `type_mapping_report.py`.
- Change plan-to-artifact orchestration in `wrapper.py`.
- Change disk output, manifests, native build requests, compilation scheduling,
  linking, or imports in `build.py`.

## Boundaries And Invariants

- `WrapperGenerator` owns plan-to-rendered-wrapper orchestration. It neither
  makes semantic decisions nor invokes a compiler.
- `build.py` owns source output and public result records. `compiler/` owns the
  native commands it receives.
- A `.pyi` build treats its edited entry contract as authoritative for the
  Python API; it does not reparse native source to reconstruct that API.
- Path-set `.pyi` caches are operation-local. They must not become process-wide
  because later stages attach and freeze data.

The sole generation route is:

```python
complete_semantic_policies(module)
plan = WrapperPlanner().build(module)
generated = WrapperGenerator().generate(plan)
```

Unsupported policy fails at its owner before either backend emits source.

## Failure Boundary

Pipeline code reports invalid public build inputs, output modes, artifact
layout, manifests, and imported-result handling. It delegates source facts to
preprocessing and parsing; shared meaning to semantics; interoperability to
policy; completed-operation consistency to planning; emitted mechanisms to
code generation; text to printers; and native commands to compiler. Start
debugging with the first wrong representation or result, not with the final
build failure.
