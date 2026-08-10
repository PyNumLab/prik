# Semantics Package

This package owns the language-neutral contract between native parser facts,
editable `.pyi` files, policy completion, and wrapper code generation.

## Entry Points

| File | Owns |
| --- | --- |
| `models.py` | Semantic IR dataclasses and core model metadata. |
| `../semantic_metadata.py` | Cross-stage semantic metadata keys consumed after `.pyi`, C, or Fortran conversion. |
| `fortran2ir.py` | Fortran parser facts to semantic modules. |
| `c2ir.py` | C parser facts to semantic modules. |
| `pyi2ir.py` | User-editable semantic `.pyi` AST conversion and validation. |
| `../pyi_pipeline.py` | Combined `.pyi` text/file/path-set conversion and external-type reconciliation. |
| `pyi_metadata.py` | Semantic `.pyi` loader workflow metadata. |
| `native_contract.py` | Source-free native ABI and placement validation. |
| `policy_completion.py` | Complete ownership, transfer, destruction, mutability/writeback, projection, nullability, release, storage, Python-barrier, native-barrier, and accessor decisions after full signatures are known. |
| `ir2ast.py` | Semantic IR to codegen AST lowering for wrapper generation; consumes completed policies. |

## Declaration Expressions

`utilities/declaration_expressions.py` owns the shared declaration-expression
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
  -> wrapper planning or codegen AST
```

`ir2ast.py` is the boundary where semantic contracts become generated-wrapper
implementation details. Object kind, ownership, transfer, destruction,
mutability/writeback, result projection, nullability, release responsibility,
contract/boundary storage modes, Python-barrier action, and native-barrier
action must be completed before this boundary by `policy_completion.py` using
`prik/semantics/ownership.py`. Getter result, native setter assignment, and Python
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

`ir2ast.py`, bridges, and bindings consume those decisions
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
- `.pyi` wrapper checklist: `docs/maintainer/roadmap/semantic-pyi-wrapper-checklist.md`
- Source navigation: `docs/developer/source-map.md`, `docs/developer/feature-to-code-map.md`
- Pipeline map: `docs/maintainer/internal-architecture/pipeline-map.md`
- Semantic tests: `tests/fortran/semantic_ir/semantics/`
- `.pyi` tests: `tests/fortran/semantic_pyi_format/`
- Wrapper behavior that reaches `ir2ast.py`: `tests/fortran/`
