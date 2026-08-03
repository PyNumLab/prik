# Fortran Test Index

`tests/fortran/` owns tests whose user-supplied native input contract is
Fortran, including semantic `.pyi` wrapper builds and the generated
Fortran/C/CPython implementation of that contract.

Meta-tests that inspect this directory's ownership, permanent evidence ledger,
or smoke selection live outside it under `tests/architecture/fortran/`.

The final organization is feature first and stage second:

```text
tests/fortran/<documented-feature>/<owning-stage>/
```

Documented features are direct children of `tests/fortran/`; the
`infrastructure/` directory remains the single container for internal
cross-feature frameworks. Only create a feature or stage directory when it
owns a real test or fixture.

## Documentation feature map

| Documentation | Final feature directory | Focused pytest command |
| --- | --- | --- |
| [Data Types](../../docs/user/guide/data-types.md) | `data_types/` | `python3 -m pytest -q tests/fortran/data_types` |
| [Arrays](../../docs/user/guide/arrays.md) | `arrays/` | `python3 -m pytest -q tests/fortran/arrays` |
| [Strings](../../docs/user/guide/strings.md) | `strings/` | `python3 -m pytest -q tests/fortran/strings` |
| [Wrapping Functions](../../docs/user/guide/wrapping-functions.md) | `functions/` | `python3 -m pytest -q tests/fortran/functions` |
| [Wrapping Subroutines](../../docs/user/guide/wrapping-subroutines.md) | `subroutines/` | `python3 -m pytest -q tests/fortran/subroutines` |
| [Wrapping Modules](../../docs/user/guide/wrapping-modules.md) | `modules/` | `python3 -m pytest -q tests/fortran/modules` |
| [Optional Arguments](../../docs/user/guide/optional-arguments.md) | `optional_arguments/` | `python3 -m pytest -q tests/fortran/optional_arguments` |
| [Generic Interfaces](../../docs/user/guide/generic-interfaces.md) | `generic_interfaces/` | `python3 -m pytest -q tests/fortran/generic_interfaces` |
| [Wrapping Derived Types](../../docs/user/guide/wrapping-derived-types.md) | `derived_types/` | `python3 -m pytest -q tests/fortran/derived_types` |
| [Allocatables](../../docs/user/guide/allocatables.md) | `allocatables/` | `python3 -m pytest -q tests/fortran/allocatables` |
| [Pointers](../../docs/user/guide/pointers.md) | `pointers/` | `python3 -m pytest -q tests/fortran/pointers` |
| [Memory Management](../../docs/user/guide/memory-management.md) | `memory_management/` | `python3 -m pytest -q tests/fortran/memory_management` |
| [Callbacks](../../docs/user/guide/callbacks.md) | `callbacks/` | `python3 -m pytest -q tests/fortran/callbacks` |
| [Enumerations](../../docs/user/guide/enumerations.md) | `enumerations/` | `python3 -m pytest -q tests/fortran/enumerations` |
| [Raw Addresses](../../docs/user/guide/raw-addresses.md) | `raw_addresses/` | `python3 -m pytest -q tests/fortran/raw_addresses` |
| [Error Handling](../../docs/user/guide/error-handling.md) | `error_handling/` | `python3 -m pytest -q tests/fortran/error_handling` |
| [Building the Shared Library](../../docs/user/guide/building-shared-library.md) | `building_shared_library/` | `python3 -m pytest -q tests/fortran/building_shared_library` |
| [Inspect a Fortran API](../../docs/user/examples/recipes/inspect-fortran-api.md) | `source_parsing/` | `python3 -m pytest -q tests/fortran/source_parsing` |
| [Compiler Preprocessing](../../docs/user/examples/recipes/compiler-preprocessing.md) | `source_preprocessing/` | `python3 -m pytest -q tests/fortran/source_preprocessing` |
| [CLI Commands](../../docs/user/reference/cli-commands.md) | `command_line_interface/` | `python3 -m pytest -q tests/fortran/command_line_interface` |
| [Semantic IR](../../docs/user/reference/semantic-ir.md) | `semantic_ir/` | `python3 -m pytest -q tests/fortran/semantic_ir` |
| [Semantic `.pyi` Format](../../docs/user/reference/semantic-pyi-format.md) | `semantic_pyi_format/` | `python3 -m pytest -q tests/fortran/semantic_pyi_format` |
| [Exports and Modules](../../docs/user/reference/pyi-contracts/exports-and-modules.md) | `pyi_contracts/exports_and_modules/` | `python3 -m pytest -q tests/fortran/pyi_contracts/exports_and_modules` |
| [Functions and Classes](../../docs/user/reference/pyi-contracts/functions-and-classes.md) | `pyi_contracts/functions_and_classes/` | `python3 -m pytest -q tests/fortran/pyi_contracts/functions_and_classes` |
| [Calls and Results](../../docs/user/reference/pyi-contracts/calls-and-results.md) | `pyi_contracts/calls_and_results/` | `python3 -m pytest -q tests/fortran/pyi_contracts/calls_and_results` |

Each feature uses only the stages it needs: `parsing`, `probes`,
`preprocessing`, `semantics`, `policy`, `wrapper_codegen`, `compiling`,
`pipeline`, `runtime`, and `end_to_end`.

## Infrastructure owners

Infrastructure contains only internal cross-feature frameworks with no honest
public-capability or documentation-feature owner. Tests of public parsing,
preprocessing, command-line, semantic-IR, contract-printing, and build behavior
belong to their named feature even when they span several lower-level
mechanisms. Infrastructure tests normally start from completed internal models
or synthetic implementation nodes; the starting representation is supporting
evidence, not the ownership rule.

| Final directory | Owner |
| --- | --- |
| `infrastructure/policy/` | Internal completed-policy dispatch and validation framework |
| `infrastructure/wrapper_codegen/` | Shared typed-plan and generator mechanics |

Minimized real-source parser regressions live in
`source_parsing/parsing/test_real_world_interaction_regressions.py`. A
third-party project is a temporary discovery input, not a permanent fixture:
extract its named parser facts, prove that the focused suite covers its unique
lines and branches, then remove the snapshot. Parser regressions are never
end-to-end or smoke evidence.

## Fixtures and helpers

Feature-specific fixtures stay beneath their feature. End-to-end projects use:

```text
<feature>/end_to_end/fixtures/<case>/native/
```

Generated build products always use pytest temporary directories. `_support/`
contains only helpers used by several Fortran features; it contains no pytest
modules, feature sources, or checked contracts.

The permanent evidence index is
[`CONTRACT_COVERAGE.md`](CONTRACT_COVERAGE.md). Temporary legacy-node,
artifact-consumer, and support-consumer inventories live under
[`../_migration/`](../_migration/) until the final migration gate.

## Markers

- Every pytest node below a feature `end_to_end/` carries
  `fortran_end_to_end`, and no other node does.
- Only the complete `examples/blas/` and `examples/lapack/` correctness
  projects and BLAS/LAPACK native-source integration nodes additionally carry
  `real_library`.
- `toolchain_smoke` will select exact portable rows from the completed ordinary
  end-to-end suite; it is not a separate directory.

Run all migrated Fortran evidence with:

```bash
python3 -m pytest -q tests/fortran
```

Run the BLAS project by sourcing `examples/blas/build_all.sh`, then running
`python3 -m pytest -q examples/blas/tests`. Never run LAPACK locally without an
explicit request.
