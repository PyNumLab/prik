---
title: C Pointers, Arrays, and Strings
description: Give C pointer parameters precise Python and NumPy contracts
audience: users
prerequisites: C functions and scalars
related: functions-and-scalars.md, outputs-and-errors.md, ../../language-support/c-support.md, ../../reference/pyi-contracts/calls-and-results.md
status: maintained
publication: reviewed
---

# C Pointers, Arrays, and Strings

C syntax cannot tell whether `double *` represents one scalar, an output, or
the first element of an array. A source-generated contract therefore starts
with runtime-rank caller-owned storage such as `Float64[...]`. It accepts a
zero-dimensional or higher-rank NumPy array without guessing one fixed rank.
Edit the semantic `.pyi` when the Python API should require a scalar value,
one exact rank, or a projected result.

## Author a contract for pointers and arrays

When a pointer is a NumPy buffer, state its shape and the native call order in
the contract:

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C array workflow">
<button class="prik-example-tab" id="c-array-source-tab" type="button" role="tab" aria-controls="c-array-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-array-contract-tab" type="button" role="tab" aria-controls="c-array-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-array-python-tab" type="button" role="tab" aria-controls="c-array-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-array-source" role="tabpanel" aria-labelledby="c-array-source-tab" tabindex="0" markdown="1">

Create `scale.c`:

```c
#include <stddef.h>

void scale(size_t count, double *values) {
    for (size_t index = 0; index < count; ++index) {
        values[index] *= 2.0;
    }
}
```

</div>

<div class="prik-example-panel" id="c-array-contract" role="tabpanel" aria-labelledby="c-array-contract-tab" tabindex="0" markdown="1">

Create `scale.pyi`:

```python
from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).shape[0], Arg(0)])
def scale(values: Float64[:]) -> None: ...
```

`Arg(0).shape[0]` provides `count`; `Arg(0)` passes the NumPy buffer to
`double *values`.

```bash
python3 -m prik --language c scale.pyi \
  --native-c-sources scale.c \
  --compiler cc \
  --out scale \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-array-python" role="tabpanel" aria-labelledby="c-array-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import scale

values = np.array([1.0, 2.0, 3.0], dtype=np.float64)
scale.scale(values)
print(values)
```

```text
[2. 4. 6.]
```

</div>
</div>

Runtime-rank pointer storage accepts ranks 0 through 15 with primitive
non-Boolean elements, and it constrains neither ordering nor strides: a
Fortran-ordered array and a strided slice are both accepted. PRIK validates
dtype, rank, any declared shape, layout, and writeability before calling C.
An explicit shape such as `Float64[:]` still requires C-contiguous storage.

## Choose the pointer contract

`Arg(i)` uses the annotation's normal C representation: a numeric scalar
crosses by value, while rank-zero and array storage cross by address. Use
`Addr(Arg(i))` only when a scalar must become a C pointer.

Every row below is a valid edit of the generated `Float64[...]`. Choose the row
whose Python column matches the API you want, and the caller passes exactly
that:

| Python contract | Accepted Python value | `@native_call` entry | Native effect |
| --- | --- | --- | --- |
| `value: Float64` | `np.float64(3.0)` | `Arg(0)` | Passes `double` by value, not a pointer. |
| `value: Float64` | `np.float64(3.0)` | `Addr(Arg(0))` | Passes the address of call-local storage; native mutation is discarded unless returned. |
| `value: Float64[()]` | `np.array(3.0)` | `Arg(0)` | Passes the address of caller-owned rank-zero storage; native mutation is visible. |
| `values: Float64[:]` | `np.array([1.0, 2.0])` | `Arg(0)` | Requires rank one, contiguous. |
| `values: Float64[4]`, `Float64[n]` | a contiguous rank-one array of that extent | `Arg(0)` | Requires rank one and validates the declared extent. |
| `values: Float64[:, :]` | `np.ones((2, 3))` | `Arg(0)` | Requires rank two, C-contiguous. |
| `values: Float64[...]` | any of the above **except** `np.float64(3.0)` | `Arg(0)` | Passes the data address of caller-owned storage of any rank 0 through 15 and any strides. |
| `Annotated[Float64[...], Contiguous]` | the same, restricted to C-contiguous storage | `Arg(0)` | The same runtime rank, narrowed to C-contiguous storage. |

The `@native_call` entry is optional when it would be `[Arg(0), Arg(1), ...]`
in declaration order; write one only to reorder, project, or hide arguments.

Two distinctions decide most edits:

- **`Float64` versus `Float64[()]`.** Both correspond to `double *`. `Float64`
  takes a Python scalar and needs `Addr(Arg(0))` to become a pointer, and the
  native write lands in call-local storage the caller never sees. `Float64[()]`
  takes `np.array(3.0)`, is already an address, and the native write is visible
  in the caller's array.
- **`Float64[...]` versus an exact shape.** `Float64[...]` accepts rank 0
  through 15 and any strides, so it fits a pointer whose meaning the source did
  not settle. An exact shape states the rank the function actually requires and
  lets PRIK validate extents and layout for you.

