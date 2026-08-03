# Contributing to PRIK

Thanks for helping make native Python interfaces easier to build.

## Get started

Create a focused branch and install PRIK with its development tools:

```bash
python3 -m pip install -e ".[qa]"
```

Run the smallest relevant test while you work:

```bash
PYTHONPATH=. python3 -m pytest -q path/to/tests
```

## Before opening a pull request

- Add or update tests for changed behavior.
- Update the user guide when the public API, CLI, or supported behavior changes.
- Add user-visible changes to **Unreleased** in `CHANGELOG.md`.
- Run Ruff and the relevant tests:

```bash
python3 -m ruff check .
python3 -m ruff format --check .
PYTHONPATH=. python3 -m pytest -q path/to/tests
```

Keep the pull request easy to review: explain the problem, the solution, and
how you verified it. All required GitHub checks must pass before merge.

For the complete workflow, see the
[development guide](docs/developer/development-workflow.md) and
[quality-assurance guide](docs/developer/quality-assurance.md).

## License

Contributions are accepted under the [MIT License](LICENSE). By submitting a
contribution, you confirm that you have the right to license it under those
terms.
