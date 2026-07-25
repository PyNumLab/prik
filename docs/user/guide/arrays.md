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

x2py passes ordinary Fortran array arguments and array results as **NumPy
arrays**. This page covers the everyday path: create an array with the exact
dtype and layout the generated contract asks for, pass it to the wrapper, and
let x2py validate it before native code runs.

The contract records the important facts for each array: element dtype, rank,
shape, layout, stride policy, and whether the routine may write to the array.
The sections below start with the normal Fortran-layout path, then show how to
accept common C-order Python arrays and selected strided views intentionally.

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

The first routines cover ordinary Fortran arrays. `sum_columns` makes layout
visible by summing the first native axis of a square matrix, `sum_flat` covers
assumed-size storage, and `scale_visible_rows` accepts an assumed-shape array
that can be strided.

Build it:

```bash
python3 -m x2py arrays.f90 --out-dir build/arrays
```

---

## Python Usage

```python
import sys
import numpy as np

sys.path.insert(0, "build/arrays")
import arrays

api = arrays.array_ops

# Use Fortran order for a two-dimensional Fortran array.
matrix = np.ones((2, 3), dtype=np.float64, order="F")
api.scale_matrix(np.int32(2), np.int32(3), matrix)
np.testing.assert_array_equal(matrix, np.full((2, 3), 2.0, order="F"))

# The Fortran routine uses a lower bound, but Python still sees an ordinary ndarray.
shifted = np.zeros(4, dtype=np.float64)
api.shift(np.int32(4), shifted)
np.testing.assert_array_equal(shifted, np.ones(4, dtype=np.float64))

# Assumed-size arrays use flat contiguous storage.
flat_values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
assert api.sum_flat(np.int32(flat_values.size), flat_values) == np.float64(10.0)

# Array function results come back as NumPy arrays.
result = api.automatic_vector(np.int32(4))
np.testing.assert_array_equal(result, np.array([2.0, 4.0, 6.0, 8.0], dtype=np.float64))
```

---

## What x2py Checks

- Use **exact NumPy dtypes** (`np.float64`, `np.int32`, etc.).
- Rank must match the contract: a vector is not a matrix, even when the total
  number of elements is the same.
- Shape expressions must match the other arguments, such as `rows` and
  `columns` in the example above.
- Arrays written by Fortran must be writable.
- Contiguous contracts reject strided views. Strided contracts accept only the
  stride pattern they describe.
- No silent casting, copying, transposing, or layout conversion happens by
  default.

That strictness is intentional. A bad array fails at the Python boundary instead
of producing a confusing native-memory bug.

Contiguous means the elements are stored without gaps in the layout the
contract names. Fortran-contiguous and C-contiguous arrays can print the same
values but expose a different consecutive memory sequence to native code.
Strided views are useful, but only when the contract and the native routine are
prepared to receive stride metadata.

---

## Layout: Fortran First

Fortran stores multidimensional arrays in column-major order. For a normal
two-dimensional Fortran array contract, create the NumPy array with
`order="F"` or convert with `np.asfortranarray()` before calling the wrapper:

```python
values = np.asfortranarray(values, dtype=np.float64)
api.scale_matrix(np.int32(values.shape[0]), np.int32(values.shape[1]), values)
```

C-contiguous arrays are useful when a contract explicitly asks for C-order
storage. In semantic `.pyi` contracts, that is normally an explicit layout
annotation such as `ORDER_C`. x2py does not assume that a C-contiguous matrix is
close enough for a Fortran-contiguous contract; it rejects the mismatch so the
native routine sees the layout it was promised.

---

## C-order, Zero Copy

Many Python users naturally create row-major arrays. Start with the generated
Fortran-oriented contract for `sum_columns`:

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

api.sum_columns(np.int32(values.shape[0]), values, result)
np.testing.assert_allclose(result, [111.0, 222.0, 333.0])
```

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

api.sum_columns(np.int32(values.shape[0]), values, result)
np.testing.assert_allclose(result, [6.0, 60.0, 600.0])
```

Here `ORDER_C` says the Python-visible array must be C-contiguous. No
transposition happens. For the matrix above, the consecutive C-order storage
sequence is `[1.0, 2.0, 3.0, 10.0, 20.0, 30.0, 100.0, 200.0, 300.0]`, so the
native first-axis groups are Python rows. In Fortran order, the consecutive
sequence is `[1.0, 10.0, 100.0, 2.0, 20.0, 200.0, 3.0, 30.0, 300.0]`, so the
same routine returns column sums instead. x2py treats layout as part of the
contract and rejects the wrong order instead of guessing.

---

## C-order With COPY_F

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

api.sum_columns(np.int32(values.shape[0]), values, result)
np.testing.assert_allclose(result, [111.0, 222.0, 333.0])
```

`ORDER_C` says what layout Python may pass. `COPY_F` says x2py should create
the Fortran-order representation needed for the native call, preserving the
logical axes. If a visible output array also uses `COPY_F`, x2py copies the
Fortran-order result back into the caller's C-order storage after the call.

---

## Flat Storage

Fortran assumed-size dummies, such as `values(*)`, do not carry their final
extent in the dummy declaration. The caller supplies a real NumPy array, and a
companion argument such as `count` tells the native routine how much of that
storage to read.

The generated contract for `sum_flat` uses `Flat`:

```python
from x2py.contracts import Flat, Float64, Int32

def sum_flat(
    count: Int32,
    values: Float64[Flat],
) -> Float64: ...
```

The Python call is just a one-dimensional contiguous array plus the explicit
count:

```python
values = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
total = api.sum_flat(np.int32(values.size), values)
assert total == np.float64(10.0)
```

Use `Flat` for native interfaces that consume contiguous storage without a full
shape in the dummy declaration. It is not a shortcut for arbitrary reshaping or
strided slicing. Multidimensional flat-edge forms exist for older storage
interfaces, but the first rule stays the same: the semantic contract describes
the storage the native routine actually consumes.

---

## Strided Views Without Copies

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

api.scale_visible_rows(visible_rows, out)
np.testing.assert_allclose(out, 3.0 * visible_rows)
```

The important part is not the slice syntax itself. The important part is that
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
| `Float64[Flat]` | Assumed-size flat storage. |
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
