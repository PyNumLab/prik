---
title: Contracts Component
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide, semantic .pyi format
related: index.md, parsers.md, semantics.md, ../architecture.md
status: maintained
publication: reviewed
---

# Contracts Component

## Purpose And Boundaries

`prik/contracts/` is the public vocabulary used in semantic `.pyi` files. It
defines the importable names for scalar and array types, descriptor handles,
metadata expressions, native-call descriptions, callbacks, and decorators.

The package preserves valid Python annotation syntax at runtime. It does not
parse that syntax, assign semantic meaning, complete interoperability policy,
or generate a wrapper. Those responsibilities belong to `parsers/`,
`semantics/`, `policy/`, and `codegen/` respectively.

## How A Contract Name Is Used

```text
name imported from prik.contracts
  -> Python AST produced by the .pyi parser
  -> semantic interpretation in pyi2ir.py
  -> policy completion, planning, and generation
```

For example, `Float64[:, :]` creates a declarative array-contract object whose
element type, rank, and shape can be inspected. It does not create semantic IR
or a NumPy array. A concrete scalar name such as `Float64` additionally has a
zero-valued NumPy constructor so generated contracts can be imported and used
as Python modules.

## Local Structure

```text
prik/contracts/
└── __init__.py
```

[`prik/contracts/__init__.py`](../../../prik/contracts/__init__.py) contains
the complete public namespace. Its contents have four roles:

- scalar, array, descriptor, and wrapped-type markers describe values;
- expression helpers such as `Arg`, `Len`, and `Ownership` describe metadata;
- decorators such as `native_abi`, `native_call`, `prototype`, and `standalone`
  describe callable ABI or structure; and
- `CONTRACT_SYMBOLS` and `CONTRACT_TYPE_NAMES` give parsers and printers the
  canonical public vocabulary.

Private `_Contract*` classes implement import-time annotation behavior. They
are mechanisms behind the public names, not part of the contract language.

## Run The Contract Demonstration

```bash
python3 prik/contracts/__init__.py
```

```text
Float64() -> np.float64(0.0) (float64)
Float64[:, :] -> element=Float64, rank=2, shape=(slice(None, None, None), slice(None, None, None))
```

The first line demonstrates the concrete NumPy scalar constructor. The second
shows the declarative type, rank, and shape retained by an array annotation;
later stages interpret those facts.

## Change Routes And Evidence

- Change public `.pyi` names in `prik/contracts/__init__.py`, then update the
  parser, semantic conversion, printer, and
  [semantic `.pyi` reference](../../user/reference/pyi-contracts/index.md).
- Change the meaning of a contract in `prik/semantics/pyi2ir.py`.
- Change ownership, projection, or support decisions in `prik/policy/`.

| Evidence | What it establishes |
| --- | --- |
| [Contract runtime tests](../../../tests/fortran/data_types/runtime/) | Concrete scalar constructors and invalid constructor use. |
| [Semantic `.pyi` parser tests](../../../tests/fortran/infrastructure/semantic_pyi/parsing/) | Recognition of the public vocabulary and annotation syntax. |
| [Semantic `.pyi` pipeline tests](../../../tests/fortran/infrastructure/semantic_pyi/pipeline/) | Contract loading, semantic conversion, and re-emission. |

The import path and public names are part of the file format. A name being
valid Python syntax does not by itself make the corresponding wrapper behavior
supported, and runtime constructors must not become the authority for semantic
datatype decisions.
