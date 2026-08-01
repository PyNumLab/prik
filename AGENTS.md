# Repository Instructions

The active codebase is entirely Python.
Before starting implementation work, update or read the relevant docs first so the intended public behavior, ownership rules, and limitations are explicit; then implement code and tests to match that documented contract.

Ignore:
- *.f90
- *.f95
- *.for
- *.c
- *.h
- *.json

Do not spend context window or analysis on those files unless explicitly requested.
When asked to change or move an API, import path, command, feature, or behavior, do not add or keep compatibility layers, aliases, shims, fallback paths, or legacy entrypoints unless explicitly requested. A requested change means the old behavior should be removed.
When updating tests, remove obsolete tests that only assert removed/old implementation behavior does not exist. Do not preserve rejection or absence checks for API/features that were intentionally removed unless explicitly requested.

Before `prik/semantics/ir2ast.py` runs, the post-IR policy stage must have completed every semantic decision needed by wrapper generation, including object kind, ownership, transfer, destruction, mutability/writeback, nullability, output projection, release responsibility, contract-value storage mode (`stack`, `heap`, or `alias`), getter behavior, native setter assignment, and Python setter exposure. Bridge and binding generators may only dispatch from those completed decisions into small named implementation methods. They must not infer or override semantic policy from datatype, `intent`, dotted-variable shape, `is_alias`, or local memory checks, and they must not contain a fallback that silently chooses a different behavior. When such a decision is found in bridge or binding code, remove it there and move it into post-IR policy completion. Backend-local helper temporaries may still be created inside the selected implementation method because they are emitted-code details, not semantic policy.

For behavior changes, first try to express the change in completed semantic
policy or the shared wrapper plan. Change binding or bridge lowering only when
the selected plan requires a genuinely new emitted-code mechanism; those
generators should otherwise keep reusing and dispatching existing planned
paths.

After every implementation task, the final summary must include a breakdown of
the stages that actually changed. Relevant stages include parsing, semantic IR
construction, post-IR policy completion, IR-to-AST/lowering, binding
generation, bridge generation, compilation/build integration, and
documentation. For each changed stage, state what behavior or representation
changed there. Do not include unchanged stages or empty stage headings. Also
identify the tests that were added or updated, where they live, what behavior
they cover, and the relevant verification results. When the implementation
reused or improved an existing code path, name that path and explain how it was
reused or changed. The stage breakdown is a required part of the summary, not a
restriction on the rest of it: add any relevant cross-cutting outcomes,
decisions, risks, limitations, verification gaps, or handoff details outside
the stage breakdown when they help explain the implementation.

Changes in `prik/semantics/ir2ast.py`, `prik/codegen/`, and `prik/compiling/` are separated from the rest of the project. For modifications limited to those areas, run only `tests/wrapper` tests unless a broader test run is explicitly requested.
Do not run LAPACK wrapper tests locally unless the user explicitly asks for them. Local verification may run everything else, including BLAS-only real-library tests; leave LAPACK coverage to GitHub Actions by default.
Do not run the full coverage workflow for routine changes. Run focused tests plus the required static-analysis suite. Reserve the complete CI-style coverage workflow for explicit pre-merge or pull-request verification, or when the user specifically requests it.
When investigating coverage failures, mirror the GitHub Actions workflow before deciding the fix: run coverage with `COVERAGE_PROCESS_START=pyproject.toml`, combine parallel data with `python3 -m coverage combine`, then run `python3 -m coverage report`. Do not assume a plain local coverage run matches CI, especially when subprocess tests are involved.
For documentation-only changes that do not modify executable Python code,
runtime behavior, build configuration, or test logic, do not run the complete
static-analysis suite by default. Run the focused documentation checks and
whitespace check instead:
- `python3 -m pytest -q tests/docs/test_examples.py tests/docs/test_structure.py`
- `git diff --check`
Run the complete static-analysis suite when code, tests, build behavior, or
tooling configuration changes, or when explicitly requested for pre-merge or
pull-request verification:
- `python3 -m ruff check .`
- `python3 -m ruff format --check .`
- `bandit -c pyproject.toml -r c_parser fortran_parser semantics prik --severity-level medium --confidence-level medium`
- `vulture`
- `python3 tools/check_radon_policy.py --base-ref auto`
- `radon cc c_parser fortran_parser semantics prik -n C -s --total-average`
- `radon mi c_parser fortran_parser semantics prik -s`
Treat Ruff, Bandit, Vulture, and the Radon policy as blocking. The full Radon complexity and maintainability reports are advisory but must still be run. If a command cannot run because a dependency, network service, or CI-only environment value is unavailable, state that explicitly in the final response.
When you create a commit add this prefix to the message to know that you did push the commit "codex: ..."
