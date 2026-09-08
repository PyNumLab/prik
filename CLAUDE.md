# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

PRIK (Python Runtime Interop Kit) generates native Python bindings from Fortran
projects: importable CPython extensions plus editable `.pyi` contracts for
reshaping the generated Python API. The active codebase is entirely Python
(`prik/`); Fortran/C fixture and source files (`*.f90`, `*.f95`, `*.for`, `*.c`,
`*.h`) are inputs/outputs of the tool, not implementation — don't spend
analysis effort on them unless explicitly asked to.

This repo also has an `AGENTS.md` with detailed, load-bearing contributor
policy (test philosophy, changelog rules, policy-completion boundary, QA
gating). Read it — the summary below pulls out what matters most day to day,
but AGENTS.md is authoritative for edge cases.

## Commands

Install with dev/QA extras:

```bash
python3 -m pip install -e ".[qa]"
```

Run the full suite:

```bash
PYTHONPATH=. python3 -m pytest -q
```

Run a single test / focused owner (always prefer the narrowest owning path over the full suite):

```bash
python3 -m pytest -q path/to/tests
python3 -m pytest -q path/to/test_file.py::test_name
```

The five independently-collecting suite roots:

```bash
python3 -m pytest -q tests/fortran -m "not real_library"
python3 -m pytest -q tests/c
python3 -m pytest -q tests/docs
python3 -m pytest -q tests/tools
python3 -m pytest -q tests/workflows
```

For documentation-only changes, run only:

```bash
python3 -m pytest -q tests/docs
git diff --check
```

Static analysis suite (blocking for any code/test/build/tooling change; run before pushing):

```bash
python3 -m ruff check .
python3 -m ruff format --check .
python3 tools/check_static_analysis_versions.py
python3 tools/check_codegen_complexity.py   # advisory
python3 -m bandit -c pyproject.toml -r prik --severity-level medium --confidence-level medium
python3 -m vulture
python3 tools/check_radon_policy.py --base-ref auto   # blocking (changed code)
python3 -m radon cc prik -n C -s --total-average       # advisory, still run
python3 -m radon mi prik -s                            # advisory, still run
```

Enable the tracked pre-push hook once per clone (`git config core.hooksPath .githooks`) — it runs the static-analysis gate plus focused doc/wrapper/tools/workflows smoke tests.

Full CI-style coverage (only for explicit pre-merge/PR verification or investigating a coverage failure — mirror this exactly, a plain local `coverage run` does not match CI):

```bash
COVERAGE_PROCESS_START=pyproject.toml PYTHONPATH=. python3 -m coverage run -m pytest -q --randomly-seed=1
python3 -m coverage combine
python3 -m coverage report   # fail_under = 90
```

Run pytest with at most `-n 2` — never `-n 4`, `-n 8`, or `-n auto`. This
machine has 12 cores but only ~7 GB of RAM; each xdist worker loads NumPy
while the Fortran end-to-end tests fork gfortran and cc per test, so higher
parallelism exhausts memory, thrashes swap, and has hard-frozen the machine.
Prefer the narrowest owning test path, and commit verified work promptly
rather than batching it behind a long run.

Don't run LAPACK wrapper tests locally unless explicitly asked (leave to GitHub Actions); ordinary local runs also exclude `real_library` generally. `examples/blas`, `examples/lapack`, `examples/fftpack`, `examples/minpack` are full-library correctness projects with their own workflows.

Alternate-compiler toolchain lane (when changing compiler portability/native generation):

```bash
python3 tools/run_fortran_toolchain_lane.py --compiler=/path/to/compiler
```

## Architecture

PRIK is a strict pipeline: source facts flow forward through owned stages, and
**meaning moves forward only** — a downstream stage implements an upstream
decision, it never reinterprets or overrides it.

```
preprocessing/  ->  parsers/  ->  semantics/  ->  policy/  ->  planning/  ->  codegen/  ->  printers/  ->  compiler/  ->  runtime/
```

