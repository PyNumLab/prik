---
title: Package Guides
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, ../codebase-map.md, ../feature-to-code-map.md
status: maintained
publication: reviewed
---

# Package Guides

The [architecture](../architecture.md) shows how PRIK moves from inputs to an
importable extension. These guides describe the packages that own each stage,
its local modules, and its tests. The [codebase map](../codebase-map.md)
provides the complementary module and hotspot inventory.

| Package | Responsibility | Relevant changes |
| --- | --- | --- |
| [`prik.pipeline`](pipeline.md) | Composes wrapper, contract, report, artifact, and build workflows. | Public build workflows, artifact layout, or cross-stage orchestration. |
| [`prik.preprocessing`](preprocessing.md) | Prepares Fortran input and measures target facts. | Includes, provenance, parser input, or target probes. |
| [`prik.parsers`](parsers.md) | Records Fortran and semantic-`.pyi` syntax facts. | Declarations, locations, parser diagnostics, or raw `.pyi` AST. |
| [`prik.semantics`](semantics.md) | Builds the shared language-neutral semantic model. | Semantic types, shapes, origins, or raw contract metadata. |
| [`prik.policy`](policy.md) | Completes interoperability and support decisions. | Ownership, projection, lifecycle, exports, or support choices. |
| [`prik.planning`](planning.md) | Projects completed policy into backend-neutral wrapper plans. | Planned operations, ordering, namespaces, or backend views. |
| [`prik.codegen`](codegen.md) | Lowers plans into C and Fortran nodes and Python facades. | Binding, bridge, node, or facade mechanisms. |
| [`prik.printers`](printers.md) | Serializes C, Fortran, and semantic `.pyi` representations. | Generated text, formatting, escaping, or line wrapping. |
| [`prik.compiler`](compiler.md) | Constructs and executes native compilation and linking commands. | Compiler profiles, command arguments, linking, or native-support installation. |
| [`prik.contracts`](contracts.md) | Defines the public semantic `.pyi` vocabulary. | Contract syntax or its public imported names. |
| [`prik.naming`](naming.md) | Normalizes public names and constructs generated symbols. | Public-name normalization, collisions, or generated symbols. |
| [`prik.runtime`](runtime.md) | Provides imported native handles and bundled native support. | Runtime handle behavior or native-support payloads. |
| [`prik.utilities`](utilities.md) | Holds mechanisms with no stage-specific owner. | A genuinely stage-neutral helper. |

Each guide records the same local contract:

1. Its responsibility and boundaries.
2. Its inputs, outputs, modules, and important entrypoints.
3. Direct-execution examples and the behavior they demonstrate.
4. Focused tests, change routes, and invariants.

The guides cover the current Fortran-wrapper route. The C-input frontend is
deferred material and does not change the generated CPython C binding backend.
