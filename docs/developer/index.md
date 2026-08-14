---
title: Developer Documentation
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: architecture.md, packages/index.md, workflows/contributing.md
status: maintained
publication: reviewed
---

# Developer Documentation

Read these pages in order when you are new to PRIK:

1. [PRIK Architecture](architecture.md) explains the build flow, the
   representations passed between stages, and the boundary at which each
   decision becomes fixed.
2. [Architecture Components](packages/index.md) explain the build stages and
   supporting components through their local modules, entrypoints, examples,
   and tests.

For a specific change, use the matching reference:

- [Codebase Map](codebase-map.md) locates packages, modules, and hotspots.
- [Feature-to-Code Map](feature-to-code-map.md) and
  [Testing Strategy](testing-strategy.md) locate capability and test ownership.
- [Workflows](workflows/contributing.md) cover contributing, local
  verification, pull-request checks, and documentation maintenance.
