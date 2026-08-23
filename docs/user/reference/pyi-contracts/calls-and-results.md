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
from prik.contracts import Int32

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
from prik.contracts import Addr, Arg, Int32, Return, Returns, native_call

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

## Preserve an Exact C Scalar at the Native Call

A target-specific C contract may intentionally expose two distinct C types as
the same NumPy dtype. For example, both `long` and `long long` may use signed
64-bit values, so both public signatures use `Int64`. C still treats the two
native types as distinct.

Use a C scalar cast only around the affected native-call expression:

```python
from prik.contracts import Arg, CLongLong, Float64, Int64, native_call

@native_call([CLongLong(Arg(0)), Arg(1)])
def accumulate(count: Int64, scale: Float64) -> None: ...
```

The user passes a normal NumPy `int64`. The binding extracts it into
`int64_t`, then emits the native call as:

```c
accumulate((long long)contract_count, contract_scale);
```

The same sparse form records a native function result whose C identity was
lost by width-based normalization:

```python
from prik.contracts import Arg, CLongLong, Float64, Int64, Return, native_call

@native_call([Arg(0)], result=CLongLong(Return(0)))
def llround(value: Float64) -> Int64: ...
```

The decorator position determines the direction. A native scalar wrapper in
the ordered list describes a native parameter; it may wrap `Arg(i)` or an
output-parameter `Return(i)`. In `result=...`, it declares the native function
result. Here the binding declares a `long long` result, receives it, and
converts it into the public `Int64` result slot selected by `Return(0)`.

Unchanged arguments and results retain their ordinary lowering. Native C scalar
names are call-expression operators: using `CLongLong` or `CLong` as a
function annotation, field type, or return annotation is an error. Generated C
contracts add these operators only when the active target's canonical contract
storage is not C-compatible with the source declaration.

For a scalar address, conversion happens before taking the address:

```python
@native_call([Addr(CLongLong(Arg(0)))])
def update(value: Int64) -> Int64: ...
```

This converts the extracted `int64_t` into a `long long` call-local and passes
that local's address, so the callee receives a genuine `long long *`. It never
casts `int64_t *` to an incompatible pointer type.

For a ranked argument, the same operator selects the exact NumPy storage that
can cross the pointer boundary without a cast:

```python
@native_call([CLongLong(Arg(0))])
def update_many(values: Int64[:]) -> None: ...
```

The public value type remains signed 64-bit integer, but the caller must supply
an array created with `dtype=numpy.longlong` when `long long` is distinct from
the target's canonical `int64_t`. An ordinary `numpy.int64` array is rejected
on that target even when it has the same width and representation. The binding
passes the accepted `numpy.longlong` storage directly as `long long *`; it does
not reinterpret an incompatible pointer or allocate a conversion copy.
This exact-storage rule applies to every supported signed, unsigned, real, and
complex C scalar type with corresponding NumPy storage, including `CLong`,
`CUnsignedLongLong`, and `CLongDoubleComplex`. C `_Bool` arrays remain
unsupported because NumPy Boolean array storage is not C `_Bool` storage.

There is no `intent` annotation in the `.pyi`. The signature,
`Returns[...]`, and `@native_call(...)` are the complete contract after the
file is loaded.

## Control Mutation

`Immutable` means the original Python value must not change. A writable native
argument then needs an explicit replacement result or a supported rule that
discards the temporary mutation:

```python
from prik.contracts import Annotated, Float64, Immutable, Returns

def scale(
    values: Annotated[Float64[:], Immutable],
) -> Returns["values", Float64[:]]: ...
```

prik calls the native procedure with separate writable storage and returns the
replacement. The original array remains unchanged.

Do not combine replacement-only mutation with a writable borrowed view. Those
requests contradict each other and are rejected.

## Edit Types, Shapes, Layout, and Optionality

Annotations affect runtime checks; they are not only IDE hints:

```python
from prik.contracts import Float64

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
binary interface. It is valid only when the implementation matches. prik can
check exact NumPy dtype, rank, shape, layout, writeability, byte order,
alignment, and zero-sized-array rules. Plain multidimensional arrays in a
Fortran contract use Fortran order by default. The
[array guide](../../guide/arrays.md#what-prik-validates) explains these checks.

## Advanced Array Shape Expressions

Generated contracts may translate native array extents into Python and NumPy
expressions:

| Native relationship | Semantic `.pyi` contract |
| --- | --- |
| total element count | `values.size` |
| second-axis extent | `values.shape[1]` |
| runtime rank | `values.ndim` |
| extent from an integer argument | `rows` or `rows + 1` |
| extent calculated by native code | `extent_for(n)` |

These expressions describe the existing native interface; they do not change
what the implementation accepts. Most users should leave generated shape
relationships unchanged. When editing one, use visible integer arguments and
the documented array properties shown above.

A native extent function remains a declarative native call—it is not executed
as Python. PRIK rejects unresolved, incompatible, or unsafe relationships
instead of guessing an array size.

## Translate Status Results into Exceptions

Use `@raises(...)` when a projected native status should become a Python
exception:

```python
from prik.contracts import Addr, Arg, Hidden, Int32, String, native_call, raises

@raises(status="status", message="message", success=0)
@native_call([Addr(Arg(0)), Hidden("status", Int32), Hidden("message", String[32])])
def solve(value: Int32) -> None: ...
```

Declare the status and any native-only message with `Hidden(name, T)`: it is
produced by the native call but never reaches Python, so it does not appear in
the return annotation. A message may instead name a visible rank-zero NumPy
bytes buffer that the caller supplies. A non-success status raises the generated
exception before an ordinary result is returned. See [Error
Handling](../../guide/error-handling.md#status-projection-example) for the
Python behavior.

## Release the GIL for a Native Call

Native calls keep Python's Global Interpreter Lock (GIL) by default. Use
`@nogil` only when the native call can safely run while other Python threads
execute:

```python
from prik.contracts import nogil

@nogil
def run_parallel_engine() -> None: ...
```

`@nogil` accepts no arguments and releases the GIL only around the native
bridge call. Argument conversion, result conversion, writeback, cleanup, and
exception projection still run with the GIL held. Remove `@nogil` to restore
the default held-GIL behavior. This changes call behavior, not the native
procedure interface.

If a decorated native call invokes a PRIK callback, the callback trampoline
temporarily reacquires the GIL for Python execution. Callback contracts are
covered in the [Callbacks](../../guide/callbacks.md) guide.

## Next

Most users can stop here. Return to
[Editing `.pyi` Contracts](index.md) to choose another edit.
