---
title: Arrays
description: How to pass NumPy arrays to Fortran routines with x2py — shape, layout, strides, and validation rules
audience: users
prerequisites: data types, wrapping functions
related: allocatables.md, pointers.md, wrapping-subroutines.md
status: maintained
publication: reviewed
---

# Arrays

x2py passes ordinary Fortran array arguments and results as **NumPy arrays**.
This page shows the everyday path: create arrays with the dtype, shape, layout,
and writeability required by the generated contract, then let x2py validate
those facts before native code runs.

The examples start with normal Fortran-layout arrays, then show the intentional
cases: accepting C-order arrays, copying C-order arrays into Fortran order,
passing flat assumed-size storage, and using selected strided views.

---

## Complete Example

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

`sum_columns` makes layout visible by summing the first native axis of a square
matrix. `sum_flat` covers rank-one assumed-size storage. `scale_visible_rows`
accepts an assumed-shape array that can be strided.

Build:

```bash
python3 -m x2py arrays.f90 --out-dir build/arrays
```

---

## Python Usage

```python
import sys
import numpy as np

sys.path.insert(0, "build/arrays")
from arrays.array_ops import (
    automatic_vector,
    scale_matrix,
    scale_visible_rows,
    shift,
    sum_columns,
    sum_flat,
)

# Fortran-order matrix, mutated in place.
matrix = np.ones((2, 3), dtype=np.float64, order="F")
scale_matrix(np.int32(2), np.int32(3), matrix)
# matrix is now filled with 2.0

# The Fortran routine uses a lower bound, but Python sees an ordinary ndarray.
shifted = np.zeros(4, dtype=np.float64)
shift(np.int32(4), shifted)
# shifted is now [1.0, 1.0, 1.0, 1.0]

# Rank-one assumed-size dummies read the contiguous storage sequence.
flat_matrix = np.asfortranarray(
    np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]], dtype=np.float64)
)
total = sum_flat(np.int32(flat_matrix.size), flat_matrix)
# total is np.float64(66.0)

# Array function results come back as NumPy arrays.
vec = automatic_vector(np.int32(4))
# vec is [2.0, 4.0, 6.0, 8.0]
```

---

## What x2py Validates

- Exact NumPy dtype, such as `np.float64` or `np.int32`.
- Rank and shape, including shape expressions such as `rows, columns`.
- Required layout and contiguity.
- Writeability for arrays exposed as `intent(out)` or `intent(inout)`.
- The declared stride pattern for stride-aware contracts.
- No silent casting, copying, transposing, or layout conversion by default.

Contiguous means the elements are stored without gaps in the layout the
contract names. Fortran-contiguous and C-contiguous arrays can print the same
values but expose a different consecutive memory sequence to native code.

That strictness is intentional. A bad array fails at the Python boundary instead
of producing a confusing native-memory bug.

---

## Layout: Fortran First

For normal Fortran multidimensional arrays, use Fortran order:

```python
values = np.asfortranarray(data, dtype=np.float64)
# or
values = np.ones(shape, dtype=np.float64, order="F")
```

x2py does not assume that a C-contiguous matrix is close enough for a
Fortran-contiguous contract. If the contract asks for Fortran order and you pass
C-order storage, the wrapper rejects the array before native code runs.

---

## Working With C-order Arrays

Start with the generated Fortran-oriented contract for `sum_columns`:

```python
from x2py.contracts import Float64, Int32

def sum_columns(
    size: Int32,
    values: Float64[size, size],
    result: Float64[size],
) -> None: ...
```

With that contract, pass a Fortran-order matrix. The routine sums columns:

```python
values = np.array(
    [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [100.0, 200.0, 300.0]],
    dtype=np.float64,
    order="F",
)
result = np.empty(values.shape[0], dtype=np.float64)

sum_columns(np.int32(values.shape[0]), values, result)
# result is [111.0, 222.0, 333.0]
```

### Option 1: Zero Copy

If you intentionally want the same routine to accept a C-contiguous square
matrix without copying, edit the semantic `.pyi` contract to require `ORDER_C`:

```python
from x2py.contracts import Annotated, Float64, Int32, ORDER_C

def sum_columns(
    size: Int32,
    values: Annotated[Float64[size, size], ORDER_C],
    result: Float64[size],
) -> None: ...
```

The Python call still looks the same, but the array is now C-order. The same
printed matrix produces row sums:

```python
values = np.array(
    [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [100.0, 200.0, 300.0]],
    dtype=np.float64,
    order="C",
)
result = np.empty(values.shape[0], dtype=np.float64)

sum_columns(np.int32(values.shape[0]), values, result)
# result is [6.0, 60.0, 600.0]
```

No transposition happens. For the matrix above, the consecutive C-order storage
sequence is `[1.0, 2.0, 3.0, 10.0, 20.0, 30.0, 100.0, 200.0, 300.0]`, so the
native first-axis groups are Python rows. In Fortran order, the consecutive
sequence is `[1.0, 10.0, 100.0, 2.0, 20.0, 200.0, 3.0, 30.0, 300.0]`, so the
same routine returns column sums instead.

### Option 2: COPY_F

Sometimes you want the Python API to accept C-order arrays, but you still want
the native routine to behave exactly like the original Fortran-order call. Add
`COPY_F` beside `ORDER_C`:

```python
from x2py.contracts import Annotated, COPY_F, Float64, Int32, ORDER_C

def sum_columns(
    size: Int32,
    values: Annotated[Float64[size, size], ORDER_C, COPY_F],
    result: Float64[size],
) -> None: ...
```

