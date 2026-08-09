---
title: Arrays
description: NumPy array shape, layout, strides, and validation in prik
audience: users
prerequisites: data types
related: strings.md, allocatables.md, pointers.md, wrapping-subroutines.md
status: maintained
publication: reviewed
---

# Arrays

prik exposes Fortran arrays as **NumPy arrays**.
Each generated contract defines the accepted dtype, shape, layout,
writeability, and strides. prik validates these rules before native code runs.

This page starts with normal Fortran-order arrays. It then covers C-order
arrays, `COPY_F`, `Flat` storage, and strided views.

Small `intent` note for this page: `intent(in)` reads an array,
`intent(inout)` mutates it, and `intent(out)` fills caller-provided storage.
Without `intent`, prik conservatively uses the `intent(inout)` rule. The
subroutines page covers the full return rules.

---

## Complete Example

The page uses one module throughout. Its routines cover:

- `scale_matrix`: a 2D array mutated in place
- `shift`: lower bounds with normal Python indexing
- `sum_columns`: the effect of storage order
- `sum_flat`: `values(*)` assumed-size storage
- `sum_flat_columns`: a checked prefix and flat final axis
- `scale_visible_rows`: stride-aware assumed-shape arrays
- `automatic_vector`: an array function result

Create `arrays.f90`:

```fortran
module array_ops
  implicit none
contains

  subroutine scale_matrix(rows, columns, values)
    integer(4), intent(in) :: rows, columns
    real(8), intent(inout) :: values(rows, columns)
    values = 2.0_8 * values
  end subroutine scale_matrix

  subroutine shift(size, values)
    integer(4), intent(in) :: size
    real(8), intent(inout) :: values(0:size-1)
    values = values + 1.0_8
  end subroutine shift

  subroutine sum_columns(size, values, result)
    integer(4), intent(in) :: size
    real(8), intent(in) :: values(size, size)
    real(8), intent(out) :: result(size)
    integer(4) :: column

    do column = 1, size
      result(column) = sum(values(:, column))
    end do
  end subroutine sum_columns

  function sum_flat(count, values) result(total)
    integer(4), intent(in) :: count
    real(8), intent(in) :: values(*)
    real(8) :: total
    integer(4) :: index

    total = 0.0_8
    do index = 1, count
      total = total + values(index)
    end do
  end function sum_flat

  function sum_flat_columns(rows, columns, values) result(total)
    integer(4), intent(in) :: rows, columns
    real(8), intent(in) :: values(rows, *)
    real(8) :: total
    integer(4) :: row, column

    total = 0.0_8
    do column = 1, columns
      do row = 1, rows
        total = total + values(row, column)
      end do
    end do
  end function sum_flat_columns

  subroutine scale_visible_rows(values, out)
    real(8), intent(in) :: values(:, :)
    real(8), intent(out) :: out(:, :)

    out = 3.0_8 * values
  end subroutine scale_visible_rows

  function automatic_vector(count) result(values)
    integer(4), intent(in) :: count
    real(8) :: values(count)
    integer(4) :: i

    values = [(2.0_8 * i, i = 1, count)]
  end function automatic_vector

end module array_ops
```

Build:

```bash
python3 -m prik arrays.f90 --out-dir build/arrays
```

---

## Python Usage

```python
import sys
import numpy as np

sys.path.insert(0, "build/arrays")
from arrays.array_ops import *

# Fortran-order matrix, mutated in place.
matrix = np.ones((2, 3), dtype=np.float64, order="F")
scale_matrix(np.int32(2), np.int32(3), matrix)
print(matrix)
# [[2. 2. 2.]
#  [2. 2. 2.]]

# The Fortran routine uses a lower bound, but Python sees an ordinary ndarray.
shifted = np.zeros(4, dtype=np.float64)
shift(np.int32(4), shifted)
print(shifted)  # [1. 1. 1. 1.]

# A flat argument can read any contiguous rank.
flat_matrix = np.array(
    [
        [1.0, 2.0, 3.0],
        [10.0, 20.0, 30.0],
    ],
    dtype=np.float64,
    order="F",
)
total = sum_flat(np.int32(flat_matrix.size), flat_matrix)
print(total)  # 66.0

# A flat final axis keeps the prefix and flattens the rest.
panels = np.asfortranarray(
    np.arange(1, 25, dtype=np.float64).reshape((2, 3, 4), order="F")
)
panel_total = sum_flat_columns(np.int32(2), np.int32(12), panels)
print(panel_total)  # 300.0

# Array function results come back as NumPy arrays.
vec = automatic_vector(np.int32(4))
print(vec)  # [2. 4. 6. 8.]
```

