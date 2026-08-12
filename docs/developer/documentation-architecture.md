---
title: Documentation Architecture
audience: developers, maintainers, contributors
prerequisites: repository checkout, documentation metadata standard
related: architecture.md, testing-strategy.md, ../user/index.md
status: maintained
publication: draft
---

# Documentation Architecture

This page defines how prik documentation is organized and maintained. It is a
repository-governance contract, not part of the product-learning material.
`mkdocs.yml` owns the complete intended navigation for the User and Contributor
areas. A publication hook filters that tree so GitHub Pages contains only
pages explicitly marked as reviewed.

## Architecture Principles

1. Active documentation has two physical areas: `user/` and `developer/`. The
   latter is presented as Contributor Documentation and serves developers,
   maintainers, and future contributors from one architectural account. Both
   areas may be published after review.
2. `docs/index.md` is the website entry point. Each area index gates its whole
   area: a draft area index prevents every page below that area from entering
   the production site, even when an individual child page is marked reviewed.
3. Implemented behavior is documented as supported only when current code and
   tests prove it. Public user pages describe behavior and limits without
   exposing internal test-evidence ledgers.
4. Planned behavior is marked explicitly and never presented as an implemented
   user contract.
5. Contributor governance and volatile internals do not appear in user workflows.
6. Historical material remains under `old_docs/` and outside active navigation.
7. User-facing source-driven examples show the complete input source before the
   command that consumes it. Generated paths must come from an immediately
   preceding command, and commands show their expected result. Fixture-backed
   examples stay synchronized with their checked source.
8. The website keeps its documentation navigation expanded, shows a draggable
   scrollbar when the sidebar is longer than the screen, and renders an
   accessible copy control on every code block, including command-output and
   result blocks.
9. On desktop-sized viewports, the page body starts beside the navigation and
   uses a `1200px` maximum width: wider than the theme default for code and
   tables, but still bounded for readable prose. Any unused space remains on
   the far right rather than separating the sidebar from the content.
10. Code and result blocks use a consistent responsive width capped at `56rem`.
    They reserve dedicated right-side space for the copy control, and long lines
    scroll inside the block instead of widening the page.

`docs/index.md` is the user-first project entrance. It uses the canonical
`PRIK — Python Runtime Interop Kit` identity and public description, shows the
shortest checked source-to-import workflow, summarizes the product's concrete
advantages, and links to real-library evidence before sending the reader into
Getting Started. Contributor and deeper User Guide destinations stay available
through site navigation instead of competing with that first task.
The FAQ uses natural task questions as concise routes to authoritative guides;
it does not duplicate those guides.

## Audience Areas

| Area | Primary reader | Publication | Content |
| --- | --- | --- | --- |
| `user/` | People using prik | Documentation website after review | Getting Started, guides, performance benchmarks, tutorials, examples, public reference, support status, FAQ, troubleshooting |
| `developer/` | Developers, maintainers, and future contributors changing or governing prik | Documentation website after review | Architecture, source orientation, design decisions, internal maps, testing, coding standards, feature work, contribution workflows, documentation policy, CI administration, releases, and roadmaps |

Pages use their task and stability for placement within the contributor tree.
Implemented architecture, design proposals, roadmaps, and release procedures
remain separate topics, but they do not claim separate architectural
audiences. Cross-area links between user and contributor documentation should
explain why the reader is leaving the current task.

## Reading Order And Cross-Links

The `nav` sequence in `mkdocs.yml` is the canonical reading order. Sequential
User documentation pages may link back to pages the reader has already
completed. They must not link from instructional prose to a later page in that
sequence. Explicit terminal navigation blocks headed `Next` may link forward
because choosing a next destination is their purpose. Outside those blocks,
name the later topic in plain text and say that it is covered later instead of
asking the reader to leave the current task.
When a section index presents an ordered reading list of pages in that same
section, keep the list and the matching `mkdocs.yml` subsection in the same
order so sidebar next/previous navigation follows the advertised route.
`Next` blocks list destinations as bullets, and each bullet includes at least
one Markdown link. If an intended destination page does not exist yet, either
remove the destination until it is useful or create the draft page with
metadata and a TODO section.

Each page includes the behavior, warning, ownership fact, or limitation needed
for its current task. A forward reference never defers a fact needed now.
README documentation lists, area indexes, and explicit navigation menus are
exceptions because choosing a destination is their purpose. Same-page anchors
and links to source or test evidence do not change documentation reading order.
Contextual links to `user/reference/pyi-contracts/` are also allowed after a
Getting Started or User Guide section has already taught a complete small
contract edit. These links provide optional lookup of the full editing rules;
they must not replace instructions required to complete the current example.

## Page Metadata Contract