Now callers still pass ordinary C-order NumPy arrays, but x2py copies the input
into a Fortran-order temporary before the native call. The result is back to the
original column sums:

```python
values = np.array(
    [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [100.0, 200.0, 300.0]],
    dtype=np.float64,
    order="C",
)
result = np.empty(values.shape[0], dtype=np.float64)

sum_columns(np.int32(values.shape[0]), values, result)
# result is [111.0, 222.0, 333.0]
```

`ORDER_C` says what layout Python may pass. `COPY_F` says x2py should create
the Fortran-order representation needed for the native call, preserving the
logical axes. If a visible output array also uses `COPY_F`, x2py copies the
Fortran-order result back into the caller's C-order storage after the call.

---

## Flat Storage

Fortran assumed-size dummies, such as `values(*)`, do not carry their extent in
the dummy declaration. The caller supplies a real NumPy array, and a companion
argument such as `count` tells the native routine how much storage to read.

The generated contract for `sum_flat` uses `Flat`:

```python
from x2py.contracts import Flat, Float64, Int32

def sum_flat(
    count: Int32,
    values: Float64[Flat],
) -> Float64: ...
```

The Python call may pass any contiguous NumPy rank. x2py flattens the storage
sequence to the rank-one native view that `values(*)` expects:

```python
values = np.asfortranarray(
    np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]], dtype=np.float64)
)
total = sum_flat(np.int32(values.size), values)
# total is np.float64(66.0)
```

Use `Flat` for native interfaces that consume contiguous storage without a full
shape in the dummy declaration. It is not a shortcut for arbitrary reshaping or
strided slicing. `Float64[Flat]` accepts contiguous arrays of rank 1 through 15,
then passes their element sequence as a rank-one native view. Storage order
still matters: Fortran-contiguous arrays flatten in column-major order, and
C-contiguous arrays flatten in row-major order.

Multidimensional flat-edge forms are different. `Float64[rows, Flat]` is a
rank-two contract: x2py validates rank two, dtype, Fortran contiguity, and the
`rows` extent, while the final `Flat` axis remains unconstrained.

---

## Strided Views

Some Fortran interfaces accept assumed-shape arrays that do not need contiguous
storage. `scale_visible_rows` is one of those routines. x2py can keep that
useful NumPy behavior visible with a stride-aware contract:

```python
from x2py.contracts import Float64, Returns

def scale_visible_rows(
    values: Float64[::, ::],
    out: Float64[::, ::],
) -> Returns["out", Float64[::, ::]]: ...
```

That contract can accept a view where one axis moves through memory with a
stride and the other axis stays dense:

```python
base = np.asfortranarray(
    np.arange(1, 25, dtype=np.float64).reshape((8, 3), order="F")
)

visible_rows = base[::2, :]                         # shape (4, 3)
out_storage = np.zeros((8, 3), dtype=np.float64, order="F")
out = out_storage[::2, :]                           # matching strided output

scale_visible_rows(visible_rows, out)
# out now contains 3.0 * visible_rows
```

x2py passes the base address, extents, and positive element strides that Fortran
needs, while still rejecting layouts the contract did not allow. Reversed
slices, broadcasted views, and C-order strided matrices are rejected for this
Fortran-oriented contract. Striding is not an order workaround.

---

## Mutation And Results

For array arguments, the generated contract tells you who owns the storage and
what changes you should expect:

| Fortran intent or result | Python behavior |
|--------------------------|-----------------|
| `intent(in)` array | Pass a NumPy array; native code reads it. |
| `intent(inout)` array | Pass a writable NumPy array; native code mutates it in place. |
| `intent(out)` array | Pass preallocated output storage when the contract exposes it. |
| Array function result | Receive a new NumPy array result. |

Python indexing stays normal NumPy indexing. Fortran lower bounds are part of
the native association rule, not a change to how Python indexes the array.

---

## Common Array Contracts

You do not usually write these by hand for source-driven builds, but they are
worth recognizing when you inspect generated contracts:

| Contract | Meaning |
|----------|---------|
| `Float64[:]` | One-dimensional contiguous array. |
| `Float64[:, :]` | Two-dimensional Fortran-contiguous array. |
| `Annotated[Float64[:, :], ORDER_C]` | Two-dimensional C-contiguous array. |
| `Annotated[Float64[:, :], ORDER_C, COPY_F]` | C-contiguous Python array copied to Fortran order for the native call. |
| `Float64[::]` | One-dimensional strided array. |
| `Float64[::, ::]` | Two-dimensional Fortran-oriented stride-aware array. |
| `Float64[rows, columns]` | Shape depends on other arguments. |
| `Float64[Flat]` | Assumed-size storage; accepts any contiguous rank and passes a rank-one native view. |
| `Float64[rows, Flat]` | Rank-two Fortran-contiguous storage with a checked first axis and flat final axis. |
| `Float64[...]` | Assumed-rank array, currently rank 1 through 15. |

For most user code, the practical rule is simple: start from the generated
`.pyi`, create NumPy arrays with the exact dtype and layout it names, and let
the wrapper enforce the rest.

---

## Next

- Continue with [Wrapping Functions](wrapping-functions.md).
- Use [Wrapping Subroutines](wrapping-subroutines.md) when a routine mutates
  caller-provided arrays in place.
- Move to [Allocatables](allocatables.md) and [Pointers](pointers.md) later when
  the Python API needs native allocation or association state, not just ordinary
  NumPy data.
- Check the [Language Feature Matrix](../language-support/feature-matrix.md) for supported and unsupported array forms.
