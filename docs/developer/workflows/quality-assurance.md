---
title: Quality Assurance
audience: developers, maintainers, contributors
prerequisites: repository checkout, QA dependencies
related: contributing.md, ../testing-strategy.md, ci.md
status: maintained
publication: draft
---

# Quality Assurance

This page records the active quality stack and commands. Historical rollout
logs and completed tool-adoption checklists belong in Git history, not in the
current contributor workflow.

## Install

```bash
python3 -m pip install -e ".[qa]"
python3 tools/check_static_analysis_versions.py
```

## Active Cadence

| Cadence | Evidence |
| --- | --- |
| Inner loop | Smallest owning pytest target and Ruff on changed code |
| Local pre-push | Blocking static analysis, focused documentation smoke, one compiled scalar-wrapper smoke, `tests/tools/`, and `tests/workflows/` |
| Pull request | Static analysis, compiler smoke, Python matrix, project coverage, real libraries, performance/docs, aggregate required check |
| Manual discovery | Deep Hypothesis fuzz profile and advisory complexity reports |
| Dependency change or annual review | Dependency vulnerability review |

The one stable required ruleset context is:

```text
Pull Request / Validation · all required checks
```

If the workflow or job display name changes, update the repository ruleset;
do not keep an alias job for the old name.

## Focused And Documentation Checks

Run the narrowest behavioral owner first:

```bash
python3 -m pytest -q path/to/owning/tests
```

Documentation-only changes that do not alter Python, tests, build
configuration, or tooling use:

```bash
python3 -m pytest -q tests/docs
git diff --check
```

When Python code, test logic, build behavior, or tools change, run the complete
blocking and advisory static suite:

```bash
python3 -m ruff check .
python3 -m ruff format --check .
python3 tools/check_static_analysis_versions.py
python3 tools/check_codegen_complexity.py
python3 -m bandit -c pyproject.toml -r prik --severity-level medium --confidence-level medium
python3 -m vulture
python3 tools/check_radon_policy.py --base-ref auto
python3 -m radon cc prik -n C -s --total-average
python3 -m radon mi prik -s
```

Ruff, Bandit, Vulture, version checks, and the changed-code Radon policy are
blocking. The codegen complexity checker and full Radon reports are advisory;
review their findings instead of changing correct behavior solely to satisfy a
structural preference. If automatic Radon base detection lacks CI SHA metadata
locally, rerun with `--base-ref main` and report that fact.

## Coverage And Test-Order Reproduction

Do not run the complete coverage workflow for routine changes. When
investigating a CI coverage failure, mirror subprocess collection exactly:

```bash
COVERAGE_PROCESS_START=pyproject.toml \
PYTHONPATH=. \
python3 -m coverage run -m pytest -q --randomly-seed=1
python3 -m coverage combine
python3 -m coverage report
```

The blocking project coverage target is 90%. Codecov patch status is
informational, but new reachable behavior still needs focused tests.

Reproduce an order-dependent failure with the seed from CI:

```bash
python3 -m pytest -q --randomly-seed=<seed-from-failing-run>
```

## Compiler And Property Evidence

Run a configured alternate-compiler lane with:

```bash
python3 tools/run_fortran_toolchain_lane.py --compiler=/path/to/ifx
python3 tools/run_fortran_toolchain_lane.py --compiler=/path/to/flang
```

`--plan` prints the selected tests without running them. CI currently pins
IFX/ICX 2026.1.1 and Flang/Clang 22.1.8 as evidence versions, not declared
minimum versions.

Run property and deep fuzz profiles with:

```bash
python3 -m pytest -q -m property --hypothesis-profile=ci
HYPOTHESIS_PROFILE=fuzz python3 -m pytest -q -m fuzz --hypothesis-show-statistics
```

Minimize an actionable fuzz failure and preserve it as a focused regression in
the owning feature/stage suite.

## Tool Responsibilities

| Tool | Role |
| --- | --- |
| pytest and coverage.py | Behavioral regression and project coverage |
| pytest-randomly | Stable-seed order-coupling detection |
| Hypothesis | Generated parser, semantic, and codegen invariants |
| Ruff | Linting, formatting, modernization, and bounded McCabe checks |
| Bandit | Medium-confidence/severity security boundary review |
| Vulture | Dead-code detection with narrow exclusions |
| Radon | Blocking changed-hotspot policy plus advisory project reports |
| GitHub Actions | Reproducible shared compiler, platform, library, benchmark, docs, and release evidence |

Mutation testing and pre-commit are not part of the active stack. The tracked
`.githooks` pre-push hook is the supported local automation boundary.

## Real Libraries And Verification Limits

Ordinary local suites exclude `real_library`. BLAS, FFTPACK, and MINPACK may be
run through their documented example workflows. LAPACK wrapper tests remain a
GitHub Actions responsibility unless explicitly requested locally.

GitHub Actions writes path-aware JUnit reports and prints failed pytest node
IDs at the end of failed matrix logs. The real-library lane builds and tests
the complete maintained BLAS, LAPACK, FFTPACK, and MINPACK examples using their
documented entrypoints.
