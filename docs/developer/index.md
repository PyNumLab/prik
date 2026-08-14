---
title: Developer Documentation
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: architecture.md, packages/index.md, workflows/contributing.md
status: maintained
publication: reviewed
---

# Developer Documentation

PRIK turns source or semantic `.pyi` contracts into importable CPython
extensions through a staged build pipeline. These documents explain that
architecture, the components that implement it, and how to locate change and
test ownership.

## Read these first

When you are new to PRIK, read these pages in order:

1. [PRIK Architecture](architecture.md) — build flow, stage handoffs, and the
   boundary at which each decision becomes fixed.
2. [Architecture Components](packages/index.md) — each build stage and supporting
   component: local modules, entrypoints, examples, and focused tests.

## Get set up

Install an editable checkout with development tools:

```bash
python3 -m pip install -e ".[qa]"
```

For the short public checklist (branch, tests, changelog, license), see the
repository-root `CONTRIBUTING.md`. The full contributor path is in
[Contributing workflow](workflows/contributing.md).

## For a specific change

| Need | Doc |
| --- | --- |
| Locate packages, modules, and hotspots | [Codebase Map](codebase-map.md) |
| Connect a capability to code and evidence | [Feature-to-Code Map](feature-to-code-map.md) |
| Choose where tests live and what they prove | [Testing Strategy](testing-strategy.md) |
| Contribute, verify locally, and open a PR | [Contributing workflow](workflows/contributing.md) |
| Static analysis and broader verification | [Quality Assurance](workflows/quality-assurance.md) |
| Hosted PR checks | [Pull request checks](workflows/ci.md) |
| Maintain docs and executable examples | [Documentation maintenance](workflows/documentation.md) |
