---
title: Naming Component
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, index.md, policy.md, planning.md, codegen.md
status: maintained
publication: reviewed
---

# Naming Component

## Purpose And Boundaries

`prik/naming/` owns naming rules shared by policy, planning, printers, and code
generation. It keeps Python-visible names valid and collision-free and creates
deterministic native symbols within target-language constraints. It does not
choose exports, ownership, wrapper support, or emitted syntax.

## The Two Naming Routes

```text
source spelling + public namespace
  -> normalize Python identifier
  -> reserve it or add a collision suffix
  -> public export name

owner identity + preferred generated name + target rules
  -> escape reserved or special names
  -> avoid occupied symbols
  -> deterministic native symbol
```

Public names and generated symbols are deliberately separate. Escaping a
Python keyword must not rename the underlying Fortran symbol, and a C or
Fortran restriction must not change the public Python API.

## Local Structure

```text
prik/naming/
├── __init__.py
├── policy.py
└── native_symbols.py
```

- [`prik.naming`](../../../prik/naming/__init__.py) re-exports the supported
  public-name and generated-symbol policy API. Change it only when that
  package-level API changes.
- [`policy.py`](../../../prik/naming/policy.py) contains
  `normalize_public_name()`, `NamingPolicy.reserve_public_name()`, and
  `generated_symbol()`. Change it for normalization, strict-name behavior,
  namespace collisions, keywords, or target-language rules.
- [`native_symbols.py`](../../../prik/naming/native_symbols.py) contains
  `NativeSymbolNames.compact()`. It combines a readable prefix with a hash of
  the full owner identity under a requested length limit.

`NamingPolicy` retains public reservations for one construction operation.
`NativeSymbolNames` is stateless: the same owner, preferred spelling, and
limit always produce the same result.

## Run The Naming Demonstrations

The policy example shows normalization, a public collision, and one C special
method rewrite:

```bash
python3 prik/naming/policy.py
```

```text
Normalized public name: render_value
Collision-safe public name: render_value_2
C destructor symbol: state_drop
```

The compact-symbol example preserves a readable prefix while using the full
owner path for collision resistance:

```bash
python3 prik/naming/native_symbols.py
```

```text
Owner identity: geometry.point.coordinates
Stable native symbol: point_coordinate_d_c2fc5940
Within 27-character limit: True
```

## Change Routes And Evidence

- Change Python normalization, namespace reservation, or target-language rules
  in `policy.py`.
- Change bounded native helper symbols in `native_symbols.py`; treat their
  spelling as generated ABI when compiled artifacts refer to it.

| Evidence | What it establishes |
| --- | --- |
| [Naming tests](../../../tests/fortran/infrastructure/naming/) | Python keyword handling, strict mode, namespace collisions, language keywords, and special-method rewriting. |

Naming must be deterministic for identical inputs. This component may apply a
rule supplied by a target language, but it must never infer semantic policy or
emit source text.
