---
title: Raw Addresses
description: Pass primitive, array, and fixed-string storage addresses through semantic contracts
audience: advanced users
prerequisites: arrays, strings, editing semantic pyi contracts
related: data-types.md, arrays.md, strings.md, ../reference/editing-semantic-pyi-contracts.md, ../reference/semantic-pyi-format.md
status: maintained
publication: reviewed
---

# Raw Addresses

`Addr(T)` makes an integer address part of the Python API.
x2py casts the address and passes it to native code without owning the memory.

Use this boundary only when the API must expose an address. Prefer checked
scalar storage, arrays, and strings for normal wrappers.

## Checked Storage Or Raw Address

| Contract | Python argument | Validation |
| --- | --- | --- |
| `Int32[()]` | 0-D array with dtype `np.int32` | Dtype, rank, and writeability |
| `Addr(Int32)` | Integer address | Pointer-sized integer only |
| `Float64[rows, columns]` | NumPy array | Dtype, shape, order, and writeability |
| `Addr(Float64[rows, columns])` | Integer address | Extent expressions only |
| `String[8][()]` | 0-D NumPy bytes array with dtype `S8` | Dtype, length, and writeability |
| `Addr(String[8])` | Integer address | Declared fixed length only |

`T[()]` changes the Python storage representation, not the native primitive
datatype. It is usually the better choice for scalar mutation.

## Complete Example

Create `raw_api.f90`:

```fortran
module raw_api
  implicit none
contains

  subroutine increment(value)
    integer(4), intent(inout) :: value
    value = value + 1
  end subroutine increment

  subroutine scale(rows, columns, values)
    integer(4), intent(in) :: rows, columns
    real(8), intent(inout) :: values(rows, columns)
    values = 2.0_8 * values
  end subroutine scale

  subroutine edit_label(label)
    character(len=8), intent(inout) :: label
    label(1:1) = "X"
  end subroutine edit_label

end module raw_api
```

Generate a starter contract:

```bash
python3 -m x2py generate --pyi raw_api.f90 --out contracts/raw
```

Edit `contracts/raw/raw_api.pyi`:

```python
from x2py.contracts import Addr, Arg, Float64, Int32, String, native_call

def increment(value: Addr(Int32)) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2)])
def scale(
    rows: Int32,
    columns: Int32,
    values: Addr(Float64[rows, columns]),
) -> None: ...

def edit_label(label: Addr(String[8])) -> None: ...
```

Build from the edited contract and native source:

```bash
python3 -m x2py contracts/raw/__init__.pyi \
  --native-fortran-sources raw_api.f90 \
  --out-dir build/raw
```

## Primitive Address

Keep the NumPy owner in a variable for the full call:

```python
import sys

import numpy as np

sys.path.insert(0, "build/raw")
from raw.raw_api import increment

value = np.array(3, dtype=np.int32)
increment(value.ctypes.data)

print(value[()])  # 4
```

For checked mutation, use `Int32[()]` instead. The call then accepts `value`
directly and validates its storage.

## Array Address

`array.ctypes.data` is the address of the first array element.
The owner must contain enough storage for every declared extent.

```python
import sys

import numpy as np

sys.path.insert(0, "build/raw")
from raw.raw_api import scale

values = np.asfortranarray(
    [[1.0, 2.0], [3.0, 4.0]],
    dtype=np.float64,
)

scale(np.int32(2), np.int32(2), values.ctypes.data)
print(values)
# [[2. 4.]
#  [6. 8.]]
```

The raw address does not carry shape, order, or strides. Passing C-order
storage does not make a Fortran routine use C ordering.

Every raw array extent must use a literal or a visible scalar argument.
Unresolved forms such as `Addr(Float64[:])` are invalid.

## Fixed-String Address

A fixed string address points to exactly the declared number of bytes.
Use a NumPy `S8` owner for `Addr(String[8])`:

```python
import sys

import numpy as np

sys.path.insert(0, "build/raw")
from raw.raw_api import edit_label

label = np.array("alpha   ", dtype="S8")
edit_label(label.ctypes.data)

print(label[()])  # b'Xlpha   '
```

This mutates bytes storage. It does not return a Python `str`.
Use `String[8]` with `Returns[...]` when the result should be immutable text.
Use `String[8][()]` when the wrapper should validate mutable storage.

## Safety Rules

- Keep the NumPy or ctypes owner alive until the call returns.
- Do not pass the address of a temporary expression.
- Use the exact native dtype and alignment.
- Supply enough storage for every declared array extent.
- Match the native array ordering and layout.
- Use writable memory when native code may modify it.
- Treat address zero as null only when the native routine allows null.

x2py cannot validate the pointee's lifetime, dtype, size, shape, order,
alignment, ownership, or writeability. A wrong address can crash the process.

## `Addr(T)` And `Addr(Arg(...))`

These spellings describe different boundaries:

- `Addr(T)` means the Python caller passes an integer address.
- `Addr(Arg(i))` means x2py takes the address of a converted scalar argument.

Arrays, rank-zero storage, strings, and raw addresses already use storage
addresses. Do not wrap their `Arg(i)` projection in another `Addr(...)`.

## Next

- [Strings](strings.md) for immutable and checked mutable character boundaries
- [Editing Semantic `.pyi` Contracts](../reference/editing-semantic-pyi-contracts.md)
- [Semantic `.pyi` Format](../reference/semantic-pyi-format.md) for complete
  `Addr(...)` validation rules