---

## What prik Validates

- Exact NumPy dtype (`np.float64`, `np.int32`, ...)
- Correct rank and shape (including expressions such as `rows, columns`)
- Required layout and contiguity
- Writeability for `intent(out)` or `intent(inout)` arrays
- Declared stride pattern for stride-aware contracts

**prik does not silently cast, copy, transpose, or convert rejected caller
layouts.** A mismatch raises `TypeError` before native code runs. A generated
Boolean contract still accepts only `np.bool_` storage; when its numbered
`Bool8`-`Bool64` element type records a different native logical width, the
completed wrapper plan performs the required Boolean representation copy in
the Fortran bridge. That internal ABI adaptation is not a caller-side dtype or
layout coercion.

Contiguous elements have no gaps between them in the required layout.
Two arrays can print the same values but use different memory orders.

---

## Layout: Fortran First

Use Fortran (column-major) order for normal multidimensional arrays:

```python
values = np.asfortranarray(data, dtype=np.float64)
# or
values = np.ones(shape, dtype=np.float64, order="F")
```

prik rejects C-contiguous matrices for a Fortran-contiguous contract.
This gives the native routine the layout it expects.

---

## C-order Arrays

Start with the generated Fortran-oriented contract for `sum_columns`:

```python
from prik.contracts import Float64, Int32

def sum_columns(
    size: Int32,
    values: Float64[size, size],
    result: Float64[size],
) -> None: ...
```

With that contract, pass a Fortran-order matrix. The routine sums columns:

```python
values = np.array(
    [
        [1.0, 2.0, 3.0],
        [10.0, 20.0, 30.0],
        [100.0, 200.0, 300.0],
    ],
    dtype=np.float64,
    order="F",
)
result = np.empty(values.shape[0], dtype=np.float64)

sum_columns(np.int32(values.shape[0]), values, result)
print(result)  # [111. 222. 333.]
```

### Option 1: Accept C-order Without Copy

Edit the semantic `.pyi` and add `ORDER_C`:

```python
from prik.contracts import Annotated, Float64, Int32, ORDER_C

def sum_columns(
    size: Int32,
    values: Annotated[Float64[size, size], ORDER_C],
    result: Float64[size],
) -> None: ...
```

