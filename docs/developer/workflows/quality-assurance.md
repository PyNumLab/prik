---
title: Quality Assurance
audience: developers, maintainers, contributors
prerequisites: repository checkout, QA dependencies
related: contributing.md, ../testing-strategy.md, ci.md
status: maintained
publication: reviewed
---

# Quality Assurance

This page defines the local evidence expected before a pull request. Start
with the smallest owner; CI provides broader platform and library evidence.

## Install

```bash
python3 -m pip install -e ".[qa]"
python3 tools/check_static_analysis_versions.py
```

## Routine Verification

Run the narrowest behavioral owner first:

```bash
python3 -m pytest -q path/to/owning/tests
```

For documentation-only changes:

```bash
python3 -m pytest -q tests/docs
git diff --check
```

For Python, test, build, or tool changes, run focused tests and the static
suite:

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
blocking. The codegen review and full Radon reports are advisory. If automatic
Radon base detection lacks CI SHA metadata, rerun with `--base-ref main`.

## Broader Evidence

Do not run complete coverage for routine changes. When investigating a CI
coverage failure, mirror CI collection:

```bash
COVERAGE_PROCESS_START=pyproject.toml \
PYTHONPATH=. \
python3 -m coverage run -m pytest -q --randomly-seed=1
python3 -m coverage combine
python3 -m coverage report
```

The project coverage target is 90%. Reproduce an order-dependent failure with
the seed from CI:

```bash
python3 -m pytest -q --randomly-seed=<seed-from-failing-run>
```

Run an alternate compiler lane when changing compiler portability or native
generation:

```bash
python3 tools/run_fortran_toolchain_lane.py --compiler=/path/to/ifx
python3 tools/run_fortran_toolchain_lane.py --compiler=/path/to/flang
```

Run property or fuzz profiles when changing generated invariants or
investigating a failure:

```bash
python3 -m pytest -q -m property --hypothesis-profile=ci
HYPOTHESIS_PROFILE=fuzz python3 -m pytest -q -m fuzz --hypothesis-show-statistics
```

Minimize an actionable fuzz failure and retain it as a focused regression.

## Limits

Native changes need focused codegen evidence and relevant end-to-end coverage.
Ordinary local runs exclude `real_library`. BLAS, FFTPACK, and MINPACK have
their own example workflows; leave LAPACK wrapper tests to GitHub Actions
unless explicitly requested. See [Pull request checks](ci.md) for hosted
coverage, compiler, real-library, benchmark, and documentation evidence.
