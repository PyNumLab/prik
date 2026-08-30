---
title: C Functions and Scalars
description: Build C scalar functions and shape their Python call surface
audience: users
prerequisites: C user guide overview
related: index.md, pointers-arrays-and-strings.md, ../../language-support/c-support.md, ../../reference/pyi-contracts/calls-and-results.md
status: maintained
publication: reviewed
---

# C Functions and Scalars

## Build a scalar C function

Create `native_math.c`, build it, and call the generated extension:

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C scalar workflow">
<button class="prik-example-tab" id="c-scalar-source-tab" type="button" role="tab" aria-controls="c-scalar-source" aria-selected="true">Source and build</button>
<button class="prik-example-tab" id="c-scalar-contract-tab" type="button" role="tab" aria-controls="c-scalar-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="c-scalar-python-tab" type="button" role="tab" aria-controls="c-scalar-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-scalar-source" role="tabpanel" aria-labelledby="c-scalar-source-tab" tabindex="0" markdown="1">

```c
double add(double left, double right) {
    return left + right;
}
```

```bash
python3 -m prik --language c native_math.c \
  --compiler cc \
  --out native_math \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-scalar-contract" role="tabpanel" aria-labelledby="c-scalar-contract-tab" tabindex="0" markdown="1">

The source build writes this editable `native_math.pyi` contract beside the
extension:

```python
from prik.contracts import Float64

def add(left: Float64, right: Float64) -> Float64: ...
```

Generate the contract without compiling when you only want to inspect it:

```bash
python3 -m prik generate --pyi --language c native_math.c --out native_math.pyi
```

</div>

<div class="prik-example-panel" id="c-scalar-python" role="tabpanel" aria-labelledby="c-scalar-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import native_math

print(native_math.add(np.float64(3.0), np.float64(2.5)))
```

```text
5.5
```

</div>
</div>

Pass the NumPy scalar matching the generated contract type—for example,
`np.float64` for a C `double`. C contract extraction writes one file rather
than the Fortran package layout; the [`.pyi` format
reference](../../reference/pyi-format.md#source-to-contract-layout) shows both
forms.

## Rename and reorder arguments

An authored contract can present an existing C ABI under a better Python name
and argument order. It names the real C symbol, then states each native
argument explicitly.

When the Python declaration and C symbol have the same name, omit `@bind`:
that name is the default native target. Use `@bind("native_name")` only for a
different C symbol.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C projection workflow">
<button class="prik-example-tab" id="c-projection-source-tab" type="button" role="tab" aria-controls="c-projection-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-projection-contract-tab" type="button" role="tab" aria-controls="c-projection-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-projection-python-tab" type="button" role="tab" aria-controls="c-projection-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-projection-source" role="tabpanel" aria-labelledby="c-projection-source-tab" tabindex="0" markdown="1">

Create `projected.c`:

```c
int combine_native(int right, int *left, int bias) {
    return 100 * right + 10 * *left + bias;
}

void read_status(int value, int *output) {
    *output = value + 1;
}
```

</div>

<div class="prik-example-panel" id="c-projection-contract" role="tabpanel" aria-labelledby="c-projection-contract-tab" tabindex="0" markdown="1">

Create `projected.pyi`:

```python
from prik.contracts import Addr, Arg, Int32, Return, bind, native_call

@bind("combine_native")
@native_call([Arg(1), Addr(Arg(0)), Int32(5)])
def combine(left: Int32, right: Int32) -> Int32: ...

@bind("read_status")
@native_call([Arg(0), Return("output", 0)])
def status(value: Int32) -> Int32: ...
```

`combine` is the Python name, `combine_native` is the linked C symbol,
`Addr(Arg(0))` passes the address of `left`, and `Int32(5)` supplies the literal
third native argument. `Return(...)` turns the output pointer into the Python
result.

```bash
python3 -m prik --language c projected.pyi \
  --native-c-sources projected.c \
  --compiler cc \
  --out projected \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-projection-python" role="tabpanel" aria-labelledby="c-projection-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import projected

print(projected.combine(np.int32(2), np.int32(3)))
print(projected.status(np.int32(7)))
```

```text
325
8
```

</div>
</div>

## Exact native scalar identities

Generated C contracts are target-specific. Distinct C types such as `long`
and `long long` may use the same public NumPy contract type while retaining
their exact native identity inside `@native_call(...)`:

```python
from prik.contracts import Arg, CLongLong, Float64, Int64, Return, native_call

@native_call([Arg(0)], result=CLongLong(Return(0)))
def llround(value: Float64) -> Int64: ...
```

The public signature continues to use ordinary NumPy contract types. Scalars
and scalar addresses accept that public dtype and convert at the native
boundary. Ranked arguments require the exact NumPy element storage so their
pointer path remains zero-copy. See [Preserve an Exact C Scalar at the Native
Call](../../reference/pyi-contracts/calls-and-results.md#preserve-an-exact-c-scalar-at-the-native-call)
for arguments, addresses, results, arrays, and exact-storage rules.

## Next

Continue with [Pointers, Arrays, and
Strings](pointers-arrays-and-strings.md) when a C parameter uses pointer
syntax.
