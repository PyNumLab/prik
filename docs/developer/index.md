---
title: Contributor Documentation
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: architecture.md, packages/index.md, workflows/contributing.md
status: maintained
publication: reviewed
---

# Contributor Documentation

This is the single documentation area for changing, testing, and governing
PRIK. Start with the architecture guide, then open the detailed
package, workflow, concept, design, or active-roadmap page needed for the task.

## Orientation

- [PRIK architecture](architecture.md): build architecture, input routes,
  stage handoffs, concrete representations, and authority boundaries.
- [Package guides](packages/index.md): one detailed page per production
  package, with local structure, important objects, runnable examples, tests,
  change routes, and invariants.
- [Codebase map](codebase-map.md): package, module, and hotspot ownership.
- [Feature-to-code map](feature-to-code-map.md): user-visible capability to
  source, tests, and documentation.
- [Testing strategy](testing-strategy.md): language/feature/stage ownership and
  verification selection.

## Workflows

- [Contributing](workflows/contributing.md): find an owner, change the
  contract, and prepare a focused pull request.
- [Quality assurance](workflows/quality-assurance.md): choose and run the
  required local evidence.
- [Pull request checks](workflows/ci.md): understand the hosted checks that
  follow local verification.
- [Documentation maintenance](workflows/documentation.md): write, verify, and
  preview documentation locally.

## Cross-Cutting Concepts

- [Datatype lifecycle](concepts/datatype-lifecycle.md): compiler measurement,
  semantic identity, policy, backend representation, and runtime validation.

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
