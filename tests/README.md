# Test Suite Map

Product-behavior tests are organized language first. Within a language,
documented language features use a feature-first, stage-second layout:

```text
tests/<language>/<language-feature>/<owning-stage>/
```

Parsing, preprocessing, command-line handling, semantic IR and `.pyi`
conversion, build orchestration, and other cross-feature mechanisms are
infrastructure. They live below `tests/<language>/infrastructure/`, even when
they also have user documentation. Maintainer tooling has the independent
`tests/tools/` owner, while exceptional automation-safety checks live under
`tests/workflows/`.
Generated C and CPython binding code used by a Fortran wrapper remains evidence
for the Fortran input contract; `tests/c/` means C is the user-owned input
language.

| Owner | Contract | Focused command |
| --- | --- | --- |
| [`tests/docs/`](docs/README.md) | Documentation publication, link integrity, executable examples, and public reference synchronization | `python3 -m pytest -q tests/docs` |
| [`tests/fortran/`](fortran/README.md) | Fortran input, semantic `.pyi` wrapper contracts, generated bridge/binding behavior, and Fortran runtime features | `python3 -m pytest -q tests/fortran` |
| [`tests/c/`](c/README.md) | C input-language inspection behavior | `python3 -m pytest -q tests/c` |
| [`tests/tools/`](tools/README.md) | Maintainer commands and CI support scripts | `python3 -m pytest -q tests/tools` |
| [`tests/workflows/`](workflows/README.md) | Exceptional safety properties for repository automation | `python3 -m pytest -q tests/workflows` |

The tracked pre-push hook runs the blocking static-analysis gate, the focused
publication and user-content documentation smoke tests, one compiled scalar
source-to-native-call wrapper test, `tests/tools/`, and `tests/workflows/`
locally; activate it once per clone with `git config core.hooksPath .githooks`.
GitHub Actions runs the checks again as the shared enforcement boundary.

The Fortran feature index maps each maintained User Guide and semantic `.pyi`
page to its final directory and focused command. The cleanup contract and
progress gates live in
[`../docs/developer/roadmap/fortran-test-suite-cleanup-checklist.md`](../docs/developer/roadmap/fortran-test-suite-cleanup-checklist.md).

## Ownership contract

Every pytest module and checked fixture has a behavioral owner below
`tests/{docs,tools,workflows,fortran,c}/`. Test organization is a maintainer convention,
not behavior frozen by recursive layout tests. No legacy stage-first root,
shared fixture corpus, forwarding fixture, collection shim, import alias, or
path fallback is part of the maintained suite.

Tests protect observable behavior or an explicit durable invariant. They do
not freeze documentation prose, heading order, private symbol names, complete
source inventories, or incidental implementation structure. A structural
check requires a concrete risk that cannot be protected more directly through
behavior.

## Final Fortran stage ownership

Within one Fortran feature, use only the stages that own real evidence:

| Stage | What it proves |
| --- | --- |
| `parsing/` | Source becomes the intended parser model or stops with its intended diagnostic |
| `probes/` | Compiler-derived target facts are correct |
| `preprocessing/` | Source processing, dependencies, and mappings are correct |
| `semantics/` | Parser or `.pyi` facts become the intended semantic IR |
| `policy/` | Ownership, lifetime, projection, mutation, nullability, storage, and accessor decisions are complete |
| `codegen/` | Completed policy selects a typed plan and named bridge/binding node mechanisms |
| `printers/` | C, Fortran, and semantic `.pyi` representations serialize to exact text |
| `compiling/` | Commands, objects, libraries, and link inputs are correct |
| `pipeline/` | Wrapper orchestration, build stages, and generated results transition correctly |
| `runtime/` | Runtime support mechanisms behave correctly without owning a complete feature journey |
| `end_to_end/` | Source or intentional `.pyi` input produces an imported extension whose public behavior is called and verified |

## Declaration-expression evidence

Array declaration expressions have deliberate vertical coverage. The arrays
semantic tests preserve names, imports, and native callable provenance; the
arrays policy tests classify dependency roles and unsupported native calls; and
the arrays end-to-end tests compile representative dimensions, inquiry forms,
reductions, conditionals, powers, and logical-kind arrays. Contract-batch
reconciliation belongs with `tests/fortran/infrastructure/semantic_pyi/`,
where editable `.pyi` imports and prototypes are exercised.

