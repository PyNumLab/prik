---
title: Source Package Guides
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, ../codebase-map.md, ../feature-to-code-map.md
status: maintained
publication: draft
---

# Source Package Guides

These pages are the file-level companion to the
[architecture guide](../architecture.md). Read the architecture guide once for
the whole flow, then use this table to enter the owner of a change. Do not read
the guides as thirteen alternative pipelines: each describes one handoff in
the same pipeline.

| Package | Read it when you need to change | Canonical guide |
| --- | --- | --- |
| `prik.contracts` | public semantic `.pyi` syntax | [Contracts](contracts.md) |
| `prik.compiler` | compiler profiles, command argv, or native-support installation | [Compiler](compiler.md) |
| `prik.preprocessing` | parser input, provenance, includes, or target probes | [Preprocessing](preprocessing.md) |
| `prik.parsers` | Fortran syntax facts or raw `.pyi` syntax | [Parsers](parsers.md) |
| `prik.semantics` | the shared semantic graph, types, or raw metadata | [Semantics](semantics.md) |
| `prik.policy` | completed ownership, projection, lifecycle, or support choices | [Policy](policy.md) |
| `prik.planning` | plan representation, ordering, or backend views | [Planning](planning.md) |
| `prik.codegen` | generated binding, bridge, node, or Python-facade mechanism | [Code generation](codegen.md) |
| `prik.printers` | C, Fortran, or `.pyi` text serialization | [Printers](printers.md) |
| `prik.pipeline` | wrapper, contract, report, artifact, or build orchestration | [Pipeline](pipeline.md) |
| `prik.runtime` | imported native handles or bundled native support | [Runtime](runtime.md) |
| `prik.naming` | public-name normalization or generated symbols | [Naming](naming.md) |
| `prik.utilities` | a genuinely stage-neutral helper | [Utilities](utilities.md) |

Each guide answers the same practical questions:

1. What does this stage receive and produce?
2. Which module owns the behavior I need to change?
3. Which classes and functions are the important entrypoints?
4. What does each direct-execution example prove?
5. Which tests protect that behavior?

The directory tour covers every supported Python module under that package,
including package initializers and nested backend packages. The deferred
C-input frontend is intentionally excluded from the published Fortran route.
Source-tree `README.md` files remain short orientation notes and link back to
these canonical guides.
