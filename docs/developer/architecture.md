---
title: PRIK Architecture
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: packages/index.md, codebase-map.md, feature-to-code-map.md, testing-strategy.md
status: maintained
publication: reviewed
---

# PRIK Architecture

PRIK turns Fortran declarations into importable CPython extensions. It first
records source facts, converts them into a language-neutral semantic model,
completes the interoperability policy, plans the wrapper, and emits and builds
the native code. Editable semantic `.pyi` contracts can enter the same process
at semantic-IR construction.

This document describes the system-level model: the stages, their handoffs,
their authority boundaries, and the representations they produce. The linked
[architecture component guides](packages/index.md) describe the implementation inside each
package.

## Build Architecture

The package root is a small public facade. A direct Fortran build enters through
`build_fortran_extension`:

```python
from prik import build_fortran_extension

result = build_fortran_extension("solver.f90", output_dir="build/solver")
module = result.import_module()
```

`prik.__init__` exposes `__version__` and the source-first and contract-first
build entry points: `build_fortran_extension` and `build_pyi_extension`. The
CLI enters through `python3 -m prik` and dispatches to the same stage owners.
Its parser, semantic, and report commands intentionally stop before a complete
wrapper build.

The two input routes converge in semantic IR construction, then share policy,
planning, generation, and native compilation:

<object class="prik-build-path" type="image/svg+xml" data="../assets/build-path.svg" aria-label="Interactive PRIK build path">
  <a href="../packages/">Open the Architecture Components guides</a>.
</object>

Select a stage or input route to open its component guide. Each route box opens
its first owning stage.

Pipeline orchestration spans the complete build: it coordinates source facts,
shared meaning, completed interoperability policy, a wrapper plan, emitted
artifacts, and the final result. `compiler/` is the native execution service
invoked after generated source is available. The following table names the
concrete representations produced for one small wrapper.

Three supporting packages cross those stages without becoming hidden policy
owners: [`contracts/`](packages/contracts.md) supplies the public semantic
`.pyi` vocabulary; [`naming/`](packages/naming.md) supplies stable public and
generated-name rules; and [`utilities/`](packages/utilities.md) supplies only
stage-neutral mechanisms. [`runtime/`](packages/runtime.md) enforces completed
handle and view behavior after the generated extension is imported.

Type-mapping reports inspect source and semantic facts without building a
wrapper. They are an inspection route, not a second backend.

## `scale` Across the Pipeline

The [one-command quick start](../index.md#from-fortran-to-python-in-one-command)
introduces the source, build command, and `7.5` result. Here, its `scale`
function illustrates the representations produced across the pipeline.

| Stage owner | Result for `scale` | What that owner is responsible for |
| --- | --- | --- |
| `pipeline/` | A public build request, artifact layout, native build request, and eventually a `WrapperBuildResult`. | Orchestrate the complete build without taking over stage-owned decisions. |
| `preprocessing/` | Prepared source, provenance, dependencies, and compiler-derived type facts. | Make the source and target facts available to later stages. |
| `parsers/` | A `FortranProject` with source-faithful function, argument, type, and `intent` facts. | Record syntax and source-located diagnostics without deciding wrapper behavior. |
| `semantics/` | A language-neutral semantic model ([`SemanticModule`](packages/semantics.md)) containing a callable and its stable type, shape, origin, and raw contract metadata. | Give frontend facts a shared meaning. |
| `policy/` | The semantic model with complete export, transport, ownership, projection, lifecycle, and support choices. | Decide how the callable may interoperate with Python. |
| `planning/` | A deterministic wrapper plan ([`ModulePlan`](packages/planning.md)) with binding, shared native-entrypoint, and bridge facets, ordered C ABI and original-Fortran call records, names, and build requirements. | Project and validate completed choices without making new policy. |
| `codegen/` | CPython-binding nodes from binding plus entrypoint facets, and Fortran-bridge nodes from entrypoint plus bridge facets, with Python-facade representation. | Implement the plan-selected mechanisms. |
| `printers/` | Generated C and Fortran source text. | Serialize formed nodes without deciding behavior. |
| `compiler/` | Recorded or executed native commands and a linked extension. | Compile and link the explicit native inputs. |
| Extension module and [`runtime/`](packages/runtime.md) | An importable `scale` module; its call returns `np.float64(7.5)` for `np.float64(3.0)` and `np.float64(2.5)`. | The generated public Python interface and any imported runtime support it uses. |

The first incorrect representation locates the stage whose behavior or
diagnostic changed.

## Architectural Boundaries

> **Meaning moves forward. Downstream stages implement earlier decisions; they
> do not silently reinterpret them.**

PRIK deliberately separates four kinds of work:

| Kind of work | Owner | Boundary |
| --- | --- | --- |
| Source facts | `preprocessing/`, `parsers/` | What was written and what the compiler target reports. |
| Shared meaning | `semantics/` | A language-neutral model, not a Python API or emitted code. |
| Interoperability decisions | `policy/` | Complete policy before planning starts. |
| Planned mechanism and emitted text | `planning/`, `codegen/`, `printers/` | Implement the completed decision; do not replace it. |

The critical boundary is before
[`WrapperPlanner.build()`](packages/planning.md), the planning operation that
projects policy-complete semantic IR into a `ModulePlan`. By then, policy has
completed every decision needed by wrapper generation: object kind, ownership,
transfer, destruction, storage, mutability and writeback, nullability, output
projection, setter behavior, release responsibility, and support.

Planning may order, name, validate, and project those choices. It must not
invent a new interoperability decision. Code generation then dispatches from
the plan into named implementation mechanisms.

Binding and bridge generation must not infer or override policy from a
datatype, Fortran `intent`, alias shape, storage layout, or a local memory
check. If a required decision is absent, its owner reports the diagnostic; a
downstream fallback would hide an architectural error.

The architecture preserves these invariants:

- Parsers preserve source facts; semantic IR supplies shared meaning.
- Policy is complete before planning; planning projects rather than creates it.
- Code generation implements a plan; printers only serialize it.
- Pipeline orchestrates stages; it does not become a parser, policy engine, or
  lowering backend.
- Supported behavior has focused owner-stage evidence and, when public,
  end-to-end evidence.

## Input Routes

PRIK has two supported ways to describe a wrapper. They converge at
`SemanticModule` and use the same policy, planning, lowering, build, and
runtime architecture afterward.

| Input | Enters through | Architectural role |
| --- | --- | --- |
| Fortran source | preprocessing, Fortran parsing, and Fortran-to-IR conversion | Source-first wrapper contract. |
| Semantic `.pyi` | raw `.pyi` parsing and `.pyi`-to-IR conversion | Contract-first wrapper surface with explicit native implementation inputs. |

The C-input frontend is deferred and is not part of the published contributor
architecture. This does not affect PRIK's generated CPython C binding backend,
which remains part of the supported Fortran-wrapper architecture.

## Ownership and Evidence

The stage at which PRIK first has enough information to determine an answer
owns both the behavior and its diagnostic. Syntax facts belong to parsing;
language-neutral types and shapes belong to semantics; ownership, projection,
lifetime, setters, and support belong to policy; completed wrapper operations
belong to planning; and emitted mechanisms belong to code generation.

Focused tests prove an invariant at its earliest owner. Public support claims
also require end-to-end build, import, call, and behavior evidence. The
[testing strategy](testing-strategy.md) records the complete evidence model;
the [codebase map](codebase-map.md), [feature-to-code map](feature-to-code-map.md),
and [architecture component guides](packages/index.md) record the detailed
ownership.
For package and module ownership, continue with the
[Codebase Map](codebase-map.md).
