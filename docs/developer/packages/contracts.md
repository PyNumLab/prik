---
title: Contracts Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, semantic .pyi format
related: index.md, parsers.md, semantics.md, ../architecture.md
status: maintained
publication: draft
---

# Contracts Package

## Purpose And Boundaries

`prik/contracts/` owns the public names written in semantic `.pyi` contracts.
Those names describe scalar types, arrays, storage, ownership requests,
projections, native calls, callbacks, and descriptor handles. The package is a
public syntax vocabulary; it does not define semantic IR, complete policy, or
generate wrappers.

## Local Structure

```text
prik/contracts/
└── __init__.py
```

The single module is intentional. A semantic contract imports one stable
public namespace instead of depending on internal stage packages.

## What This Stage Receives And Produces

```text
semantic .pyi text
  -> names imported from prik.contracts
  -> Python AST in prik.parsers.pyi
  -> contract interpretation in prik.semantics.pyi2ir
  -> completed policy in prik.policy
```

Some primitive symbols also construct exact NumPy scalar values at runtime.
Subscriptions such as `Float64[:, :]` construct declarative contract objects;
they do not create semantic IR objects.

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/contracts/__init__.py`](../../../prik/contracts/__init__.py) | The complete public vocabulary: scalar and array markers, descriptor markers (`Allocatable`, `Pointer`), metadata expressions, decorators, and the small runtime constructors behind concrete scalar and descriptor contracts. | Adding, removing, or documenting public `.pyi` syntax. This one file is intentionally the stable import namespace; private `_Contract*` classes preserve annotation syntax at runtime. |

The canonical public import path is part of the file format. Internal code may
interpret these names, but must not replace them with imports from semantics,
policy, or codegen.

## Execution Example

Run the real package entry file:

```bash
python3 prik/contracts/__init__.py
```

```text
Float64() -> np.float64(0.0) (float64)
Float64[:, :] -> element=Float64, rank=2, shape=(slice(None, None, None), slice(None, None, None))
```

The first line proves that a primitive contract scalar has exact NumPy runtime
behavior. The second proves that array subscription produces declarative rank
and shape syntax for later semantic interpretation.

## Tests And What They Prove

- [Contract runtime tests](../../../tests/fortran/data_types/runtime/) protect scalar and descriptor-constructor behavior.
- [Semantic `.pyi` parser tests](../../../tests/fortran/semantic_pyi_format/parsing/) protect recognition of the public vocabulary.
- [Semantic `.pyi` round-trip tests](../../../tests/fortran/semantic_pyi_format/pipeline/) protect loading and re-emission through the shared contract path.
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py) fixes the example output above.

## Change Routes

- Add or rename public syntax here first, then update `.pyi` parsing,
  conversion, printing, user reference documentation, and focused round-trip
  tests.
- Change semantic meaning in `prik/semantics/pyi2ir.py`, not in a runtime
  constructor.
- Change ownership or lowering selection in policy after semantic conversion.

## Invariants And Common Mistakes

- Keep `prik.contracts` stable and public; do not expose internal policy models
  through this namespace.
- A valid Python annotation is not automatically a supported wrapper contract.
- NumPy construction behavior must not become the semantic datatype authority.

See the [semantic `.pyi` user reference](../../user/reference/semantic-pyi-format.md)
for the public language and the [semantics package](semantics.md) for its IR
interpretation.
