---
title: .pyi Exports and Modules
audience: users, advanced users
prerequisites: editing .pyi contracts overview
related: index.md, functions-and-classes.md, ../semantic-pyi-format.md, ../../guide/wrapping-modules.md
status: maintained
publication: reviewed
---

# Exports and Modules

The entry `__init__.pyi` controls the extension's Python namespace. Leaf
`.pyi` files describe native modules and their declarations.

## Choose the Package Shape

Generated entry contract:

```python
from . import module1
from . import module2
```

Python then uses `package.module1` and `package.module2`. To place both
modules' public names directly in `package`, edit the entry contract:

```python
from .module1 import *
from .module2 import *
```

Selective imports and aliases also work:

```python
from .module1 import solve
from .module2 import reset as clear
```

Changing entry imports changes only the Python namespace. It does not rename a
native module or select a native object file.

Only declarations reachable from `__init__.pyi` are public. Missing files,
import cycles, and two different exports using the same Python name are
errors. Explicit aliases share the same native target, but Python object
identity is not guaranteed for every read.

## Remove or Hide a Declaration

Delete a declaration to remove it from the Python API:

```python
from prik.contracts import Int32

counter: Int32

def summarize() -> Int32: ...
```

The removed declaration is not regenerated during this build. This works for
functions, variables, classes, methods, fields, constructors, and individual
overload candidates.

Use `@private` for a function or class that another contract declaration still
needs:

```python
from prik.contracts import Float64, private

@private
def scaled_counter() -> Float64: ...
```

Use `private[...]` for a variable or argument:

```python
from prik.contracts import Float64, private

scale: private[Float64]
```

Both forms keep the declaration in the contract while hiding it from Python.

## Add or Rename a Native Procedure

You may add a declaration when the procedure already exists in the supplied
native implementation:

```python
from prik.contracts import Float64

def norm2(values: Float64[:]) -> Float64: ...
```

In a module leaf, the filename identifies the native module and the function
name selects the native procedure. Use `@bind(...)` when the Python name
differs:

```python
from prik.contracts import Float64, Int32, bind

@bind("solver_step")
def step(values: Float64[:]) -> Int32: ...
```

For a standalone native symbol, also use `@standalone`:

```python
from prik.contracts import Float64, bind, standalone

@standalone
@bind("vendor_norm2")
def norm2(values: Float64[:]) -> Float64: ...
```

The declaration must include the correct native arguments, types, ranks, and
call shape. Adding Python syntax cannot create a native procedure that is not
present in the linked implementation.

## Set Module Values at Import

A writable scalar module variable may have a literal initial value:

```python
from prik.contracts import Int32

counter: Int32 = 41
```

prik sets the module variable when the extension is imported. It remains
writable. This works only when prik can write that native variable, and the
initializer must be a literal rather than a call, name, or expression.

Use `Final[...]` only for a true read-only constant:

```python
from prik.contracts import Final, Int32

nmax: Final[Int32] = 12
```

See [Wrapping Modules](../../guide/wrapping-modules.md#shape-the-module-api-with-the-contract)
for the resulting Python usage.

## Next

Use [Functions and Classes](functions-and-classes.md) to add methods,
overloads, or a custom constructor.
