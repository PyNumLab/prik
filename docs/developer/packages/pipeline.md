---
title: Pipeline Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, package guides for participating stages
related: ../architecture.md, index.md, compiler.md, planning.md, codegen.md, printers.md
status: maintained
publication: draft
---

# Pipeline Package

## Purpose And Boundaries

`prik/pipeline/` composes complete workflows across established stage
boundaries. It selects the next stage, preserves progress and timing, assigns
artifact names, writes generated payloads, coordinates compilation/linking,
and returns public results. It does not absorb parser grammar, semantic rules,
policy, backend lowering, printer formatting, or compiler command mechanics.

## Local Structure

```text
prik/pipeline/
├── pyi.py
├── type_mapping_report.py
├── wrapper.py
└── build.py
```

## Internal Workflow

```text
semantic modules or source-build request
  -> completed policy and WrapperPlanner
  -> WrapperGenerator
       -> backend node generation
       -> language printers
       -> GeneratedWrapper
  -> build.py writes sources and creates NativeBuildPlan
  -> prik.compiler compiles and links
  -> WrapperBuildResult
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `pyi.py` | `pyi_*_to_semantic_module()` workflows, `emit_module_stubs()` | Loads text/files/path sets, caches conversion per operation, reconciles external types, and emits stub packages. |
| `type_mapping_report.py` | report builders | Connects target probes, semantic conversion, and codegen dtype projection into an auditable report. |
| `wrapper.py` | `GeneratedSource`, `GeneratedWrapper`, `WrapperGenerator` | Validates/freezes a plan, invokes docstring and backend generation, prints sources, assigns names, and returns one in-memory wrapper artifact. |
| `build.py` | `NativeCompilationUnit`, `NativePrebuiltArtifact`, `NativeLinkItem`, `NativeBuildPlan`, `WrapperBuildResult` | Owns public source/`.pyi` build APIs, file output, native input plans, dependency-ready compilation, linking, manifests, and extension import. |

## Execution Examples

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

```bash
python3 prik/pipeline/type_mapping_report.py
```

```text
| `int` | signed 32-bit | `Int (Int32 storage)` | `numpy.int32` |
```

The exact width depends on the active target and requires a C compiler. The
columns expose native spelling, measured fact, semantic identity, and NumPy
projection rather than hiding them behind one universal datatype table.

```bash
python3 prik/pipeline/wrapper.py
```

```text
Extension initializer: PyInit_generator_demo
Rendered sources: bind_c_generator_demo_wrapper.f90, generator_demo_wrapper.c, generator_demo_wrapper.h
Native support: binding_support
```

This result is still in memory: no file has been written or compiled.

```bash
python3 prik/pipeline/build.py
```

```text
scale(3.0, 2.5) = 7.5
```

The final example requires configured C and Fortran compilers. It follows the
entire public source-build path, imports the resulting extension, and calls its
generated Python API.

## Tests

- [Pipeline infrastructure](../../../tests/fortran/infrastructure/pipeline/)
- [Semantic `.pyi` pipeline](../../../tests/fortran/semantic_pyi_format/pipeline/)
- [Build pipeline](../../../tests/fortran/building_shared_library/pipeline/)
- [Compilation integration](../../../tests/fortran/building_shared_library/compiling/)
- [End-to-end builds](../../../tests/fortran/building_shared_library/end_to_end/)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Change `.pyi` batch loading, reconciliation, or caching in `pyi.py`.
- Change cross-stage datatype reporting in `type_mapping_report.py`.
- Change plan-to-artifact orchestration in `wrapper.py`.
- Change disk output, manifests, native build requests, compilation scheduling,
  linking, or imports in `build.py`.

## Invariants And Common Mistakes

- `WrapperGenerator` owns plan-to-rendered-wrapper orchestration, not semantic
  decisions and not native compilation.
- Per-operation semantic caches must not become process-global because later
  stages attach and freeze data.
- A pipeline helper delegates domain rules to their owning package.
- There is one direct generation route and no legacy retry:

  ```python
  complete_semantic_policies(module)
  plan = WrapperPlanner().build(module)
  generated = WrapperGenerator().generate(plan)
  ```

  Unsupported completed policy fails with its exact owner before either
  backend emits source.
- `.pyi` builds reuse the same backend but take API/ABI facts from one edited
  entry contract plus explicit native inputs; they never reparse native source
  to reconstruct the Python API.

## Failure Ownership

| Failure | Earliest owner |
| --- | --- |
| Compiler preprocessing or native include expansion | preprocessing |
| Required target facts cannot be measured | preprocessing probe |
| Source syntax cannot be represented | parser |
| Source facts cannot form a contract | semantic conversion |
| Lifetime, ABI, projection, or support is unsafe | policy completion |
| Completed policy is inconsistent while projected | planning |
| A supported plan lacks an emitted mechanism | binding or bridge generator |
| Native command or link plan is wrong | compiler or build pipeline |
| Imported runtime behavior is wrong | generated binding, runtime support, or upstream policy according to cause |
