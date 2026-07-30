---
title: Generated Modules Reference
audience: users
prerequisites: wrapping modules
related: generated-functions.md, generated-classes.md, semantic-pyi-format.md, ../guide/wrapping-modules.md
status: maintained
publication: draft
---

# Generated Modules Reference

x2py preserves the native module namespace in the generated Python extension.
Standalone procedures are exported from the extension root. Procedures,
variables, constants, and classes declared inside a Fortran module are exported
from that generated child module.

Use [Wrapping Modules](../guide/wrapping-modules.md) for a source-first
walkthrough. This page documents the package shape, import rules, and module
member surface.

## Extension Identity

The default extension name comes from the source input or the semantic `.pyi`
entry contract. `--out NAME` overrides the extension module name for compiled
wrapper builds. For a package entry named `__init__.pyi`, the containing
directory name becomes the default extension identity.

Contained Fortran modules become child Python modules:

```python
from module_state.module_state import summarize

assert summarize() == np.int32(15)
```

Module members are importable through their child module; they are not
automatically flattened onto the extension root. A
root-level semantic `.pyi` entry may explicitly reshape the Python export tree
with imports, aliases, or star imports. Duplicate root exports fail before
code generation.

## Contract Package Shape

Generated `.pyi` packages use one entry contract plus one leaf per native
module:

```python
# __init__.pyi
from . import first_mod
from . import second_mod

# first_mod.pyi
def shared_call() -> None: ...
```

A module leaf is named `<native-module>.pyi`; that filename is a native module
fact. Renaming the leaf changes the module selected by wrapper generation.
Wrapper commands accept exactly one entry `.pyi` and recursively discover
relative imports from that entry.

## Functions, Variables, And Constants

Module procedures are attributes of the child module and follow
[Generated Functions Reference](generated-functions.md). Public module
variables are direct module attributes:

```python
from x2py.contracts import Final, Int32

nmax: Final[Int32] = 12

counter: Int32

def summarize() -> Int32: ...
```

Reading a supported variable fetches current native module state. Assigning an
exact matching scalar value writes through when Python setter exposure is part
of the completed wrapper policy. Native getter and setter helpers are internal
implementation details and are not exported as Python callables.

Representable native parameters are `Final[...]` constants in the generated
contract. Assigning to the Python module attribute may shadow the object in
Python, but it does not mutate the native parameter.

Supported module arrays, allocatables, pointers, and derived objects follow the
ownership rules in [Memory Management](../guide/memory-management.md) and
the topic-specific user-guide pages. Plain and `Aliased` derived module
variables return live native-owned objects. `Aliased` permits an address-backed
borrow; a plain declaration uses typed module-specific access. Missing
ownership, release, mutability, or a supported module-object mechanism blocks
generation.

Rank-zero `Allocatable[Derived]` and `Pointer[Derived]` module variables are
nullable live proxies: the module attribute is `None` while native state is
absent and otherwise exposes the generated fields. Compatible allocatable
dummies use a reversible typed `move_alloc` transaction; reassociable pointer
dummies use a typed pointer transaction and restore the final association.
Payload-only calls use direct or synchronous scoped addresses. See the
[derived-object lifetime rules](../guide/memory-management.md#derived-objects-and-fields).

## Visibility, Binding Names, And Imports

Private source declarations are omitted from generated contracts. Edited
contracts can also remove declarations or mark them with `@private` or
`private[...]`.

`@bind("native_name")` records a native symbol name that differs from the
Python declaration name. It does not move a declaration between modules and it
does not change Python import policy.

Supported import policy belongs in the entry contract:

```python
from . import box_ops
from .second_math import double_after_add as fused_value
```

This keeps `extension.second_math.double_after_add(...)` available while also
exporting `extension.fused_value(...)`. Star imports are explicit flattening
requests; colliding names fail.

## Evidence And Maintenance

Module package shape, child namespaces, variable access, and import policy are
covered by
[`test_module_variables_and_state.py`](../../../tests/fortran/modules/end_to_end/test_module_variables_and_state.py),
[`test_contract_package_runtime.py`](../../../tests/fortran/semantic_pyi_format/end_to_end/test_contract_package_runtime.py),
[`test_multi_source_builds.py`](../../../tests/fortran/building_shared_library/end_to_end/test_multi_source_builds.py), and
[`test_source_generated_pyi_contracts.py`](../../../tests/fortran/building_shared_library/pipeline/test_source_generated_contracts.py).

When module namespace behavior changes, update this page, generated package
fixtures, [Semantic `.pyi` Format](semantic-pyi-format.md), and the module
workflow page in the same change.