Every page under `docs/` starts with front matter containing:

- `title`: navigation title;
- `audience`: primary intended readers;
- `prerequisites`: assumed knowledge or pages;
- `related`: adjacent pages; and
- `status`: `maintained`, `draft`, `planned-documentation`,
  `not-yet-implemented`, `design`, or `active-roadmap`;
- `publication`: `draft` until a maintainer has reviewed the page for the
  website, then `reviewed`.

Pages with status `draft`, `planned-documentation`, or
`not-yet-implemented` include a `## TODO` section.

## Publication Review Contract

Publication is fail-closed. A missing or unknown `publication` value is treated
as `draft`. Production builds include a Markdown page only when:

1. its own front matter says `publication: reviewed`;
2. `docs/index.md` is reviewed; and
3. for a page in `user/` or `developer/`, that area's index is also reviewed
   (`user/index.md` or `developer/index.md`).

The publication hook removes every other Markdown page from the MkDocs file
collection and navigation before rendering, so drafts do not enter generated
HTML, search, or the sitemap. When a reviewed page mentions an unpublished
documentation page, the production build keeps the link visible with its
expected website route even though the target page itself is not published.
Links to existing repository evidence outside the `docs/` tree are rewritten to
the matching file or directory on GitHub; links to missing targets remain
unchanged so the strict build can reject them. Links to another active
documentation page or directory must stay relative to `docs/`.

Use the normal local server to preview exactly what GitHub Pages will publish:

```bash
python3 -m mkdocs serve
```

Use the explicit draft-preview environment flag while reviewing unpublished
pages locally:

```bash
PRIK_DOCS_INCLUDE_DRAFTS=1 python3 -m mkdocs serve
```

Draft preview adds a visible warning to unpublished pages. Changing a page from
`publication: draft` to `publication: reviewed` is the only publication-state
edit. Existing navigation remains the intended complete tree; the hook reveals
reviewed entries automatically. New pages must still be added to `mkdocs.yml`.

## Repository Tree

```text
docs/
  index.md
  user/
    index.md
    performance.md
    getting-started/
    guide/
    tutorials/
    examples/
    reference/
    language-support/
    faq/
    troubleshooting/
  developer/
    index.md
    architecture.md
    contributing/
    documentation-architecture.md
    design/
    internal-architecture/
    roadmap/
    CI, release, source, and workflow pages
  javascripts/
    code-copy.js
  stylesheets/
    site.css
    code-copy.css
  old_docs/
```

The repository-root `CHANGELOG.md` is the canonical release history. It lives
beside `README.md` and `pyproject.toml` so GitHub and package users can find it
without navigating the documentation website.

New active pages must be created in one of the two areas. Website-only static
behavior and presentation assets live in `javascripts/` and `stylesheets/`.
Do not restore separate developer/maintainer architecture trees or place
contributor governance beside the website landing page. Historical
`old_docs/` material is never eligible for website publication.

The Performance page keeps its explanatory text and reproduction workflow in
reviewed Markdown. Result-dependent summary, table, and environment blocks are
bounded by `prik-performance-*` comments and are generated from paired `pyperf`
files by `tools/generate_performance_docs.py`. The same tool owns the runtime
comparison SVG and the clean-build comparison SVG. Clean-build results contain
development and optimized compiler profiles and record the compiler-process
limit used by prik; f2py retains its normal Meson/Ninja scheduler. Generation
must fail when a marker is missing or duplicated;
it must not rewrite prose outside those blocks. The environment block records
both the operating-system distribution and the lower-level platform string so
published results identify the benchmark host clearly.

Automated performance snapshots run on the fixed `ubuntu-24.04-arm` workflow
label after verifying its Neoverse N2/Cobalt 100 CPU part. The benchmark scripts
add an architecture-neutral CPU identity to every runtime and build result
because pyperf's Linux metadata collector does not report `cpu_model_name` on
every ARM64 `/proc/cpuinfo` format. Documentation generation continues to
require matching CPU metadata across each prik/f2py result pair.
Runtime results combine equal reduced worker budgets from PRIK-first and
f2py-first passes in the same job. The merged suites drive publication, while
the order-specific suites remain in the uploaded artifact for auditability.

## Continuous Documentation Quality

- Require metadata for every active page.
- Keep website navigation, repository routing, area indexes, and physical areas
  synchronized.
- Reject draft pages and draft-gated areas from published site navigation.
- Require explicit publication metadata on every active page.
- Check that User documentation does not link forward from instructional prose,
  except for the documented contextual `.pyi` contract references.
- Treat unsupported-feature placeholders as blocking reminders during feature
  completion.
- Run link, structure, generated-reference freshness, and executable-example
  checks in CI.
