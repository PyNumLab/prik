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

## Allocatable And Pointer Scalar Strings

A scalar `character` dummy may carry the `allocatable` or `pointer` attribute,
at a deferred length (`character(len=:)`) or a declared one
(`character(len=8)`). Every combination is supported, in every direction:

| Fortran dummy | Python surface |
| --- | --- |
| `intent(in)` | A `str` argument. |
| `intent(out)` | A returned `str`, or `None` when the procedure leaves it unallocated or unassociated. |
| `intent(inout)` | A `str` argument that also returns the value the procedure left behind, or `None`. |
| function result | A returned `str`, or `None`. |

The attribute never changes the Python surface, and it never changes how the
value crosses into native code — a scalar string is always a byte buffer and a
length. It changes only the storage PRIK builds inside the generated adapter,
because an `allocatable` or `pointer` dummy will not accept a plain temporary as
its actual argument.

An update keeps its `str` argument and adds a return value, because the native
procedure chooses the new value during the call and the caller's string cannot
hold it:

```fortran
subroutine grow(value)
  character(len=:), allocatable, intent(inout) :: value
  if (allocated(value)) value = value // '!!!'
end subroutine grow
```

```python
print(grow("ab"))  # ab!!!
```

The Python string you pass is never modified; the reallocated value comes back
as the result. A procedure that deallocates the dummy returns `None`, which is
how you tell an unallocated result from an empty string:

```python
print(drop("abc"))  # None
print(repr(empty_out("abc")))  # ''
```

### Pointer Dummies And Native Storage

A `pointer` dummy needs an associated actual argument, so PRIK allocates a
target for the call. What happens to that target afterwards is the native
procedure's decision, and PRIK follows it:

| The native procedure… | Python receives | PRIK's target |
| --- | --- | --- |
| writes through the pointer | the edited value | freed after the call |
| leaves it alone | the value passed in | freed after the call |
| deallocates it | `None` | already freed; not freed again |
| nullifies it | `None` | orphaned by the procedure |
| reassociates it elsewhere | the new target's value | orphaned by the procedure |

PRIK copies the value out of whatever the dummy ends up holding and never frees
native storage, because it cannot know whether that storage is a static target,
a fresh allocation, or something the library still owns. Two consequences are
worth planning for: a procedure that reassociates or nullifies the dummy
orphans the target PRIK allocated for that call, and a procedure that returns a
freshly allocated pointer each call leaks unless it also frees it. Prefer an
`allocatable` dummy, whose release is unambiguous, when you control the Fortran
side.

### Spelling Them In A Contract

In a semantic `.pyi` contract, the attribute is a `native_call` projection and
the length is the first subscription after `String`:

| Contract | Fortran |
| --- | --- |
| `String` | `character(len=*)` — the caller fixes the length |
| `String[8]` | `character(len=8)` — exactly eight encoded bytes |
| `String[:]` | `character(len=:)` — the length comes from allocation |

So the procedure above generates:

```python
@native_call([Allocatable(Arg(0))])
def grow(value: String[:] | None) -> Returns["value", String[:]] | None: ...
```

`Allocatable(...)` and `Pointer(...)` carry the attribute, and they wrap the
argument, the projected output, or the result:

```python
@native_call([Pointer(Arg(0))])
def edit(value: String[4] | None) -> Returns["value", String[4]] | None: ...

@native_call([], result=Allocatable(Return(0)))
def build() -> String[:] | None: ...
```

Arrays keep the length in that same first slot and add their shape second, as in
`String[8][:]` or `Allocatable[String[:][:]]`. Keep the native call and
storage declarations accurate when editing; [Calls and
Results](../reference/pyi-contracts/calls-and-results.md) explains the shared
argument and result rules.

## Next

- Continue with [Wrapping Functions](wrapping-functions.md).
- [Wrapping Subroutines](wrapping-subroutines.md) for complete `intent` and
  result-projection rules.
- [Raw Addresses](raw-addresses.md) for the advanced `Addr(String[n])`
  boundary.
