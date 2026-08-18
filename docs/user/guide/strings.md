---
title: Strings
description: Immutable strings, mutable character storage, and NumPy byte arrays in prik
audience: users
prerequisites: data types, arrays
related: data-types.md, arrays.md, raw-addresses.md
status: maintained
publication: reviewed
---

# Strings

prik uses Python `str` for scalar character values.
Mutable character storage uses fixed-width NumPy bytes arrays.

The contract decides whether native mutation becomes a new `str` or changes
caller-owned storage.

## Choose A String Boundary

| Contract | Python value | Native mutation |
| --- | --- | --- |
| `String` | Variable-length `str` | Returned only when projected |
| `String[8]` | `str` encoded as exactly 8 bytes | Returned as a new `str` |
| `String[8][()]` | Rank-zero NumPy array with dtype `S8` | Visible in place |
| `String[8][count]` | NumPy bytes array with dtype `S8` | Visible in place |
| `Addr(String[8])` | Integer address | Visible through caller-owned memory |

Use normal string and NumPy contracts by default. Raw addresses are an
advanced boundary covered later in the guide.
`Returns[...]` tells the wrapper to return the changed value of an argument.

## Complete Example

The source, generated contract, edited contract, and Python calls below
describe the same string boundaries. The results remain visible below the four
views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Strings example">
<button class="prik-example-tab" id="strings-source-tab" type="button" role="tab" aria-controls="strings-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="strings-generated-contract-tab" type="button" role="tab" aria-controls="strings-generated-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="strings-contract-tab" type="button" role="tab" aria-controls="strings-contract" aria-selected="false" tabindex="-1">Edited contract</button>
<button class="prik-example-tab" id="strings-python-tab" type="button" role="tab" aria-controls="strings-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="strings-source" role="tabpanel" aria-labelledby="strings-source-tab" tabindex="0" markdown="1">

### Fortran source

Create `strings_api.f90`:

```fortran
module strings_api
  implicit none
contains

  subroutine edit_text(text)
    character(len=8), intent(inout) :: text
    text(1:1) = "X"
  end subroutine edit_text

  subroutine edit_buffer(text)
    character(len=8), intent(inout) :: text
    text(1:1) = "X"
  end subroutine edit_buffer

  function make_text() result(text)
    character(len=8) :: text
    text = "ready"
  end function make_text

  subroutine edit_labels(count, labels)
    integer(4), intent(in) :: count
    character(len=8), intent(inout) :: labels(count)
    integer(4) :: index

    do index = 1, count
      labels(index)(1:1) = "X"
    end do
  end subroutine edit_labels

end module strings_api
```

</div>

<div class="prik-example-panel" id="strings-generated-contract" role="tabpanel" aria-labelledby="strings-generated-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `contracts/strings/strings_api.pyi` is:

```python
from prik.contracts import Addr, Arg, Int32, Returns, String, native_call

def edit_text(
    text: String[8]
) -> Returns["text", String[8]]: ...

def edit_buffer(
    text: String[8]
) -> Returns["text", String[8]]: ...

def make_text() -> String[8]: ...

@native_call([Addr(Arg(0)), Arg(1)])
def edit_labels(
    count: Int32,
    labels: String[8][count]
) -> None: ...
```

Generate it:

```bash
python3 -m prik generate --pyi strings_api.f90 --out contracts/strings
```

</div>

<div class="prik-example-panel" id="strings-contract" role="tabpanel" aria-labelledby="strings-contract-tab" tabindex="0" markdown="1">

## Edited Contract

Only `edit_buffer` changes. Rank-zero storage makes native mutation visible in
place rather than returning a replacement value. The edited
`contracts/strings/strings_api.pyi` is:

```python
from prik.contracts import Addr, Arg, Int32, Returns, String, native_call

def edit_text(
    text: String[8]
) -> Returns["text", String[8]]: ...

def edit_buffer(text: String[8][()]) -> None: ...

def make_text() -> String[8]: ...

@native_call([Addr(Arg(0)), Arg(1)])
def edit_labels(
    count: Int32,
    labels: String[8][count],
) -> None: ...
```

Build from the edited contract and native source:

```bash
python3 -m prik contracts/strings/__init__.pyi \
  --native-fortran-sources strings_api.f90 \
  --out-dir build/strings
```

For the complete result-mapping rules, see
[Reorder Arguments and Project Outputs](../reference/pyi-contracts/calls-and-results.md#reorder-arguments-and-project-outputs).

</div>

<div class="prik-example-panel" id="strings-python" role="tabpanel" aria-labelledby="strings-python-tab" tabindex="0" markdown="1">

## Immutable Values

`String[8]` accepts a Python `str` whose encoded length is exactly eight bytes.
The wrapper copies it into native storage.

```python
import sys

sys.path.insert(0, "build/strings")
from strings.strings_api import edit_text, make_text

original = "alpha   "
changed = edit_text(original)

print(repr(original))     # 'alpha   '
print(repr(changed))      # 'Xlpha   '
print(repr(make_text()))  # 'ready   '
```

Python strings are immutable. `Returns[...]` copies the changed native buffer
into a new `str`. Without that projection, the mutation is discarded.

## Mutable Scalar Storage

`String[8][()]` accepts a rank-zero NumPy bytes array.
Native writes change the same object.

```python
import sys

import numpy as np

sys.path.insert(0, "build/strings")
from strings.strings_api import edit_buffer

buffer = np.array("alpha   ", dtype="S8")
edit_buffer(buffer)

print(buffer[()])  # b'Xlpha   '
```

The public value is bytes storage. Reading `buffer[()]` returns `np.bytes_`,
not `str`.

## String Arrays

String arrays use fixed-width NumPy bytes dtypes. The dtype item size is the
Fortran character length.

```python
import sys

import numpy as np

sys.path.insert(0, "build/strings")
from strings.strings_api import edit_labels

labels = np.array([b"alpha   ", b"beta    "], dtype="S8")
edit_labels(np.int32(labels.size), labels)

print(labels)  # [b'Xlpha   ' b'Xeta    ']
```

The wrapper checks rank, shape, dtype, and writeability before the call.
Unicode and object arrays are rejected.

</div>
</div>

Result:

```text
'alpha   '
'Xlpha   '
'ready   '
b'Xlpha   '
[b'Xlpha   ' b'Xeta    ']
```

## Length And Encoding

- `String[8]` requires exactly eight encoded bytes.
- `String` accepts a runtime character length.
- Fixed-width results retain trailing Fortran blanks.
- Embedded NUL bytes are rejected for scalar Python strings.
- `String[8][()]` and `String[8][count]` require dtype `S8`.
- A dummy without `intent` uses the conservative `intent(inout)` behavior.

Deferred-length scalar storage (`character(len=:)`) is supported in two
places: a read-only `allocatable, intent(in)` argument, and an
`allocatable, intent(out)` result, which PRIK projects as a returned string.

Two forms are blocked before code generation. A mutable
`allocatable, intent(inout)` argument is rejected because the native procedure
may reallocate it to a length the caller's buffer cannot hold. A
`character(len=:), pointer` argument is rejected because the adapter has no
target to associate. Use a fixed-width buffer for both.

## Next

- Continue with [Wrapping Functions](wrapping-functions.md).
- [Wrapping Subroutines](wrapping-subroutines.md) for complete `intent` and
  result-projection rules.
- [Raw Addresses](raw-addresses.md) for the advanced `Addr(String[n])`
  boundary.
