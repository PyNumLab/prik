---
title: Documentation Maintenance
audience: developers, maintainers, contributors
prerequisites: repository checkout
related: ../architecture.md, ../testing-strategy.md, quality-assurance.md, ../../user/index.md
status: maintained
publication: reviewed
---

# Documentation Maintenance

PRIK has two active documentation areas: `docs/user/` for product users and
`docs/developer/` for contributors and maintainers. `mkdocs.yml` defines the
page order, and `docs_theme/nav.html` makes each expandable section label open
its first page while its **+** control expands or collapses the section.
`old_docs/` is historical material outside the site.

## Write The Right Contract

User pages explain supported behavior and its limits. Contributor pages explain
ownership, architecture, tests, and maintenance. Planned work must be marked
as planned, not as current support.

Support claims require current implementation and evidence. A parser test does
not prove wrapper support, and a successful build does not prove runtime
behavior. Examples must be complete enough to run in a clean checkout: show
the input before the command that consumes it, and show the result when it
helps the reader verify success.

For one user-guide example with two or more matching views, use the
`prik-example-tabs` component. When an example shows both **Fortran source**
and **Python usage**, include the complete generated `.pyi` as the third view.
Later sections may quote only the relevant contract snippet. Use only the
relevant pair when source is absent. Select source first when it exists;
otherwise select the contract first. Put the `generate --pyi` command directly
below the contract, mirroring the build command below the source. Place the
observable result immediately after the tab set. Do not use it in Getting
Started, whose pages should remain linear.

When an example teaches a contract edit, add a separate **Generated contract**
view before **Edited contract**. Put the generation command below the former
and the edited-contract build command below the latter.

## Add Or Update A Page

1. Put the page in the user or contributor area that matches its reader and
   task.
2. Add front matter with `title`, `audience`, `prerequisites`, `related`,
   `status`, and `publication`.
3. Add it to `mkdocs.yml` in its intended reading order and update necessary
   index or contextual links.
4. Keep related source, tests, commands, and limitations accurate.

## Verify Locally

```bash
python3 -m pytest -q tests/docs
git diff --check
python3 -m mkdocs serve
python3 -m mkdocs build --strict
```

`tests/docs` checks links, metadata, public references, and executable
examples. Package-guide production commands are checked against the result
shown in the guide.

New pages remain `publication: draft` until a maintainer reviews them. To
preview draft pages locally, run:

```bash
PRIK_DOCS_INCLUDE_DRAFTS=1 python3 -m mkdocs serve
```