| Package | Owns |
| --- | --- |
| `preprocessing/` | Source prep, provenance, includes, compiler-derived target/type probes |
| `parsers/` | Syntax facts only (`fortran/`, `pyi/` — a deferred `c/` frontend exists but isn't the published contributor architecture) |
| `semantics/` | Language-neutral semantic IR (`SemanticModule`); shared meaning, not a Python API or emitted code |
| `policy/` | **Every** interoperability decision: object kind, ownership, transfer, destruction, mutability/writeback, nullability, output projection, release responsibility, storage mode (stack/heap/alias), getter/setter behavior, support |
| `planning/` | Projects policy-complete IR into a deterministic, backend-neutral `ModulePlan` (`WrapperPlanner.build()`) — orders/names/validates, invents nothing |
| `codegen/` | Dispatches the plan into named C-binding and Fortran-bridge lowering mechanisms; backend scalar projection |
| `printers/` | Serializes formed nodes to C/Fortran/`.pyi` text — no behavior decisions |
| `compiler/` | Compiler commands, compile objects, native-support install, linking |
| `runtime/` | Python runtime objects + bundled native support used by generated extensions |
| `pipeline/` | End-to-end build orchestration (`build.py`, `wrapper.py`, `pyi.py`) tying the stages together |
| `contracts/` | Public names usable in semantic `.pyi` contracts (deliberately public — its import path is part of `.pyi` syntax) |
| `naming/` | Shared public-name and generated-symbol policy |
| `utilities/` | Stage-neutral helpers only (parsing/normalization/rendering/evaluation/visitor) |

Two input routes converge at `SemanticModule` and share everything after it:
Fortran source (`preprocessing` → `parsers/fortran` → `semantics/fortran2ir.py`)
and semantic `.pyi` contracts (`parsers/pyi` → `semantics/pyi2ir.py`).

**The hard boundary is before `WrapperPlanner.build()`.** By that point policy
must be fully decided. Binding/bridge generators (`codegen/`) must never infer
or override policy from datatype, Fortran `intent`, alias shape, storage
layout, or a local memory check, and must not add a silent fallback — if a
decision is missing, that's a bug in `policy/`, not something to patch around
in codegen. When changing behavior, prefer expressing it in completed policy
or the shared wrapper plan; touch binding/bridge lowering only when the plan
already requires a genuinely new emitted-code mechanism.

**Deciding binding vs. bridge, or any ABI question:** ask how it would work for
a `bind(C)` procedure, where there is no bridge. A direct entrypoint has only
the binding and the user's C ABI symbol, so whatever the direct route must do
is binding-owned; the bridge owns exactly the remainder that makes an ordinary
non-`bind(C)` procedure reachable through the same completed plan. When a form
*cannot* be `bind(C)` at all — e.g. a deferred-length `character(len=:)` dummy,
which the standard rejects there because `bind(C)` character dummies must have
length 1 — that proves a generated Fortran adapter is mandatory and names what
it must construct. See AGENTS.md for the full rule.

Array declaration expressions specifically cross packages in a fixed order:
`utilities/declaration_expressions.py` (parse/normalize text) → `semantics/`
(record native callable provenance) → `policy/` (complete support) →
`codegen/` (consume the completed plan only).

Root entry points: `prik.__init__` exposes `build_fortran_extension`,
`build_pyi_extension`, and `__version__` only; `prik/cli.py` is the `python3 -m prik`
dispatcher into the same stage owners. Deeper docs: `docs/developer/architecture.md`,
`docs/developer/codebase-map.md`, `docs/developer/packages/*.md`.

## Test tree

Tests mirror the pipeline and are organized `tests/<language>/<documented-feature>/<owning-stage>/`
(stage names: `parsing/`, `probes/`, `preprocessing/`, `semantics/`, `policy/`,
`codegen/`, `printers/`, `compiling/`, `pipeline/`, `runtime/`, `end_to_end/`).
Give each test one primary invariant, placed at the earliest stage that can
prove it; add `end_to_end/` only when generation/compilation/import/runtime
behavior contributes a distinct claim. Genuinely internal (non-public-behavior)
mechanisms live under `tests/fortran/infrastructure/<production-package>/`,
mirroring the production module. See `tests/README.md` for the full stage
table and markers (`fortran_end_to_end`, `real_library`, `toolchain_smoke`, `property`, `regression`, `slow`, `benchmark`).

## Working conventions (see AGENTS.md for full detail)

- Update `CHANGELOG.md` under **Unreleased** for any user/maintainer-visible
  change (public APIs, features, examples, CI/build workflow, benchmark
  methodology, documented limitations). Skip it for invisible internal cleanup.
- When asked to move/change an API, import path, command, or behavior, remove
  the old path — do not add compatibility shims, aliases, or fallbacks unless
  explicitly asked to keep them.
- Tests are evidence for a named invariant (observable behavior, a public API,
  a documented diagnostic/serialized format, ABI/ownership/lifetime/build
  behavior, a stage boundary, or tooling-consumed structure) — not a freeze on
  prose, private names, file inventories, or incidental layout. Remove tests
  that only pin removed behavior; don't add tests that only prevent refactors.
- After finishing an implementation task, summarize which pipeline stages
  actually changed (parsing / semantic IR / policy / planning / codegen /
  bridge / compilation / docs) and what changed there, plus the tests
  touched and how they were verified.
