# Maintainer Tool Tests

`tests/tools/` owns behavior tests for repository-maintained commands and CI
support scripts below `tools/`. These tests exercise arguments, output, error
handling, and exit status; they do not freeze test or workflow organization.

Run this owner with:

```bash
python3 -m pytest -q tests/tools
```
