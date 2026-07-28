---
title: Quality Assurance
audience: developers, contributors
prerequisites: repository checkout, QA dependencies
related: testing-strategy.md, development-workflow.md
status: maintained
publication: draft
---

# Quality Assurance

Last reviewed: 2026-06-20

This project uses a staged Python QA stack. Fast bug-focused checks run on pull
requests, while the separate `Fuzz` workflow runs deeper Hypothesis discovery
on schedule or by manual dispatch.

The selected active quality stack is adopted. Scheduled workflow review and
future Ruff/Radon threshold ratchets are ongoing maintenance, not unfinished
rollout work. Mutation testing and pre-commit are not part of the active stack.

## Active Cadence

| Cadence | Tools |
| --- | --- |
| Pull request and protected-branch push | pytest, stable-seed pytest-randomly, Ruff, Bandit, Vulture, staged Radon policy |
| Main-branch push and requested coverage run | coverage.py report from the Python 3.12 test job |
| Weekly and manual dispatch | `Fuzz` workflow with Hypothesis fuzz profile |
| Manual triage | Full Radon reports and low-severity Bandit review |
| Annual dependency review | Dependency vulnerability audit outside the routine per-change gate |

## Install

Install the package plus the QA toolchain:

```bash
python -m pip install -e ".[qa]"
python tools/check_static_analysis_versions.py
```

If your shell only exposes `python3`, use:

```bash
python3 -m pip install -e ".[qa]"
python3 tools/check_static_analysis_versions.py
```

## Local Commands

Fast inner loop:

```bash
pytest -q
python -m ruff check .
python -m ruff format .
```

CI-shaped local coverage run:

```bash
HYPOTHESIS_PROFILE=ci \
COVERAGE_PROCESS_START=pyproject.toml \
PYTHONPATH=. \
python -m coverage run -m pytest -q --randomly-seed=1
python -m coverage combine
python -m coverage report
```

For subprocess coverage investigations, mirror that command shape before
deciding a fix. A plain local coverage run can miss subprocess data.
GitHub Actions runs ordinary PR tests without coverage overhead. During the
wrapper-plan migration, every Python version excludes the full BLAS/LAPACK
real-library wrapper test while retaining general native-bundle coverage.
One separate Python 3.12 job runs the full BLAS and LAPACK nodes together. A
pull request may use the `ignore-real-library-wrappers` label to skip that
expensive job without disabling the ordinary Python-version matrix.
Pushes to `main` always run the remaining Python 3.12 test job under coverage
and publish the coverage report. Add the `run-coverage` PR label, or pass
`coverage: true` to the reusable workflow, to request the same coverage gate
outside the main branch.

Every matrix test run also writes a path-aware JUnit report. If pytest fails, the final
workflow step reads that report and prints a compact `Failed pytest nodes`
section containing every failed test node ID, including parametrization such
as `[source]` or `[generated-pyi]`. This summary is intentionally separate from
pytest's traceback output so failed names remain easy to find at the end of a
long GitHub Actions log. If pytest exits before producing a readable report,
the final step says that no report was available instead of hiding the failure.

Reproduce an order-dependent failure from the stable CI seed:

```bash
pytest -q --randomly-seed=<seed-from-failing-run>
```

Run property and fuzz tests:

```bash
pytest -q -m property --hypothesis-profile=ci
HYPOTHESIS_PROFILE=fuzz pytest -q -m fuzz --hypothesis-show-statistics
```

Run security checks:

```bash
python -m bandit -c pyproject.toml -r x2py --severity-level medium --confidence-level medium
```

Run dead-code and complexity checks:

<!-- X2PY_C_DOCS_START
```bash
python -m vulture
python3 tools/check_radon_policy.py &#45;&#45;base-ref "$(git merge-base origin/main HEAD)"
python -m radon cc x2py -n C -s &#45;&#45;total-average
python -m radon mi x2py -s
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
The Radon policy check is blocking. It prevents the reviewed C-or-worse hotspot
average from rising above `19.01` and rejects new or worsened changed production
blocks above complexity `20`. Local runs must supply the pull-request merge base
explicitly as shown above. CI may use `&#45;&#45;base-ref auto`, which reads the event's
base SHA from the environment and fails if no usable SHA is available. Full
Radon reports remain advisory for refactor planning.
X2PY_C_DOCS_END -->

## Tool Decisions

### pytest And coverage.py

**Role:** behavioral regression backbone and branch-coverage floor.

**Evidence:** recorded full-suite baseline is `3497 passed`; combined
subprocess branch coverage is `95.34%`, above the configured `95%` gate.

**Decision:** keep as required baseline project gates.

### pytest-randomly

**Role:** catches hidden test-order coupling and makes failures reproducible
with seeds.

**Evidence:** normal CI uses `--randomly-seed=1`, so order is shuffled but
reproducible.

