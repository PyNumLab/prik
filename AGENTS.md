# Repository Instructions

The active codebase is entirely Python.
Before starting implementation work, update or read the relevant docs first so the intended public behavior, ownership rules, and limitations are explicit; then implement code and tests to match that documented contract.

Update `CHANGELOG.md` under **Unreleased** whenever a change adds or changes
user- or maintainer-visible behavior, public APIs, supported features,
examples, build or CI workflows, benchmark methodology, or documented
limitations. Keep entries concise and outcome-focused; do not add release
notes for internal cleanup that has no visible effect.

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

Treat tests as evidence for a named invariant, not as specifications merely
because they already exist. Add or retain automated tests when they protect at
least one of the following:

- externally observable behavior or a public API;
- a documented diagnostic or serialized/generated format;
- ABI, ownership, lifetime, memory-safety, build, or release behavior;
- a stage handoff or architectural boundary whose violation would allow a
  downstream stage to make an upstream decision; or
- repository structure that is directly consumed by tooling.

Do not add tests whose only purpose is to freeze prose, wording, heading or
section order, private class or function names, complete file inventories,
dataclass field inventories, exact internal call order, preferred inheritance,
or incidental directory/module layout. Those are recommendations for
contributor review unless the user explicitly promotes one to a maintained
contract. Unit tests may construct internal models when their behavior or
completed state is the invariant, but they should not assert implementation
shape just to prevent refactoring.

When an existing test fails after an intentional change, identify the behavior
or risk it was meant to protect before changing production code. Keep or
rewrite the test when that invariant remains a contract; remove it when it only
records the previous implementation or a recommendation. Do not change correct
behavior solely to satisfy a brittle test.

The agent owns the review work that is not delegated to rigid tests. Before and
after a refactor, compare the affected public behavior and stage outputs. When
editing documentation, examples, diagnostics, or generated text, preserve the
existing meaning, behavior, and wording as much as the request permits; inspect
the diff and run the affected example or focused command when practical. Treat
illustrative wording and demonstration output as review recommendations unless
they are explicitly documented as stable formats. A command/result pair shown
in a package guide must remain factual: run the command and compare stable
output with the page, or validate only the displayed invariant when the output
is an excerpt or depends on the active target. Do not duplicate that expected
output in a separate test inventory.

Before wrapper planning begins in `prik/planning/planner.py`, the
post-IR policy stage must have completed every semantic decision needed by
wrapper generation, including object kind, ownership, transfer, destruction,
mutability/writeback, nullability, output projection, release responsibility,
contract-value storage mode (`stack`, `heap`, or `alias`), getter behavior,
native setter assignment, and Python setter exposure. Bridge and binding
generators may only dispatch from those completed decisions into small named
implementation methods. They must not infer or override semantic policy from
datatype, `intent`, dotted-variable shape, `is_alias`, or local memory checks,
and they must not contain a fallback that silently chooses a different
behavior. When such a decision is found in bridge or binding code, remove it
there and move it into post-IR policy completion. Backend-local helper
temporaries may still be created inside the selected implementation method
because they are emitted-code details, not semantic policy.

For behavior changes, first try to express the change in completed semantic
policy or the shared wrapper plan. Change binding or bridge lowering only when
the selected plan requires a genuinely new emitted-code mechanism; those
generators should otherwise keep reusing and dispatching existing planned
paths.

To answer an ABI question, or to decide whether something belongs in the
binding or in the Fortran bridge, first ask: **how would this work for a
`bind(C)` procedure, where there is no bridge at all?** A direct entrypoint has
only the binding and the user's C ABI symbol, so whatever the direct route must
do is binding-owned by definition. The bridge then owns exactly the remainder:
the work that makes an ordinary non-`bind(C)` procedure reachable through that
same completed plan. Deriving the boundary this way keeps one shared entrypoint
contract for both routes instead of two parallel designs.

The question is still decisive when the form cannot be `bind(C)` at all. A
Fortran type that no interoperable interface can declare — a deferred-length
`character(len=:)` dummy, for example, which the standard rejects in a
`bind(C)` interface because character dummies there must have length 1 — proves
that a generated Fortran adapter is mandatory rather than optional, and names
what that adapter has to construct: the non-interoperable local the native
dummy requires. Record that reasoning with the completed policy so the bridge
implements a decided mechanism rather than rediscovering it.

After every implementation task, the final summary must include a breakdown of
the stages that actually changed. Relevant stages include parsing, semantic IR
construction, post-IR policy completion, wrapper planning/direct lowering, binding
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

Changes limited to wrapper planning, direct bridge/binding lowering, or native
compilation should use the focused owners under
`tests/fortran/infrastructure/codegen/`, feature-local
`tests/fortran/*/codegen/` directories, and
`tests/fortran/infrastructure/building/compiling/` as applicable. Include the
relevant end-to-end feature tests whenever a generated or compiled mechanism
changes; run a broader suite when behavior spans multiple stages.
Do not run LAPACK wrapper tests locally unless the user explicitly asks for them. Local verification may run everything else, including BLAS-only real-library tests; leave LAPACK coverage to GitHub Actions by default.
Do not run the full coverage workflow for routine changes. Run focused tests plus the required static-analysis suite. Reserve the complete CI-style coverage workflow for explicit pre-merge or pull-request verification, or when the user specifically requests it.
When investigating coverage failures, mirror the GitHub Actions workflow before deciding the fix: run coverage with `COVERAGE_PROCESS_START=pyproject.toml`, combine parallel data with `python3 -m coverage combine`, then run `python3 -m coverage report`. Do not assume a plain local coverage run matches CI, especially when subprocess tests are involved.
For documentation-only changes that do not modify executable Python code,
runtime behavior, build configuration, or test logic, do not run the complete
static-analysis suite by default. Run the focused documentation checks and
whitespace check instead:
- `python3 -m pytest -q tests/docs`
- `git diff --check`
Run the complete static-analysis suite when code, tests, build behavior, or
tooling configuration changes, or when explicitly requested for pre-merge or
pull-request verification:
- `python3 -m ruff check .`
- `python3 -m ruff format --check .`
- `python3 tools/check_static_analysis_versions.py`
- `python3 tools/check_codegen_complexity.py`
- `python3 -m bandit -c pyproject.toml -r prik --severity-level medium --confidence-level medium`
- `python3 -m vulture`
- `python3 tools/check_radon_policy.py --base-ref auto`
- `python3 -m radon cc prik -n C -s --total-average`
- `python3 -m radon mi prik -s`
Treat Ruff, Bandit, Vulture, and the Radon policy as blocking. The full Radon complexity and maintainability reports are advisory but must still be run. If a command cannot run because a dependency, network service, or CI-only environment value is unavailable, state that explicitly in the final response.

The codegen complexity checker is also advisory: review and report its findings,
but do not change correct behavior or fail the task solely to satisfy its
structural recommendations.
When you create a commit add this prefix to the message to know that you did push the commit "codex: ..."