Cross-feature mechanisms have explicit infrastructure owners. `parsing/`,
`preprocessing/`, `cli/`, `semantic_ir/`, `semantic_pyi/`, and `building/` own
shared pipeline behavior; the remaining owners mirror their production package
(`policy/`, `codegen/`, `printers/`, `naming/`, `pipeline/`, `runtime/`,
`utilities/`). `tests/fortran/README.md` and `tests/c/README.md` carry the
complete per-language tables. A user-visible language behavior stays with its
feature even when its test crosses several pipeline stages. Minimized
real-world parser interactions belong under `infrastructure/parsing/`; full
third-party snapshots are temporary analysis inputs, not permanent fixtures.

## Independent suite gates

The final roots must collect and execute independently:

```bash
python3 -m pytest -q tests/fortran -m "not real_library"
python3 -m pytest -q tests/c
python3 -m pytest -q tests/docs
python3 -m pytest -q tests/tools
python3 -m pytest -q tests/workflows
```

The full-library BLAS/LAPACK integration nodes and the complete correctness
projects in `examples/blas/` and `examples/lapack/` remain in the dedicated
real-library job. The BLAS and LAPACK sources are owned by
`examples/blas/native/` and `examples/lapack/native/`; LAPACK is not part of
the default local verification command.

## Markers

Directory ownership is primary. Markers provide orthogonal or cross-feature
selection:

- `fortran_end_to_end` selects every compiled, imported, and called Fortran
  feature test, and nothing else;
- `real_library` selects only the dedicated BLAS correctness example and
  BLAS/LAPACK native-source end-to-end integration tests;
- `property`, `regression`, `benchmark`, and `slow` retain their ordinary
  meanings; and
- `toolchain_smoke` selects only the bounded portable compiler-profile subset
  declared by `tests/fortran/conftest.py`.

The smoke suite is eight exact nodes reused from ordinary Fortran end-to-end
tests. Strict mode requires a resolved compiler, rejects skips and xfails, and
prints the selected nodes with their mechanism and compilation fixture:

```bash
python3 -m pytest -q tests/fortran \
  -m toolchain_smoke \
  --require-toolchain-smoke \
  --prik-fortran-compiler=gfortran
```

The alternate-compiler GitHub Actions lanes are reproduced through one
repository-owned runner:

```bash
python3 tools/run_fortran_toolchain_lane.py --compiler=/path/to/compiler
```

It runs the maintained compiler-profile and focused preprocessing-CLI tests
before invoking the exact strict smoke selection above. `--plan` prints both
commands without running them.

`--prik-fortran-compiler` is authoritative for preprocessing, type probes,
native compilation, generated bridge compilation, and linking. It also selects
the matching vendor C compiler for generated binding compilation: GNU/GCC,
Intel/icx, LLVM/Clang, NVIDIA/nvc, or legacy PGI/pgcc. The test session resolves
the Fortran executable once and does not substitute another compiler family.

## Adding or moving a test

Give each test one primary invariant. Put exhaustive syntax and policy
combinations at the earliest stage that can prove them. Add end-to-end evidence
only when generation, compilation, import, or runtime behavior contributes a
distinct claim.

Unsupported behavior belongs at the first decisive stage. Preserve a later
CLI/API diagnostic test only when propagation is itself public behavior.
Feature-local fixtures live below their feature; cross-feature helpers require
an explicit infrastructure owner.

First decide whether the invariant is a language feature or a cross-feature
mechanism. For a cross-feature mechanism, place it under its infrastructure
owner when that makes the invariant easier to find:

```text
tests/fortran/infrastructure/<production-package>/test_<production-module>.py
```

For example, `prik/policy/ownership.py` uses
`infrastructure/policy/test_ownership.py`, while
`prik/planning/planner.py` uses `infrastructure/codegen/test_planner.py`;
language source printers use `infrastructure/printers/` and the wrapper
orchestrator uses `infrastructure/pipeline/test_wrapper_generator.py`.
This is navigation guidance, not a requirement to create one test file per
production module.
User-visible behavior does not move to infrastructure merely because it reaches
those modules. Production `if __name__ == "__main__"` demonstrations are
maintained examples rather than a fixed cross-stage inventory. Package-guide
command/result pairs are executed by `tests/docs/test_examples.py`, using the
documentation itself as the expected-output source. Feature-local tests prove
the underlying parser, policy, generation, or runtime behavior.

Shared support modules provide builders and assertions only. They do not
re-export `pytest`, standard-library modules, or production symbols.

After moving or splitting tests, run collection before execution and compare
node IDs, parametrized suffixes, markers, skips, and xfails. Then run every
destination touched by the move. Run complete CI-style coverage only for an
explicit pre-merge or coverage gate, not for feature inner loops.
