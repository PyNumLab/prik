---
title: CI/CD
audience: maintainers
prerequisites: testing strategy
related: ../developer/testing-strategy.md, release-process.md
status: planned-documentation
publication: draft
---

# CI/CD

GitHub Actions owns repository quality checks and the reviewed-documentation
deployment. The documentation workflow builds the same filtered MkDocs site
that maintainers can preview locally, uploads the generated `site/` directory,
and deploys it through GitHub Pages.

## Documentation Publication

The `Documentation` workflow runs for relevant pull requests, pushes to
`main`, and manual dispatches. Pull requests run the documentation tests and a
strict production build without deploying. A push to `main` runs those checks
and deploys the reviewed site when GitHub Pages is configured to use GitHub
Actions.

Enable the repository once through **Settings > Pages > Build and deployment >
Source > GitHub Actions**. Then open **Actions > Documentation > Run workflow**,
select `main`, and run it. Later documentation changes deploy automatically
after they are merged or pushed to `main`; maintainers do not build or upload
`site/` themselves.

Before changing a page to `publication: reviewed`, preview the production view
with `python3 -m mkdocs serve`. Use
`X2PY_DOCS_INCLUDE_DRAFTS=1 python3 -m mkdocs serve` to review unpublished
pages with their draft warning. The lane index must also be reviewed before a
page in that lane can enter the deployed artifact.

## TODO

- TODO: Document the complete current CI quality gates and scheduled jobs.
- TODO: Link coverage troubleshooting to the maintained quality page.
