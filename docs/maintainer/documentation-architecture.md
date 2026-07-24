---
title: Documentation Architecture
audience: maintainers
prerequisites: repository checkout, documentation metadata standard
related: README.md, ../developer/testing-strategy.md, ../user/index.md
status: maintained
publication: draft
---

# Documentation Architecture

This page defines how x2py documentation is organized and maintained. It is a
repository-governance contract, not part of the product-learning material.
`mkdocs.yml` owns the complete intended navigation for the User, Developer,
and Maintainer lanes. A publication hook filters that tree so GitHub Pages
contains only pages explicitly marked as reviewed.

## Architecture Principles

1. Active documentation has three physical lanes: `user/`, `developer/`, and
   `maintainer/`. Every lane may be published after review.
2. `docs/index.md` is the website entry point. Each lane index gates its whole
   lane: a draft lane index prevents every page below that lane from entering
   the production site, even when an individual child page is marked reviewed.
3. Implemented behavior is documented as supported only when current code and
   tests prove it. Public user pages describe behavior and limits without
   exposing internal test-evidence ledgers.
4. Planned behavior is marked explicitly and never presented as an implemented
   user contract.
5. Maintainer policy and volatile internals do not appear in user workflows.
6. Historical material remains under `old_docs/` and outside active navigation.
7. User-facing source-driven examples show the complete input source before the
   command that consumes it. Generated paths must come from an immediately
   preceding command, and commands show their expected result. Fixture-backed
   examples stay synchronized with their checked source.
8. The website keeps its documentation navigation expanded and renders an
   accessible copy control on every code block, including command-output and
   result blocks.
9. On desktop-sized viewports, the page body starts beside the navigation and
   uses a `1200px` maximum width: wider than the theme default for code and
   tables, but still bounded for readable prose. Any unused space remains on
   the far right rather than separating the sidebar from the content.
10. Code and result blocks use a consistent responsive width capped at `56rem`.
    They reserve dedicated right-side space for the copy control, and long lines
    scroll inside the block instead of widening the page.

`docs/index.md` is the user-first project entrance. Its body introduces x2py,
shows the shortest checked source-to-import workflow and its generated function
docstring, and sends the reader into Getting Started. Developer, Maintainer,
and deeper User Guide destinations stay available through site navigation
instead of competing with that first task.

## Audience Lanes

| Lane | Primary reader | Publication | Content |
| --- | --- | --- | --- |
| `user/` | People using x2py | Documentation website after review | Getting Started, guides, tutorials, examples, public reference, support status, FAQ, troubleshooting, changelog |
| `developer/` | People changing x2py | Documentation website after review | Source orientation, implementation maps, testing, coding standards, feature work, contribution workflow |
| `maintainer/` | People governing x2py | Documentation website after review | Documentation policy, design decisions, internal architecture, CI administration, releases, roadmaps |

Pages use their primary audience for placement. A developer may consult a
maintainer design record, but that does not make governance material part of
the developer workflow. Cross-lane links should be exceptional and explain why
the reader is leaving the current lane.

## Reading Order And Cross-Links

The `nav` sequence in `mkdocs.yml` is the canonical reading order. Sequential
User documentation pages may link back to pages the reader has already
completed. They must not link from instructional prose to a later page in that
sequence. Explicit terminal navigation blocks headed `Next` may link forward
because choosing a next destination is their purpose. Outside those blocks,
name the later topic in plain text and say that it is covered later instead of
asking the reader to leave the current task.
`Next` blocks list destinations as bullets, and each bullet includes at least
one Markdown link. If an intended destination page does not exist yet, either
remove the destination until it is useful or create the draft page with
metadata and a TODO section.

Each page includes the behavior, warning, ownership fact, or limitation needed
for its current task. A forward reference never defers a fact needed now.
README documentation lists, lane indexes, and explicit navigation menus are
exceptions because choosing a destination is their purpose. Same-page anchors
and links to source or test evidence do not change documentation reading order.

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
3. for a page in `user/`, `developer/`, or `maintainer/`, that lane's index is
   also reviewed (`user/index.md`, `developer/index.md`, or
   `maintainer/README.md`).

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
X2PY_DOCS_INCLUDE_DRAFTS=1 python3 -m mkdocs serve
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
    getting-started/
    guide/
    tutorials/
    examples/
    reference/
    language-support/
    faq/
    troubleshooting/
    changelog/
  developer/
    index.md
    contributing/
    source and workflow pages
  maintainer/
    README.md
    documentation-architecture.md
    design/
    internal-architecture/
    roadmap/
    CI and release policy
  javascripts/
    code-copy.js
  stylesheets/
    site.css
    code-copy.css
  old_docs/
```

New active pages must be created in one of the three lanes. Website-only static
behavior and presentation assets live in `javascripts/` and `stylesheets/`.
Do not restore top-level topic directories or place maintainer rules beside the
website landing page. Historical `old_docs/` material is never eligible for
website publication.

## Continuous Documentation Quality

- Require metadata for every active page.
- Keep website navigation, repository routing, lane indexes, and physical lanes
  synchronized.
- Reject draft pages and draft-gated lanes from published site navigation.
- Require explicit publication metadata on every active page.
- Check that User documentation does not link forward from instructional prose.
- Treat unsupported-feature placeholders as blocking reminders during feature
  completion.
- Run link, structure, generated-reference freshness, and executable-example
  checks in CI.
