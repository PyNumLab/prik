# Workflow Tests

`tests/workflows/` owns exceptional safety checks for automation under
`.github/workflows/`. Add a workflow test only when it protects a concrete,
costly risk that the workflow service itself will not reliably expose before
damage occurs. Do not use this directory to freeze job names, test paths, or
the current CI organization.

Run this owner with:

```bash
python3 -m pytest -q tests/workflows
```
