---
title: Naming Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, index.md, planning.md, codegen.md, ../codebase-map.md
status: maintained
publication: draft
---

# Naming Package

## Purpose And Boundaries

`prik/naming/` owns public and generated names whose stability and collision
rules are shared across planning and generation. It does not own semantic
policy or emitted source syntax.

## Local Structure

```text
prik/naming/
├── __init__.py
├── policy.py
└── native_symbols.py
```

## What This Stage Receives And Produces

```text
raw public or generated identity + occupied namespace
  -> normalized public name or bounded native symbol
  -> planning and code generation
```

## Directory Tour

| Module | Main entrypoints and contents | Change it when |
| --- | --- | --- |
| [`prik/naming/__init__.py`](../../../prik/naming/__init__.py) | Re-exports the supported normalization and generated-symbol policy objects. | Changing the package-level naming API. |
| [`prik/naming/policy.py`](../../../prik/naming/policy.py) | `NamingPolicy`, `NormalizedPublicName`, `PublicNameRecord`, and `GeneratedSymbolRules` normalize Python names, reserve namespaces, and apply language rules. | Public-name normalization, collision handling, keyword escaping, or target language symbol rules. |
| [`prik/naming/native_symbols.py`](../../../prik/naming/native_symbols.py) | `NativeSymbolNames` retains owner identity and creates compact, deterministic compiler-safe fragments. | Bounded native-symbol spelling or hash/prefix rules. |

## Execution Examples

```bash
python3 prik/naming/policy.py
```

```text
Normalized public name: render_value
Collision-safe public name: render_value_2
C destructor symbol: state_drop
```

```bash
python3 prik/naming/native_symbols.py
```

```text
Owner identity: geometry.point.coordinates
Stable native symbol: point_coordinate_d_c2fc5940
Within 27-character limit: True
```

The first example distinguishes public namespace allocation from generated
target naming. The second preserves a readable prefix while hashing the full
owner identity under a compiler symbol limit.

## Tests And What They Prove

- [Naming infrastructure](../../../tests/fortran/infrastructure/naming/) covers normalization, collisions, and stable generated names.

## Change Routes

- Change public normalization and collision policy in `policy.py`.
- Change stable ABI fragments in `native_symbols.py` with exact-name tests.

## Invariants And Common Mistakes

- Never consult completed ownership or emit language syntax here.
- The same inputs must always produce the same generated symbol.
