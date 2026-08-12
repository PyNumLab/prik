---
title: Contributor Documentation
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: architecture.md, packages/index.md, workflows/contributing.md
status: maintained
publication: draft
---

# Contributor Documentation

This is the single documentation area for changing, testing, governing, and
releasing PRIK. Start with the architecture guide, then open the detailed
package, workflow, concept, design, or active-roadmap page needed for the task.

## Orientation

- [Contributor architecture](architecture.md): shallow repository/package
  structure, complete workflow, authority rules, CLI/root files, and package
  routes.
- [Source package guides](packages/index.md): one detailed page per production
  package, with local structure, important objects, runnable examples, tests,
  change routes, and invariants.
- [Source map](source-map.md): exact file and hotspot lookup.
- [Feature-to-code map](feature-to-code-map.md): user-visible capability to
  source, tests, and documentation.
- [Testing strategy](testing-strategy.md): language/feature/stage ownership and
  verification selection.

## Cross-Cutting Concepts

- [Datatype lifecycle](concepts/datatype-lifecycle.md): compiler measurement,
  semantic identity, policy, backend representation, and runtime validation.

## Contributor Workflows

- [Contributing](workflows/contributing.md)
- [Quality assurance](workflows/quality-assurance.md)
- [Continuous integration and delivery](workflows/ci.md)
- [Documentation architecture](workflows/documentation.md)
- [Release process](workflows/release.md)

## Design And Planning

- [Multilanguage runtime architecture](design/multilanguage-runtime.md) is an
  explicit long-term design, not a support claim.
- [Wrapper open decisions](design/wrapper-open-decisions.md) records unresolved
  or revisitable design questions.
- [Active roadmaps](roadmap/index.md) contain incomplete work only.

## Deferred Input-Language Material

The C parser/C-to-IR reference is retained under `deferred/` and excluded from
the published Fortran contributor workflow until that input path is mature.
This does not hide the generated CPython C binding backend used by Fortran
wrappers.