For the complete dtype, shape, layout, and optionality rules, see
[Edit Types, Shapes, Layout, and Optionality](../reference/pyi-contracts/calls-and-results.md#edit-types-shapes-layout-and-optionality).

The call does not change. Pass a C-order array instead.
The same values now produce row sums:

```python
values = np.array(
    [
        [1.0, 2.0, 3.0],
        [10.0, 20.0, 30.0],
        [100.0, 200.0, 300.0],
    ],
    dtype=np.float64,
    order="C",
)
result = np.empty(values.shape[0], dtype=np.float64)

sum_columns(np.int32(values.shape[0]), values, result)
print(result)  # [  6.  60. 600.]
```

No transposition happens. Native code reads the existing storage directly.

| Python layout | Native grouping | Result |
|---------------|-----------------|--------|
| Fortran order | Python columns  | `[111.0, 222.0, 333.0]` |
| C-order       | Python rows     | `[6.0, 60.0, 600.0]` |

### Option 2: Copy C-order to Fortran Order

Keep `ORDER_C` and add `COPY_F`:

```python
from prik.contracts import Annotated, COPY_F, Float64, Int32, ORDER_C

def sum_columns(
    size: Int32,
    values: Annotated[Float64[size, size], ORDER_C, COPY_F],
    result: Float64[size],
) -> None: ...
```

prik copies the input to Fortran order before the native call.
The routine returns the original column sums:

```python
values = np.array(
    [
        [1.0, 2.0, 3.0],
        [10.0, 20.0, 30.0],
        [100.0, 200.0, 300.0],
    ],
    dtype=np.float64,
    order="C",
)
result = np.empty(values.shape[0], dtype=np.float64)

sum_columns(np.int32(values.shape[0]), values, result)
print(result)  # [111. 222. 333.]
```

`ORDER_C` validates the caller's layout.
`COPY_F` creates the Fortran-order temporary while preserving logical axes.
For output arrays, prik copies the result back to the caller's C-order storage.

---

## Flat Storage

An assumed-size dummy such as `values(*)` does not declare its extent.
A companion argument such as `count` tells the routine how much storage to read.

The generated contract for `sum_flat` uses `Flat`:

```python
from prik.contracts import Flat, Float64, Int32

def sum_flat(
    count: Int32,
    values: Float64[Flat],
) -> Float64: ...
```

`Float64[Flat]` accepts a contiguous array with rank 1-15.
Native code sees its storage as rank one:

```python
values = np.array(
    [
        [1.0, 2.0, 3.0],
        [10.0, 20.0, 30.0],
    ],
    dtype=np.float64,
)
total = sum_flat(np.int32(values.size), values)
print(total)  # 66.0
```

Storage order controls flattening:

- Fortran-contiguous: column-major order
- C-contiguous: row-major order

`Flat` rejects strided slices; dtype and contiguity rules still apply.

`Flat` can appear at one edge of a multidimensional contract.
Other axes remain visible. prik collapses the remaining Python axes into one
native extent.

For `real(8) :: values(rows, *)`, the generated contract is:

```python
from prik.contracts import Flat, Float64, Int32

def sum_flat_columns(
    rows: Int32,
    columns: Int32,
    values: Float64[rows, Flat],
) -> Float64: ...
```

This accepts a Fortran-contiguous array of rank 2 or higher.
Shape `(2, 3, 4)` becomes the native shape `(2, 12)`:

```python
panels = np.asfortranarray(
    np.arange(1, 25, dtype=np.float64).reshape((2, 3, 4), order="F")
)

total = sum_flat_columns(np.int32(2), np.int32(12), panels)
print(total)  # 300.0
```

`Float64[:, Flat]` reads the leading extent from the array itself.

For C-order buffers, put `Flat` first:
`Annotated[Float64[Flat, columns], ORDER_C]`.
This checks the final Python axis and flattens the leading axes.

---

## Strided Views

Use `::` for an assumed-shape axis that accepts F-contiguous arrays and
positive-stride views without copying:

```python
from prik.contracts import Float64, Returns

def scale_visible_rows(
    values: Float64[::, ::],
    out: Float64[::, ::],
) -> Returns["out", Float64[::, ::]]: ...
```

Here, only the first Python axis is sliced:

```python
base = np.asfortranarray(
    np.arange(1, 25, dtype=np.float64).reshape((8, 3), order="F")
)

visible_rows = base[::2, :]  # shape (4, 3)
out_storage = np.zeros((8, 3), dtype=np.float64, order="F")
out = out_storage[::2, :]  # matching strided output

scale_visible_rows(visible_rows, out)
print(out)
# [[ 3. 27. 51.]
#  [ 9. 33. 57.]
#  [15. 39. 63.]
#  [21. 45. 69.]]
```

prik passes the base address, extents, and positive element strides. Reversed
slices, broadcasted views, and C-order strided matrices are rejected for this
Fortran-oriented contract. Strides are not an order workaround.

---

## Mutation and Results

| Fortran intent / result      | Python behavior                              |
|-----------------------------|----------------------------------------------|
| `intent(in)` array          | NumPy array read by native code              |
| `intent(inout)` array       | Mutated in place; no Python return            |
| `intent(out)` array         | Filled in place; no Python return             |
| Array without `intent`      | Mutated in place; no Python return            |
| Function returning array    | New NumPy array result                       |

---

## Common Array Contracts

`T` means a concrete primitive contract such as `Float64`, `Int32`, or
`Complex128`. The examples above use `Float64` because `arrays.f90` declares
`real(8)`.

Use this list when reading or editing a generated `.pyi` contract:

- `T[:]`: 1D contiguous
- `T[:, :]`: 2D Fortran-contiguous
- `Annotated[T[:, :], ORDER_C]`: 2D C-contiguous
- `Annotated[T[:, :], ORDER_C, COPY_F]`: C-order input, Fortran temporary
- `T[::]`: 1D strided
- `T[::, ::]`: 2D stride-aware
- `T[rows, columns]`: shape depends on other arguments
- `T[Flat]`: any contiguous rank, flattened to native rank one
- `T[rows, Flat]`: Fortran-contiguous; checked prefix, remaining axes flattened
- `Annotated[T[Flat, columns], ORDER_C]`: C-contiguous; checked suffix,
  leading axes flattened
- `T[...]`: assumed-rank, currently rank 1-15

Generated shape expressions use Python and NumPy vocabulary even when the
source declaration used Fortran inquiry intrinsics:

| Fortran declaration expression | Generated `.pyi` expression |
|--------------------------------|-------------------------------|
| `size(values)`                 | `values.size`                 |
| `size(values, 2)`              | `values.shape[1]`             |
| `rank(values)`                 | `values.ndim`                 |
| `lbound(values, 2)`            | declared lower bound, or `1` when empty |
| `ubound(values, 2)`            | lower bound plus `values.shape[1] - 1`, or `0` when empty |
| first-axis extent              | `len(values)` or `values.shape[0]` |
| `extent_for(n)`                | `extent_for(n)`                |

Scalar integer arguments, arithmetic, comparisons, conditional expressions,
and `abs`, `int`, `min`, `max`, `len`, and `sum` can be combined in a shape.
Array attributes are limited to `.size`, `.ndim`, and `.shape[index]` on a
visible array argument. A user specification-function call remains a native
function call and is never evaluated as Python. A local function resolves to
the current native module, while a function named by a `USE` import retains
that import's source module and original native name. The bridge accesses both
through `use` and their compiler-produced `.mod` interfaces.

A standalone specification function has no `.mod` interface. Its semantic
contract therefore supplies an exact prototype and calls that prototype name
in the declaration expression:

```python
from prik.contracts import Addr, In, Int32, prototype, pure

@pure
@prototype
def extent_for(n: In(Addr(Int32))) -> Int32: ...
```

The bridge emits the signature as an abstract Fortran interface with a
generated `prik_` name, declares `extent_for` with `procedure(prik_...)`, and
evaluates the call natively when result allocation or another bridge-owned
shape needs the integer. For a caller-provided dummy array, the Python binding
still validates dtype, rank, ordering, contiguity, and writability, but it does
not duplicate the native procedure's explicit-extent check or call the
specification function. It passes the actual extents to the bridge. For a
returned array, the main bridge returns each natively evaluated extent through
its existing call ABI so the binding can construct the NumPy result; no
separate interoperability wrapper is generated for `extent_for`. The bridge
evaluates each such axis once, allocates its local result storage from the
recorded integer extent, and reuses that extent for NumPy construction.

Do not also use this pure prototype as a Python callback annotation. A
specification function must be pure, while PRIK's callback adapter necessarily
calls the Python runtime and cannot satisfy a pure Fortran procedure contract.
Policy completion reports that mixed use as a named blocker before planning.

The linked implementation still comes from the user-supplied native objects or
libraries. Impure or noninteger functions, incompatible arguments, inaccessible module
procedures, unresolved origins, and expressions depending on private native
state remain explicit policy blockers rather than guessed boundary values.

The lower bound is the bound of the Fortran dummy declaration, not Python's
zero-based index origin. For an assumed-shape dummy, an omitted lower bound is
one; an explicit bound such as `0:` or `start:` is retained. The common
`ubound(values, d) - lbound(values, d) + 1` expression is therefore emitted as
the corresponding `values.shape[d - 1]` extent.

---

## Next

- Continue with [Strings](strings.md) for fixed-width NumPy byte arrays.
- Then read [Wrapping Functions](wrapping-functions.md) and
  [Wrapping Subroutines](wrapping-subroutines.md).
- [Allocatables](allocatables.md) and [Pointers](pointers.md) for native
  allocation control.
