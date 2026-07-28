---
title: .pyi Calls and Results
audience: users, advanced users
prerequisites: editing .pyi contracts overview
related: index.md, functions-and-classes.md, ../semantic-pyi-format.md, ../../guide/arrays.md, ../../guide/error-handling.md
status: maintained
publication: reviewed
---

# Calls and Results

The function signature describes the Python call. `@native_call(...)`
describes how that call supplies the native arguments.

## Expose Native Arguments Directly

When every native argument is visible in native order, `@native_call(...)` is
not needed:

```python
from x2py.contracts import Int32

def scalar_status(
    base: Int32[()],
    status: Int32[()],
) -> None: ...
```

Writable scalar slots use zero-dimensional NumPy arrays:

```python
import numpy as np

base = np.array(4, dtype=np.int32)
status = np.empty((), dtype=np.int32)

module.scalar_status(base, status)
print(status[()])
```

This form also works for arrays and derived objects when their annotations
match the native arguments. For a fixed-width string, a Python `str` can be
passed, but changes made to its temporary native buffer are not visible unless
the contract returns a replacement.

## Reorder Arguments and Project Outputs

Use `Returns[...]` for a Python result and `@native_call(...)` when the native
procedure needs hidden output storage, reordered arguments, constants,
lengths, presence flags, shapes, or work buffers:

```python
from x2py.contracts import Addr, Arg, Int32, Return, Returns, native_call

@native_call([Addr(Arg(0)), Return("status", 0)])
def scalar_status(base: Int32) -> Returns["status", Int32]: ...
```

Here Python passes one value and receives the native `status` output. Every
required native argument must appear exactly once in the mapping. Missing,
duplicate, and out-of-range positions are errors.

The mapping may use entries such as `Arg(...)`, `Addr(...)`, `Value(...)`,
`Len(...)`, `IsPresent(...)`, and `Work(...)`. These entries describe the
existing native call; they cannot change what the implementation accepts. The
complete projection grammar will be covered by the Semantic `.pyi` Format
reference.

There is no `intent` annotation in the `.pyi`. The signature,
`Returns[...]`, and `@native_call(...)` are the complete contract after the
file is loaded.

## Control Mutation

`Immutable` means the original Python value must not change. A writable native
argument then needs an explicit replacement result or a supported rule that
discards the temporary mutation:

```python
from x2py.contracts import Annotated, Float64, Immutable, Returns

def scale(
    values: Annotated[Float64[:], Immutable],
) -> Returns["values", Float64[:]]: ...
```

x2py calls the native procedure with separate writable storage and returns the
replacement. The original array remains unchanged.

Do not combine replacement-only mutation with a writable borrowed view. Those
requests contradict each other and are rejected.

## Edit Types, Shapes, Layout, and Optionality

Annotations affect runtime checks; they are not only IDE hints:

```python
from x2py.contracts import Float64

def solve(
    matrix: Float64[3, 3],
    rhs: Float64[3],
) -> Float64[3]: ...
```

Supported edits include:

- changing an open dimension to a fixed size;
- selecting a supported contiguous layout;
- adding `Immutable` for a supported replacement path; and
- using `T | None` or a default `= ...` for an argument that is genuinely
  optional in the native procedure.

Changing dtype or rank, or inventing optionality, changes the declared native
binary interface. It is valid only when the implementation matches. x2py can
check exact NumPy dtype, rank, shape, layout, writeability, byte order,
alignment, and zero-sized-array rules. Plain multidimensional arrays in a
Fortran contract use Fortran order by default. The
[array guide](../../guide/arrays.md#what-x2py-validates) explains these checks.

## Translate Status Results into Exceptions

Use `@raises(...)` when a projected native status should become a Python
exception:

```python
from x2py.contracts import Addr, Arg, Int32, Return, String, native_call, raises

@raises(status="status", message="message", success=0)
@native_call([Addr(Arg(0)), Return("status", 0), Return("message", 1)])
def solve(value: Int32) -> tuple[Int32, String[32]]: ...
```

The named status and optional message must exist in the projected results. A
non-success status raises the generated exception before an ordinary result is
returned. See [Error Handling](../../guide/error-handling.md#status-projection-example)
for the Python behavior.

## Keep the GIL When Required

Ordinary native calls release Python's Global Interpreter Lock (GIL) when
their contract allows it. Use `@hold_gil` when the native call must invoke
Python immediately, such as a synchronous callback:

```python
from x2py.contracts import hold_gil

@hold_gil
def run_engine() -> None: ...
```

Remove `@hold_gil` to return to the normal GIL-releasing behavior when the call
is safe without it. This changes call behavior, not the native procedure
interface. It does not describe a callback signature; callback contracts are
covered in the [Callbacks](../../guide/callbacks.md) guide.

## Next

Most users can stop here. Return to
[Editing `.pyi` Contracts](index.md) to choose another edit.
