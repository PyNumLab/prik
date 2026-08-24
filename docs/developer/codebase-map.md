---
title: Codebase Map
audience: developers, contributors
prerequisites: contributor architecture guide
related: architecture.md, packages/index.md, feature-to-code-map.md, testing-strategy.md
status: maintained
publication: reviewed
---

# Codebase Map

This page answers one question: which modules do I open for this concern? The
[architecture](architecture.md) explains the stage handoffs and authority
boundaries, the [architecture component guides](packages/index.md) explain what
each component is responsible for, and the
[feature-to-code map](feature-to-code-map.md) connects a user-visible behavior
to its documentation and evidence.

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

Concerns are listed in pipeline order. The component guide explains the
boundary; the modules are where the change lands.

| Concern | Component | Owning modules |
| --- | --- | --- |
| Build, contract, report, and artifact orchestration | [`prik.pipeline`](packages/pipeline.md) | `build.py`, `pyi.py`, `wrapper.py`, `type_mapping_report.py` |
| Prepared source, provenance, and target facts | [`prik.preprocessing`](packages/preprocessing.md) | `source.py`, `fortran.py`, `c.py`, `probes/fortran_types.py`, `probes/c_types.py` |
| Parsed language facts | [`prik.parsers`](packages/parsers.md) | `fortran/parser.py`, `pyi/parser.py`, `c/` |
| Shared language-neutral meaning | [`prik.semantics`](packages/semantics.md) | `models.py`, `fortran2ir.py`, `pyi2ir.py`, `c2ir.py`, `scalar_types.py` |
| Completed interoperability policy | [`prik.policy`](packages/policy.md) | `completion.py`, `construction.py`, `ownership.py`, `exports.py`, `native_array_handles.py` |
| Deterministic wrapper planning | [`prik.planning`](packages/planning.md) | `models.py`, `planner.py`, `entrypoints.py` |
| Binding, bridge, and Python-facade lowering | [`prik.codegen`](packages/codegen.md) | `c/binding.py`, `c/python_surface.py`, `fortran/bridge.py`, `primitive_scalar_types.py` |
| Generated-text serialization | [`prik.printers`](packages/printers.md) | `c.py`, `fortran.py`, `pyi.py` |
| Native build and link execution | [`prik.compiler`](packages/compiler.md) | `compilers.py`, `objects.py`, `compiler_profiles.py`, `native_support.py` |
| Imported runtime objects and native payload | [`prik.runtime`](packages/runtime.md) | `handles.py`, `native_support/` |
| Public semantic `.pyi` vocabulary | [`prik.contracts`](packages/contracts.md) | `__init__.py` |
| Public names and generated symbols | [`prik.naming`](packages/naming.md) | `policy.py`, `native_symbols.py` |
| Stage-neutral helpers | [`prik.utilities`](packages/utilities.md) | `declaration_expressions.py`, `stage_values.py`, `strings.py`, `visitor.py` |

Scalar representation deliberately spans three of those rows: semantic identity
lives in `semantics/scalar_types.py`, the measured target fact comes from
`preprocessing/probes/`, and backend spellings live in
`codegen/primitive_scalar_types.py`.

## Keeping This Map Accurate

Update this page when a package gains, loses, or moves an owning module.
Update the matching [component guide](packages/index.md) when its local
structure or boundary changes, and the
[feature-to-code map](feature-to-code-map.md) when a user-visible capability
changes owners. The supported public surface is recorded in the public feature
matrix, not here.
