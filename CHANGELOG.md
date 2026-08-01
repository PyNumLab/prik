# Changelog

This file is the canonical record of user-visible PRIK changes. Add changes to
**Unreleased** as they land, then move them into a versioned section during
release preparation. Versions use [Semantic Versioning](https://semver.org/);
release tags add a leading `v` to the package version.

## Unreleased

- No user-visible changes yet.

## 0.1.0 — 2026-08-01

- First public release under the PRIK name.
- Build importable Python extensions from supported Fortran sources.
- Generate, inspect, edit, and rebuild from semantic `.pyi` contracts.
- Expose the `prik` console command and the equivalent `python -m prik`
  module command.
- Report the installed release through `prik --version` and
  `prik.__version__`.