Do not wrap `Float64[()]` or an array in `Addr(...)`; their native
representation is already an address. `Addr(Float64)` as an *annotation* is a
different form — a Python integer holding a raw native address — and it is
**not** supported on the direct C route; a contract that uses it is rejected
with `C_DIRECT_RAW_ADDRESS` before the build runs. Use `Float64` plus
`Addr(Arg(0))` when you want an address taken for you, or `Float64[()]` when
the caller should own the storage.

Return a modified call-local scalar explicitly:

```python
from prik.contracts import Addr, Arg, Float64, Returns, native_call

@native_call([Addr(Arg(0))])
def scale_scalar(value: Float64) -> Returns["value", Float64]: ...
```

`Float64[...]` does not pass a rank or extent to C. When a native parameter
needs the total element count, project the array's `size`:

```python
from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).size, Arg(0)])
def scale(values: Float64[...]) -> None: ...
```

## Pass a layout the caller chose

`Float64[...]` accepts whatever strides the caller's array already has, and
PRIK passes only the data address. Project the layout the native code needs:

| Projection | Value the binding materializes |
| --- | --- |
| `Arg(i).size` | Total number of elements. |
| `Arg(i).shape[d]` | Extent of axis `d`. |
| `Arg(i).strides[d]` | Stride of axis `d` **in bytes**, exactly as `ndarray.strides` reports it. |

```python
from prik.contracts import Arg, Float64, Int64, native_call

@native_call([Arg(0).shape[0], Int64(Arg(0).strides[0]), Arg(0)])
def scale(values: Float64[...]) -> None: ...
```

```c
void scale(size_t count, long long stride_bytes, double *values);
```

An axis projection requires the actual to have that axis. `Arg(0).shape[0]`
against rank-zero storage raises `TypeError` rather than reading past the
array's shape, so narrow the annotation to `Float64[:]` when the function
always needs rank one.

A native routine that walks `values[index]` needs contiguous elements. Either
pass the stride the routine should honor, or require contiguity in the
contract; `Arg(i).size` alone does not make a strided view safe to walk
contiguously.

```python
from prik.contracts import Annotated, Arg, Contiguous, Float64, native_call

@native_call([Arg(0).size, Arg(0)])
def scale(values: Annotated[Float64[...], Contiguous]) -> None: ...
```

`Contiguous` keeps runtime ranks 0 through 15 and rejects an actual that is
not C-contiguous.

The contract cannot infer how many elements native code accesses. Keep a
native count visible, derive it with `.size` or `.shape[d]`, or declare an
exact shape as appropriate. When the source declares `const T *`, do not
author writable storage or write-back through it.

## Pass C strings

Choose the string contract from what the C function does with the pointer:

| C parameter | Contract | Python value |
| --- | --- | --- |
| Read-only `const char *` | `String` | Python `str` |
| Writable `char *` | `String[n][()]` or `String[...][()]` | Rank-zero NumPy `S` array |

`String` borrows the UTF-8 buffer of the Python `str`; the C function must not
write through it. Writable strings use caller-owned NumPy bytes storage. A
declared capacity such as `String[32][()]` validates the array itemsize, while
`String[...][()]` accepts the caller's itemsize.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C string workflow">
<button class="prik-example-tab" id="c-string-source-tab" type="button" role="tab" aria-controls="c-string-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-string-contract-tab" type="button" role="tab" aria-controls="c-string-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-string-python-tab" type="button" role="tab" aria-controls="c-string-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-string-source" role="tabpanel" aria-labelledby="c-string-source-tab" tabindex="0" markdown="1">

Create `text.c`:

```c
#include <stddef.h>
#include <string.h>

int name_length(const char *text) {
    return (int)strlen(text);
}

void shout(const char *text, char *out) {
    size_t index = 0;
    for (; text[index]; ++index) {
        char value = text[index];
        out[index] = (value >= 'a' && value <= 'z') ? (char)(value - 32) : value;
    }
    out[index] = '\0';
}
```

</div>

<div class="prik-example-panel" id="c-string-contract" role="tabpanel" aria-labelledby="c-string-contract-tab" tabindex="0" markdown="1">

Create `text.pyi`:

```python
from prik.contracts import Int32, String

def name_length(text: String) -> Int32: ...

def shout(text: String, out: String[32][()]) -> None: ...
```

```bash
python3 -m prik --language c text.pyi \
  --native-c-sources text.c \
  --compiler cc \
  --out text \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-string-python" role="tabpanel" aria-labelledby="c-string-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import text

print(text.name_length("hello"))
buffer = np.array(b"", dtype="S32")
text.shout("hello", buffer)
print(buffer[()])
```

```text
5
b'HELLO'
```

</div>
</div>

When C uses an explicit byte length, pass it with `Len(Arg(i))` in
`@native_call(...)`. The contract does not impose a terminator convention.

## Next

Continue with [Outputs and Errors](outputs-and-errors.md) when pointer
parameters should become Python results or exceptions.
