---
title: Source Package Guides
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, ../source-map.md, ../feature-to-code-map.md
status: maintained
publication: draft
---

# Source Package Guides

These pages explain the production package one ownership boundary at a time.
Read the [architecture guide](../architecture.md) first for the complete flow,
then open the package that owns the change.

| Package | Canonical guide | Boundary |
| --- | --- | --- |
| `prik.contracts` | [Contracts](contracts.md) | Public semantic `.pyi` vocabulary |
| `prik.compiler` | [Compiler](compiler.md) | Native command construction and execution |
| `prik.preprocessing` | [Preprocessing](preprocessing.md) | Source preparation, provenance, and target probes |
| `prik.parsers` | [Parsers](parsers.md) | Fortran and semantic `.pyi` syntax facts |
| `prik.semantics` | [Semantics](semantics.md) | Language-neutral semantic IR |
| `prik.policy` | [Policy](policy.md) | Completed post-IR interoperability decisions |
| `prik.planning` | [Planning](planning.md) | Mechanical projection into wrapper plans |
| `prik.codegen` | [Code generation](codegen.md) | Plan-driven backend nodes and Python facade source |
| `prik.printers` | [Printers](printers.md) | Serialization of formed representations |
| `prik.pipeline` | [Pipeline](pipeline.md) | Cross-stage workflow and artifact orchestration |
| `prik.runtime` | [Runtime](runtime.md) | Imported-extension handle behavior and native payload |
| `prik.naming` | [Naming](naming.md) | Shared public and generated symbol rules |
| `prik.utilities` | [Utilities](utilities.md) | Genuinely stage-neutral mechanisms |

Each guide uses the same order: purpose and boundaries, local structure,
workflow, important files and objects, direct execution examples with expected
output, test owners, change routes, and invariants. Source-tree `README.md`
files remain short orientation notes and link back to these canonical guides.
