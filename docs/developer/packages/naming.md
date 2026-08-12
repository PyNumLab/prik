---
title: Naming Package
audience: developers, maintainers, contributors
prerequisites: contributor architecture guide
related: ../architecture.md, index.md, planning.md, codegen.md, ../source-map.md
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
├── policy.py
└── native_symbols.py
```

## Important Files And Essential Objects

| File | Important objects | Responsibility |
| --- | --- | --- |
| `policy.py` | `NamingPolicy`, `NormalizedPublicName`, `PublicNameRecord`, `GeneratedSymbolRules` | Normalizes Python names, reserves namespaces, and applies target-language symbol rules. |
| `native_symbols.py` | `NativeSymbolNames` | Compacts long owner identities into deterministic compiler-safe fragments. |

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

## Tests

- [Naming infrastructure](../../../tests/fortran/infrastructure/naming/)
- [Direct execution inventory](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py)

## Change Routes

- Change public normalization and collision policy in `policy.py`.
- Change stable ABI fragments in `native_symbols.py` with exact-name tests.

## Invariants And Common Mistakes

- Never consult completed ownership or emit language syntax here.
- The same inputs must always produce the same generated symbol.
