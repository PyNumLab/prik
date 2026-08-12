---
title: Release Process
audience: maintainers
prerequisites: CI/CD, changelog
related: ci.md, quality-assurance.md
status: maintained
publication: reviewed
---

# Release Process

PRIK publishes source distributions and universal Python wheels to PyPI from a
GitHub Release. GitHub Actions authenticates with PyPI through OpenID Connect;
the repository does not store a long-lived PyPI token.

## Package Identity

The public names are fixed as follows:

| Surface | Name |
| --- | --- |
| PyPI distribution | `prik` |
| Python package | `prik` |
| Console command | `prik` |
| Module command | `python -m prik` |
| GitHub repository | `PyNumLab/prik` |

Release tags use `v<version>`, for example `v0.1.0`. The version without the
leading `v` must exactly match `[project].version` in `pyproject.toml`.

## One-Time Trusted Publisher Setup

Before the first release, add a pending trusted publisher at
<https://pypi.org/manage/account/publishing/> with these exact values:

| PyPI field | Value |
| --- | --- |
| PyPI project name | `prik` |
| GitHub owner | `PyNumLab` |
| Repository name | `prik` |
| Workflow name | `publish-to-pypi.yml` |
| Environment name | `pypi` |

The pending publisher creates the PyPI project on the first successful
publication. It does not reserve the name before that upload.

In the GitHub repository, create an environment named `pypi` under **Settings
> Environments**. Add a required reviewer so publication pauses for explicit
approval. Do not add a PyPI API token or password to GitHub secrets.

## Prepare a Release

1. Choose a version that does not already exist on PyPI.
2. Set `[project].version` in `pyproject.toml`.
3. Move the user-visible entries from **Unreleased** into a versioned section
   in the repository-root [`CHANGELOG.md`](../../../CHANGELOG.md).
4. Run the focused package checks and the repository's required static
   analysis. Let GitHub Actions run the complete cross-platform suite.
5. Merge the release preparation through the normal review process and wait
   for the `main` branch checks to pass.

Build the same artifacts locally when reviewing the release candidate:

```bash
python3 -m pip install --upgrade build twine
python3 -m build --outdir .artifacts/dist
python3 -m twine check .artifacts/dist/*
```

`.artifacts/dist/` must contain one source distribution and one universal
wheel. The hidden `.artifacts/` tree contains reproducible local and CI output;
only its ignore placeholder is maintained source. The repository-root
`setup.cfg` also directs setuptools' temporary `.egg-info` metadata into that
hidden tree. The source distribution must include the repository-root
`CHANGELOG.md`. Install the wheel in a fresh virtual environment and verify
`prik --version`,
`prik.__version__`, `prik --help`, and `python -m prik --help` before creating
the release.

## Publish

Create a GitHub Release from the exact reviewed commit and use a tag matching
the project version, such as `v0.1.0`. Use that version's section from
[`CHANGELOG.md`](../../../CHANGELOG.md) as the release notes. Publishing the
GitHub Release triggers `.github/workflows/publish-to-pypi.yml`.

The workflow builds and checks the artifacts in an unprivileged job. A
separate `pypi` environment job downloads only those artifacts, requests an
OpenID Connect identity token, and uploads them with PyPA's publishing action.
Approve that environment deployment only after checking the tag, commit, and
artifact job.

PyPI versions and files are immutable. Never delete and recreate a tag to
replace a published version; fix the problem and publish a new version.

## Verify the Published Package

After the workflow succeeds, use a clean environment so a source checkout
cannot mask packaging errors:

```bash
python3 -m venv /tmp/prik-release-check
/tmp/prik-release-check/bin/python -m pip install --upgrade pip
/tmp/prik-release-check/bin/python -m pip install prik==0.1.0
/tmp/prik-release-check/bin/prik --version
/tmp/prik-release-check/bin/python -c 'import prik; print(prik.__version__)'
/tmp/prik-release-check/bin/prik --help
/tmp/prik-release-check/bin/python -m prik --help
```

Confirm the version and both distribution files on
<https://pypi.org/project/prik/>. If a release is unsafe to install, yank it on
PyPI and publish a corrected version; yanking is preferable to deleting files
because it preserves reproducibility for exact version pins.
