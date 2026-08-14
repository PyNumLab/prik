---
title: Codebase Map
audience: developers, contributors
prerequisites: contributor architecture guide
related: architecture.md, packages/index.md, feature-to-code-map.md, testing-strategy.md
status: maintained
publication: reviewed
---

# Codebase Map

This page is the directory of ownership for the maintained Fortran wrapper
route. It identifies the package or module that owns a concern. The
[architecture](architecture.md) explains the stage handoffs and authority
boundaries; the [feature-to-code map](feature-to-code-map.md) connects a
user-visible behavior to its documentation and evidence.

## Public And Build Entry Points

| Location | Responsibility |
| --- | --- |
| `prik/__init__.py` | Public build entry points and version. |
| `prik/cli.py` | CLI argument validation, stage selection, and output routing. |
| `prik/pipeline/build.py` | Source-first and contract-first extension-build orchestration. |
| `prik/pipeline/pyi.py` | Semantic `.pyi` loading and external-type reconciliation. |
| `prik/pipeline/wrapper.py` | Completed plan to rendered-wrapper orchestration and artifact records. |
| `prik/compiler/compilers.py` | Native compiler invocation and tool lookup. |

## Component Ownership

| Component | Owns | Key modules |
| --- | --- | --- |
| [`prik.pipeline`](packages/pipeline.md) | Build, wrapper, contract, report, and artifact orchestration. | `build.py`, `pyi.py`, `wrapper.py`, `type_mapping_report.py` |
| [`prik.preprocessing`](packages/preprocessing.md) | Prepared Fortran input, provenance, includes, and target probes. | `source.py`, `fortran.py`, `probes/fortran_types.py` |
| [`prik.parsers`](packages/parsers.md) | Fortran and semantic `.pyi` syntax facts. | `fortran/parser.py`, `pyi/parser.py` |
| [`prik.semantics`](packages/semantics.md) | Language-neutral semantic IR, conversions, scalar vocabulary, and raw metadata. | `models.py`, `fortran2ir.py`, `pyi2ir.py` |
| [`prik.policy`](packages/policy.md) | Completed ownership, export, lifecycle, and support policy. | `completion.py`, `construction.py`, `ownership.py`, `exports.py` |
| [`prik.planning`](packages/planning.md) | Policy-complete, backend-neutral wrapper plans. | `models.py`, `planner.py` |
| [`prik.codegen`](packages/codegen.md) | Plan-driven C and Fortran lowering, backend scalar projection, and Python facades. | `c/binding.py`, `c/python_surface.py`, `fortran/bridge.py` |
| [`prik.printers`](packages/printers.md) | Serialization of C, Fortran, and semantic `.pyi` representations. | `c.py`, `fortran.py`, `pyi.py` |
| [`prik.compiler`](packages/compiler.md) | Compiler execution, native-support installation, and linking. | `compilers.py`, `objects.py`, `native_support.py` |
| [`prik.runtime`](packages/runtime.md) | Imported runtime objects and bundled native support. | `handles.py`, `native_support/` |
| [`prik.contracts`](packages/contracts.md) | Public semantic `.pyi` contract vocabulary. | `__init__.py` |
| [`prik.naming`](packages/naming.md) | Public-name normalization and generated-symbol construction. | `policy.py`, `native_symbols.py` |
| [`prik.utilities`](packages/utilities.md) | Small helpers with no stage-specific ownership. | `declaration_expressions.py`, `stage_values.py`, `strings.py`, `visitor.py` |

The [architecture component guides](packages/index.md) give each component's
local module tour,
boundaries, execution example, and focused tests.

## Cross-Stage Hotspots

| Concern | Primary owners |
| --- | --- |
| Prepared source and target facts | `prik/preprocessing/source.py`, `prik/preprocessing/fortran.py`, `prik/preprocessing/probes/fortran_types.py` |
| Parsed language facts | `prik/parsers/fortran/parser.py`, `prik/parsers/pyi/parser.py` |
| Shared meaning | `prik/semantics/models.py`, `prik/semantics/fortran2ir.py`, `prik/semantics/pyi2ir.py` |
| Completed interoperability policy | `prik/policy/completion.py`, `prik/policy/construction.py`, `prik/policy/ownership.py`, `prik/policy/exports.py` |
| Deterministic wrapper planning | `prik/planning/models.py`, `prik/planning/planner.py` |
| Fortran bridge and CPython binding lowering | `prik/codegen/fortran/bridge.py`, `prik/codegen/c/binding.py`, `prik/codegen/c/python_surface.py` |
| Generated-text serialization | `prik/printers/fortran.py`, `prik/printers/c.py`, `prik/printers/pyi.py` |
| Native build and runtime payload | `prik/compiler/objects.py`, `prik/compiler/compilers.py`, `prik/compiler/native_support.py`, `prik/runtime/native_support/` |
| Names and scalar representations | `prik/naming/policy.py`, `prik/naming/native_symbols.py`, `prik/semantics/scalar_types.py`, `prik/codegen/primitive_scalar_types.py` |

## Documentation And Evidence

The [feature-to-code map](feature-to-code-map.md) names the public
documentation and focused tests for a supported behavior. The
[testing strategy](testing-strategy.md) describes test-tree ownership. Update
this map when package or cross-stage module ownership changes; update a package
guide when its local module structure changes. The supported public surface is
recorded in the public feature matrix.
