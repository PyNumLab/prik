---
title: Raw Addresses
description: Pass primitive, array, and fixed-string storage addresses through semantic contracts
audience: advanced users
prerequisites: arrays, strings, editing .pyi contracts
related: data-types.md, arrays.md, strings.md
status: maintained
publication: reviewed
---

# Raw Addresses

`Addr(T)` makes an integer address part of the Python API.
prik casts the address and passes it to native code without owning the memory.

Use this boundary only when the API must expose an address. Prefer checked
scalar storage, arrays, and strings for normal wrappers.

## Checked Storage Or Raw Address

| Contract | Python argument | Validation |
| --- | --- | --- |
| `Int32[()]` | 0-D array with dtype `np.int32` | Dtype, rank, and writeability |
| `Addr(Int32)` | Integer address | Integer that fits a native address |
| `Float64[rows, columns]` | NumPy array | Dtype, shape, order, and writeability |
| `Addr(Float64[rows, columns])` | Integer address | Declared array sizes only |
| `String[8][()]` | 0-D NumPy bytes array with dtype `S8` | Dtype, length, and writeability |
| `Addr(String[8])` | Integer address | Declared fixed length only |

`T[()]` changes the Python storage representation, not the native primitive
datatype. It is usually the better choice for scalar mutation.

## `Addr(T)` And `Addr(Arg(...))`

These spellings describe different boundaries:

- `Addr(T)` means the Python caller passes an integer address.
- Inside `@native_call(...)`, `Arg(i)` selects Python argument `i`, and
  `Addr(Arg(i))` tells prik to pass that converted scalar by address.

The `@native_call(...)` decorator records how Python arguments are placed in
the native call. Arrays, rank-zero storage, strings, and raw addresses already
use storage addresses, so their `Arg(i)` entry does not need another
`Addr(...)`.

## Complete Example

The source, generated contract, edited contract, and Python calls below
describe the same raw-address boundary. The results remain visible below the
four views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Raw addresses example">
<button class="prik-example-tab" id="raw-addresses-source-tab" type="button" role="tab" aria-controls="raw-addresses-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="raw-addresses-generated-contract-tab" type="button" role="tab" aria-controls="raw-addresses-generated-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="raw-addresses-edited-contract-tab" type="button" role="tab" aria-controls="raw-addresses-edited-contract" aria-selected="false" tabindex="-1">Edited contract</button>
<button class="prik-example-tab" id="raw-addresses-python-tab" type="button" role="tab" aria-controls="raw-addresses-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="raw-addresses-source" role="tabpanel" aria-labelledby="raw-addresses-source-tab" tabindex="0" markdown="1">

### Fortran source

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

</div>

<div class="prik-example-panel" id="raw-addresses-generated-contract" role="tabpanel" aria-labelledby="raw-addresses-generated-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `contracts/raw/raw_api.pyi` preserves the checked storage and
projects mutable scalar and string arguments as results:

```python
from prik.contracts import Addr, Arg, Float64, Int32, Returns, String, native_call

@native_call([Addr(Arg(0))])
def increment(
    value: Int32
) -> Returns["value", Int32]: ...

@native_call([Addr(Arg(0)), Addr(Arg(1)), Arg(2)])
def scale(
    rows: Int32,
    columns: Int32,
    values: Float64[rows, columns]
) -> None: ...

def edit_label(
    label: String[8]
) -> Returns["label", String[8]]: ...
```

Generate it:

```bash
python3 -m prik generate --pyi raw_api.f90 --out contracts/raw
```

</div>

<div class="prik-example-panel" id="raw-addresses-edited-contract" role="tabpanel" aria-labelledby="raw-addresses-edited-contract-tab" tabindex="0" markdown="1">

## Edited Contract

Change the storage boundary so Python callers provide raw addresses. The final
`contracts/raw/raw_api.pyi` is:

```python
from prik.contracts import Addr, Arg, Float64, Int32, String, native_call

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
python3 -m prik contracts/raw/__init__.pyi \
  --native-fortran-sources raw_api.f90 \
  --out-dir build/raw
```

For other argument-order and result mappings, see
[Reorder Arguments and Project Outputs](../reference/pyi-contracts/calls-and-results.md#reorder-arguments-and-project-outputs).

</div>

<div class="prik-example-panel" id="raw-addresses-python" role="tabpanel" aria-labelledby="raw-addresses-python-tab" tabindex="0" markdown="1">

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

</div>
</div>

Result:

```text
4
[[2. 4.]
 [6. 8.]]
b'Xlpha   '
```

## Safety Rules

- Keep the NumPy or ctypes owner alive until the call returns.
- Do not pass the address of a temporary expression.
- Use the exact native dtype and alignment.
- Supply enough storage for every declared array extent.
- Match the native array ordering and layout.
- Use writable memory when native code may modify it.
- Treat address zero as null only when the native routine allows null.

prik cannot validate the addressed memory's lifetime, dtype, size, shape, order,
alignment, ownership, or writeability. A wrong address can crash the process.

## Next

- Continue with [Error Handling](error-handling.md).
