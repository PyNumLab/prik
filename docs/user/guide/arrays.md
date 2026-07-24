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

x2py passes ordinary numeric Fortran arrays as **NumPy arrays**. Allocatable and pointer arrays use special handle types (`Allocatable[T[...]]` and `Pointer[T[...]]`). The semantic contract clearly specifies element type, rank, shape, layout, strides, and mutability.

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

  function automatic_vector(count) result(values)
    integer(4), intent(in) :: count
    real(8) :: values(count)
    integer(4) :: i

    values = [(2.0_8 * i, i = 1, count)]
  end function automatic_vector

end module array_ops
```

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

# In-place modification (Fortran order)
matrix = np.ones((2, 3), dtype=np.float64, order="F")
api.scale_matrix(np.int32(2), np.int32(3), matrix)
np.testing.assert_array_equal(matrix, np.full((2, 3), 2.0, order="F"))

# Lower-bound aware array
shifted = np.zeros(4, dtype=np.float64)
api.shift(np.int32(4), shifted)
np.testing.assert_array_equal(shifted, np.ones(4, dtype=np.float64))

# Array return value
result = api.automatic_vector(np.int32(4))
np.testing.assert_array_equal(result, np.array([2.0, 4.0, 6.0, 8.0], dtype=np.float64))
```

---

## Key Concepts

- Use **exact NumPy dtypes** (`np.float64`, `np.int32`, etc.).
- For multidimensional arrays intended for Fortran, use `order="F"` or `np.asfortranarray()`.
- The wrapper validates dtype, rank, shape, contiguity, and writeability **before** calling native code.
- No silent casting, copying, or layout conversion happens by default.

---

## Common Array Contracts

| Contract              | Meaning                                      |
|-----------------------|----------------------------------------------|
| `Float64[:]`          | 1D contiguous array                          |
| `Float64[:, :]`       | 2D Fortran-contiguous array                  |
| `Float64[::]`         | 1D strided array                             |
| `Float64[rows, columns]` | Shape depends on other arguments          |
| `Float64[Flat]`       | Assumed-size (flat) contiguous storage       |
| `Float64[...]`        | Assumed-rank (rank 1–15)                     |

---

## Next

- Learn about [Allocatables](allocatables.md) and [Pointers](pointers.md)
- See more examples in [Wrapping Subroutines](wrapping-subroutines.md)
- Check the [Language Feature Matrix](../language-support/feature-matrix.md) for supported and unsupported array forms.
