# Semantics Package

This package owns the language-neutral contract between native parser facts
and editable `.pyi` files. Post-IR decisions live in `../policy/`; typed wrapper
implementation plans live in `../planning/`.

The supported wrapper routes use Fortran parser facts, C parser facts, or an
authoritative semantic `.pyi` contract. `c2ir.py` supplies the semantic handoff
for the direct-C subset; parser and semantic acceptance remain broader than
runtime support. The exact public boundary lives in
`docs/user/language-support/c-support.md`.

## Entry Points

| File | Owns |
| --- | --- |
| `models.py` | Semantic IR dataclasses and core model metadata. |
| `scalar_types.py` | Stable primitive scalar names, families, and intrinsic storage facts without NumPy or backend spellings. |
| `metadata.py` | Cross-stage semantic metadata keys consumed after `.pyi`, C, or Fortran conversion. |
| `fortran2ir.py` | Fortran parser facts to semantic modules. |
| `c2ir.py` | C parser facts to semantic modules. |
| `pyi2ir.py` | User-editable semantic `.pyi` AST conversion and validation. |
| `../pipeline/pyi.py` | Combined `.pyi` text/file/path-set conversion and external-type reconciliation. |
| `pyi_metadata.py` | Semantic `.pyi` loader workflow metadata. |
| `native_contract.py` | Source-free native ABI and placement validation. |
| `native_array_handles.py` | Semantic descriptor marking, normalized data facets, and native-array facts. |
| `ownership_metadata.py` | Raw ownership and pointer-contract metadata keys and normalized semantic setters. |
| `../policy/completion.py` | Complete ownership, transfer, destruction, mutability/writeback, projection, nullability, release, storage, Python-barrier, native-barrier, and accessor decisions after full signatures are known. |
| `../planning/planner.py` | Converts completed semantic policy into the typed wrapper plan consumed by code generation. |

## Declaration Expressions

`../utilities/declaration_expressions.py` owns the shared declaration-expression
grammar, normalization, callable/reference discovery, native-style rendering,
and deterministic integer evaluation. Semantic conversion does not evaluate an
arbitrary native specification function. Instead, it records the function's
native name, known module origin when available, and any exact contract
declaration.

For an imported contract batch, `pyi2ir.py` reconciles those references with
the matching prototype or module function. Policy completion then classifies
whether the declaration has a usable boundary role or remains a named blocker.
Wrapper planning and code generation consume that completed decision; they do
not rediscover callable provenance or synthesize an interface.

Use a `@prototype` declaration when a standalone native procedure needs an
exact interface. Its argument transport and result contract supply the
information needed to emit the interface body. A module procedure already
visible through a native `use` association does not need a duplicate
interface declaration.

## Pipeline Position

```text
C parser facts, Fortran parser facts, or parsed .pyi AST
  -> semantic modules
  -> semantic policy completion
       -> complete storage, Python-barrier, and native-barrier policy
  -> typed wrapper planning
```

`../planning/planner.py` is the boundary where semantic contracts become typed
wrapper implementation plans. Object kind, ownership, transfer, destruction,
mutability/writeback, result projection, nullability, release responsibility,
contract/boundary storage modes, Python-barrier action, and native-barrier
action must be completed before this boundary by `../policy/completion.py`
using `prik/policy/ownership.py`. Getter result, native setter assignment, and Python
setter exposure policies are completed there as well.

The Python barrier and native barrier are separate policy decisions. The Python
barrier says how the generated CPython extension extracts or validates the
Python object: Python scalar value, rank-0 NumPy scalar storage, NumPy array
storage, Python string value, raw address value, or generated wrapper instance.
The native barrier says how the bridge presents the extracted value to native
code: direct value, call-local address, caller/Python-backed storage address,
raw address, packed array descriptor, or wrapper-owned native address.

Policy completion also validates the boundary spelling. Procedure `Addr(T)` is
an integer raw-address contract and is limited to primitive scalars,
fixed-length strings, and primitive arrays with fully resolved extents.
`Addr(Arg(i))` is limited to primitive scalar values that need call-local
addressing. Arrays, strings, rank-zero storage, wrapped objects, and raw-address
arguments use `Arg(i)` because their default native representation is already
address- or handle-based.

Public syntax uses the Python boundary shape directly, keeps `Final[T]` for
module constants, and requires hidden native literals inside `@native_call` to
be typed expressions such as `Int32(1)` or `String[1]("N")`.
Completed module-variable policy selects direct binding materialization for a
literal constant and a read-only native getter for a symbolic numeric source
parameter.

The planner, bridges, and bindings consume those decisions
instead of making local policy guesses. Bridge and binding dispatch is strict:
an unregistered barrier action or object-kind/action pair is an error rather
than a fallback. Model-node dispatch uses `prik.utilities.visitor.ClassVisitor` and the
`_visit_<ClassName>` protocol across parser-model conversion, `.pyi` AST
conversion, semantic lowering, bridges, bindings, and printers. Barrier/action
dispatch tables are separate and must not be used as model-node visitors.

The CLI source inspection path keeps parser and converter selection compact in
`prik/cli.py` through `_SOURCE_SEMANTIC_PIPELINES[language]`. Each table entry
selects the language parser and parser-to-IR converter; semantic policy
completion remains the next shared stage after those converters produce
`SemanticModule` objects.

## Tests And Docs

- Semantic reference: `docs/user/reference/semantic-ir.md`
- `.pyi` reference: `docs/user/reference/semantic-pyi-format.md`
- Source navigation: `docs/developer/codebase-map.md`, `docs/developer/feature-to-code-map.md`
- Architecture: `docs/developer/architecture.md`
- Semantics package guide: `docs/developer/packages/semantics.md`
- Semantic tests: `tests/fortran/infrastructure/semantic_ir/semantics/`
- C semantic tests: `tests/c/infrastructure/semantic_ir/semantics/`
- `.pyi` tests: `tests/fortran/infrastructure/semantic_pyi/`
- Wrapper behavior that reaches the typed plan: `tests/fortran/` and `tests/c/`