**Decision:** keep stable-seed PR CI. The changing-seed scheduled job was
removed as redundant maintenance overhead.

### Hypothesis

**Role:** generates edge cases for parsers, AST transforms, semantic IR, and
code generation.

<!-- X2PY_C_DOCS_START
**Bugs found:** generated code-generation cases exposed quoted `SourceName(...)`
emission. Generated preprocessing inputs also aligned raw Fortran and C macro
handling around compiler-required errors.
X2PY_C_DOCS_END -->

**Decision:** keep bounded property tests in normal test coverage and longer
fuzz profiles on schedule/manual dispatch.

### Ruff

**Role:** fast linting and formatting for undefined names, unused imports,
suspicious patterns, modernization, simplified control flow, and high McCabe
complexity.

**Bugs or issues found:** raw regex issues, formatting drift, and static-risk
maintenance debt. These are static-risk findings, not runtime defects.

**Decision:** keep as a blocking gate. Line-length diagnostics remain
intentionally unselected because wrapping parser diagnostics and embedded test
sources would add noise without improving correctness.

### Bandit

**Role:** security scanning for subprocess, filesystem, deserialization, and
credential-like patterns.

**Evidence:** no medium- or high-severity findings. Reviewed low-severity
findings are parser sentinel/template tokens and intentional argv-based
compiler/preprocessor subprocess calls without shell execution.

**Decision:** keep blocking at medium confidence/severity in CI. Re-review the
full low-severity report after subprocess-boundary changes.

### Dependency Vulnerability Review

**Role:** dependency vulnerability scanning.

**Evidence:** routine per-change scans were noisy and slow relative to the
dependency churn in this project.

**Decision:** do not run dependency vulnerability scanning as a pull-request or
local per-change gate. Revisit dependencies during an annual manual review or
when adding/upgrading runtime dependencies.

### Vulture

**Role:** dead-code detection.

**Bugs or issues found:** removed dead Fortran parser parameters and unused test
lambda parameters reported by CI.

**Decision:** keep blocking in CI with narrow exclusions.

### Radon

**Role:** complexity and maintainability tracking.

<!-- X2PY_C_DOCS_START
**Evidence:** reviewed average complexity is `C (18.95)`. The staged policy
allows unchanged legacy hotspots while blocking new or worsened changed
production hotspots above complexity `20`.
X2PY_C_DOCS_END -->

**Bugs or issues found:** Radon found maintainability hotspots. CI also exposed
that the first staged policy was too strict for unchanged legacy hotspots; the
policy was corrected.

**Decision:** keep `tools/check_radon_policy.py` blocking and keep full Radon
reports advisory/manual.

### GitHub Actions

**Role:** reproducible CI and scheduled discovery.

**Bugs or issues found:** recent remote quality runs found Ruff raw-regex
issues, Ruff formatting drift, Vulture unused test parameters, and the
too-strict Radon policy.

**Native artifact cache:** dedicated Python 3.12 BLAS and LAPACK jobs restore a
separate runner-local native cache for each library before executing the full
wrapper test. The ordinary pytest matrix excludes that full corpus while
retaining the lighter native-bundle tests. Requested coverage runs still
collect Python 3.12 coverage data; a final coverage job combines that artifact
and uploads the XML report.

**Failure reporting:** each pytest matrix invocation writes
`pytest-results.xml`; the final failure-only step runs
`tools/print_pytest_failures.py` so all failed node IDs appear together at the
end of the job log.

**Decision:** keep. Review scheduled results and record actionable failures
until fixed.

## Historical Mutation Findings

Mutation testing was useful during rollout, but it is no longer an adopted
tool. Do not keep `mutmut` as a regular dependency, workflow, or local wrapper.
A future annual mutation audit can be run outside the normal QA stack if
needed.

Keep the ordinary regression tests and fixes that came from it:

- Fortran project namespace collection respecting the requested encoding;
- direct Fortran parser contracts for diagnostics, forwarding, registries,
  ownership, provenance, source locations, boundaries, and loop progress.

<!-- X2PY_C_DOCS_START
- duplicate typedef-cycle diagnostic coverage;
- cycle-safe union-by-value diagnostics;
X2PY_C_DOCS_END -->

## Test Organization

- Unit tests: keep narrow behavior tests near existing domain folders such as
  `tests/parser`, `tests/semantics`, and `tests/pyi`.
- Regression tests: add focused tests next to the subsystem that failed. Mark
  with `@pytest.mark.regression` when useful.
- Property tests: put generated invariant tests in `tests/property`.
- Fuzz-like parser tests: keep bounded generators in `tests/property`, mark
  with `@pytest.mark.fuzz`, and run with the `fuzz` Hypothesis profile.

Good invariants for this codebase:

- parsing the same source twice produces the same JSON/dict representation;
- generated declarations preserve name order and source locations;
- semantic conversion is deterministic for equivalent parser models;
- Pyi emission can be parsed back into equivalent semantic IR for supported
  subsets;
- malformed input raises parser-owned diagnostic exceptions, not arbitrary
  exceptions.

## Adoption Status

Full adoption for the selected stack means:

- fast PR gates are blocking and stable;
- scheduled/manual fuzzing exists;
- Ruff baseline ignores are removed or deliberately retained with a reason;
- Radon has a documented blocking policy for new or materially changed code;
- scheduled workflow failures have a documented triage path.

Current status by area:

| Area | Status | Explanation |
| --- | --- | --- |
| Fast pull-request gates | Complete for adoption | Tests, coverage, Ruff, Bandit, Vulture, and staged Radon are wired as blocking gates. |
| Property and fuzz testing | Complete for adoption | Current parser, AST, semantic-IR, and code-generation invariants exist; future failures still need regression tests. |
| Dead-code detection | Complete for adoption | Vulture is clean and blocking; future public API additions should keep exclusions narrow. |
| Security and dependency scanning | Complete for adoption | Bandit is blocking; dependency vulnerability review is annual/manual or tied to dependency changes. |
| Complexity tracking | Complete for adoption | The staged Radon policy is blocking in CI; future hotspot decomposition can ratchet thresholds further. |
| Scheduled workflow triage | Complete for adoption | Jobs exist and the triage process is documented; scheduled failures remain ordinary maintenance. |

Ongoing maintenance:

1. Review scheduled workflow results regularly and record actionable failures
   until fixed.
2. Lower Ruff/Radon complexity thresholds after hotspot refactors make that
   safe.

## Scheduled Workflow Triage

The `Fuzz` workflow runs deeper discovery every Monday and by manual dispatch:

1. Re-run a failing job once to separate actionable failures from transient
   runner or package-index failures.
2. Reproduce actionable fuzz failures with the logged Hypothesis profile and
   save minimized examples as focused regression tests.
3. Record each actionable scheduled failure here or in the relevant issue until
   the regression test and fix pass.

## Progress Log

| Date | Area | Result | Follow-up |
| --- | --- | --- | --- |
| 2026-05-31 | Initial stack integration | Added configuration, CI, documentation, and Hypothesis tests. | Continue staged strictness rollout. |
| 2026-05-31 | Bandit | Reviewed low-severity findings and confirmed no medium- or high-severity findings. | Re-review when command trust boundaries change. |
| 2026-05-31 | Hypothesis code generation | Added generated native-name escaping, stable synthetic-import ordering, and semantic-IR-to-Pyi parse-back invariants; fixed quoted `SourceName(...)` emission. | Keep storing minimized failures. |
| 2026-06-01 | Ruff formatting rollout | Formatted the historical Python tree and changed CI to `ruff format --check .`. | Continue complexity-policy ratchets. |
| 2026-06-01 | Radon and Ruff complexity policy | Added `tools/check_radon_policy.py`, made the staged Radon policy blocking in CI, and lowered Ruff McCabe from `50` to `45`. | Continue hotspot refactors and later threshold ratchets toward `20`. |
| 2026-06-02 | Historical mutation-derived tests | Added direct Fortran parser contracts and fixed the directory namespace encoding bug. | Keep the tests as normal regression coverage. |
| 2026-06-03 | Manual Quality workflow review | Reviewed workflow run `26832679820`: fuzz passed, changing random-order pytest passed, static analysis exposed Ruff fixes, and full-project mutation exceeded the `3h` Actions limit. | Mutation was removed from active adoption; scheduled fuzz moved to its own workflow. |
| 2026-06-03 | Quality workflow triage | Reviewed latest Quality runs; run `26856679038` for `remove mutmut` completed successfully. | No actionable scheduled or PR quality failure remains. |

<!-- X2PY_C_DOCS_START
| 2026-06-03 | Final active-stack cleanup | Consolidated quality docs, removed mutation and pre-commit from the active stack, restored the C parser golden generator, and regenerated C parser goldens. | Treat scheduled review and threshold ratchets as ongoing maintenance. |
X2PY_C_DOCS_END -->

## References

- Ruff configuration: https://docs.astral.sh/ruff/configuration/
- Pytest configuration: https://docs.pytest.org/en/latest/reference/customize.html
- Coverage subprocess behavior: https://coverage.readthedocs.io/en/latest/config.html
- Hypothesis settings profiles: https://hypothesis.readthedocs.io/en/latest/tutorial/settings.html
- Vulture configuration: https://pypi.org/project/vulture/
- Radon command line: https://radon.readthedocs.io/en/stable/commandline.html
- Bandit configuration: https://bandit.readthedocs.io/en/latest/config.html
- pytest-randomly: https://github.com/pytest-dev/pytest-randomly
