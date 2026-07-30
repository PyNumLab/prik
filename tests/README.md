# Test Suite Map

Product-behavior tests are organized language first. Fortran tests are then
organized by documented feature and pipeline stage:

```text
tests/fortran/<documented-feature>/<owning-stage>/
```

Meta-tests that validate the test suite itself live under
`tests/architecture/`; they are outside the tree whose structure they enforce.
Only genuinely language-neutral product behavior belongs under `tests/shared/`.
Generated C and CPython binding code used by a Fortran wrapper remains evidence
for the Fortran input contract; `tests/c/` means C is the user-owned input
language.

| Owner | Contract | Focused command |
| --- | --- | --- |
| [`tests/architecture/`](architecture/README.md) | Test-suite ownership, evidence-ledger, selection, and collection invariants | `python3 -m pytest -q tests/architecture` |
| [`tests/fortran/`](fortran/README.md) | Fortran input, semantic `.pyi` wrapper contracts, generated bridge/binding behavior, and Fortran runtime features | `python3 -m pytest -q tests/fortran` |
| [`tests/c/`](c/README.md) | C input-language inspection behavior | `python3 -m pytest -q tests/c` |
| [`tests/shared/`](shared/README.md) | Behavior that neither imports nor selects a native input language | `python3 -m pytest -q tests/shared` |

The Fortran feature index maps each maintained User Guide and semantic `.pyi`
page to its final directory and focused command. The cleanup contract and
progress gates live in
[`../docs/maintainer/roadmap/fortran-test-suite-cleanup-checklist.md`](../docs/maintainer/roadmap/fortran-test-suite-cleanup-checklist.md).

## Ownership contract

Every pytest module and checked fixture has one owner below
`tests/{architecture,fortran,c,shared}/`. `tests/architecture/` contains only
meta-tests of this ownership and evidence system; it is not a compatibility
root for old stage-first tests. No legacy stage-first root, shared fixture
corpus, forwarding fixture, collection shim, import alias, or path fallback is
part of the maintained suite.

## Final Fortran stage ownership

Within one Fortran feature, use only the stages that own real evidence:

| Stage | What it proves |
| --- | --- |
| `parsing/` | Source becomes the intended parser model or stops with its intended diagnostic |
| `probes/` | Compiler-derived target facts are correct |
| `preprocessing/` | Source processing, dependencies, and mappings are correct |
| `semantics/` | Parser or `.pyi` facts become the intended semantic IR |
| `policy/` | Ownership, lifetime, projection, mutation, nullability, storage, and accessor decisions are complete |
| `wrapper_codegen/` | Completed policy selects a typed plan and named bridge/binding mechanisms |
| `compiling/` | Commands, objects, libraries, and link inputs are correct |
| `pipeline/` | Build stages and generated artifacts transition correctly |
| `runtime/` | Runtime support mechanisms behave correctly without owning a complete feature journey |
| `end_to_end/` | Source or intentional `.pyi` input produces an imported extension whose public behavior is called and verified |

Public cross-feature capabilities have explicit owners:
`source_parsing/`, `source_preprocessing/`, `command_line_interface/`, and
`semantic_ir/`. Only internal frameworks with no honest public-capability owner
belong under `tests/fortran/infrastructure/`. A user-visible behavior stays
with its feature even when its test crosses several pipeline stages. Minimized
real-world parser interactions belong under `source_parsing/parsing/`; full
third-party snapshots are temporary analysis inputs, not permanent fixtures.

## Independent suite gates

The final roots must collect and execute independently:

```bash
python3 -m pytest -q tests/fortran -m "not real_library"
python3 -m pytest -q tests/c
python3 -m pytest -q tests/shared
python3 -m pytest -q tests/architecture
```

BLAS and LAPACK remain in the dedicated real-library job. LAPACK is not part
of the default local verification command.

## Markers

Directory ownership is primary. Markers provide orthogonal or cross-feature
selection:

- `fortran_end_to_end` selects every compiled, imported, and called Fortran
  feature test, and nothing else;
- `real_library` selects only the dedicated BLAS/LAPACK native-source
  end-to-end tests;
- `property`, `regression`, `benchmark`, and `slow` retain their ordinary
  meanings; and
- `toolchain_smoke` selects only the bounded portable compiler-profile subset
  documented in `tests/architecture/fortran/`.

The smoke suite is eight exact nodes reused from ordinary feature end-to-end
tests. Strict mode requires a resolved compiler, rejects skips and xfails, and
prints the selected nodes with their mechanism and compilation fixture:

```bash
python3 -m pytest -q tests/fortran \
  -m toolchain_smoke \
  --require-toolchain-smoke \
  --x2py-fortran-compiler=gfortran
```

`--x2py-fortran-compiler` is authoritative for preprocessing, type probes,
native compilation, generated bridge and binding compilation, and linking.
The test session resolves it once and does not substitute another executable.

## Adding or moving a test

Give each test one primary invariant. Put exhaustive syntax and policy
combinations at the earliest stage that can prove them. Add end-to-end evidence
only when generation, compilation, import, or runtime behavior contributes a
distinct claim.

Unsupported behavior belongs at the first decisive stage. Preserve a later
CLI/API diagnostic test only when propagation is itself public behavior.
Feature-local fixtures live below their feature; cross-feature helpers require
an explicit infrastructure or shared owner.

After moving or splitting tests, run collection before execution and compare
node IDs, parametrized suffixes, markers, skips, and xfails. Then run every
destination touched by the move. Run complete CI-style coverage only for an
explicit pre-merge or coverage gate, not for feature inner loops.
