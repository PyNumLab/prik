---
title: C Support
description: Build supported C APIs as NumPy-aware Python extensions.
audience: users
prerequisites: installation, basic Python and NumPy
related: index.md, feature-matrix.md, ../reference/cli-commands.md, ../reference/python-api.md, ../reference/pyi-contracts/calls-and-results.md
status: maintained
publication: reviewed
---

# C Support

PRIK builds a supported subset of C APIs as importable Python extensions. The
generated binding calls your exported C symbol directly; there is no generated
C or Fortran adapter in between.

The C lane is best for standalone numerical functions with primitive values,
NumPy buffers, and explicit output storage. It is deliberately fail-closed:
parsing a declaration does not promise that it can be wrapped, and an unsupported
form stops the build before native compilation.

## Requirements

Install PRIK and NumPy, then make sure a C compiler and the development headers
for the Python that will import the extension are available. `cc` is the default
compiler; use `--compiler` when the native project requires another one.

To see the C types and NumPy dtypes selected for a particular compiler target,
run:

```bash
python3 -m prik probe --language c --compiler cc --format markdown
```

## Build a scalar C function

This first example is source-driven: PRIK reads the C declaration, builds the
extension, and writes an editable contract alongside it.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C scalar workflow">
<button class="prik-example-tab" id="c-scalar-source-tab" type="button" role="tab" aria-controls="c-scalar-source" aria-selected="true">Source and build</button>
<button class="prik-example-tab" id="c-scalar-contract-tab" type="button" role="tab" aria-controls="c-scalar-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="c-scalar-python-tab" type="button" role="tab" aria-controls="c-scalar-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-scalar-source" role="tabpanel" aria-labelledby="c-scalar-source-tab" tabindex="0" markdown="1">

Create `native_math.c`:

```c
double add(double left, double right) {
    return left + right;
}
```

Build it with an explicit language selection:

```bash
python3 -m prik --language c native_math.c \
  --compiler cc \
  --out native_math \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-scalar-contract" role="tabpanel" aria-labelledby="c-scalar-contract-tab" tabindex="0" markdown="1">

PRIK writes `build/contracts/native_math.pyi`:

```python
from prik.contracts import Float64

def add(left: Float64, right: Float64) -> Float64: ...
```

To inspect the contract without compiling, run:

```bash
python3 -m prik generate --pyi --language c native_math.c --out native_math.pyi
```

</div>

<div class="prik-example-panel" id="c-scalar-python" role="tabpanel" aria-labelledby="c-scalar-python-tab" tabindex="0" markdown="1">

Then import and call the extension:

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

PRIK validates arithmetic arguments at the native boundary. Pass the matching
NumPy scalar—for example, `np.float64` for a C `double`.

The source build writes an editable semantic `.pyi` contract beside the
extension. Use that contract when a pointer needs a more precise Python meaning
than the C declaration can express.

## Author a contract for pointers and arrays

C syntax cannot tell whether `double *` means one scalar or the first element
of an array. A source-generated contract therefore starts conservatively. When
the parameter is a NumPy buffer, state the shape and native call order in an
authored `.pyi` contract.

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

Supported arrays have ranks 1 through 15, primitive non-Boolean elements, and
C-contiguous NumPy storage. PRIK validates dtype, rank, shape, layout, and
writeability before calling C.

Use `Float64[()]` when the caller should provide one writable scalar slot.

### Choose the pointer contract

`Arg(i)` uses the annotation's normal C representation: a bare numeric scalar
crosses by value, while rank-zero and array storage cross by address. Use
`Addr(Arg(i))` only when a bare scalar must become a C pointer.

| C parameter | Python contract | `@native_call` entry | Native effect |
| --- | --- | --- | --- |
| `double value` | `value: Float64` | `Arg(0)` (or omit `@native_call`) | Passes `double` by value. |
| `double *value` | `value: Float64` | `Addr(Arg(0))` | Passes the address of call-local scalar storage; mutation is discarded unless returned. |
| `double *value` | `value: Float64[()]` | `Arg(0)` (or omit `@native_call`) | Passes the caller's zero-dimensional NumPy storage address; mutation is visible in place. |
| `double *values` | `values: Float64[:]`, `Float64[4]`, or `Float64[n]` | `Arg(0)` | Passes the validated C-contiguous NumPy data address. |

For an authored scalar read-back, write the address projection and return the
call-local value explicitly:

```python
from prik.contracts import Addr, Arg, Float64, Returns, native_call

@native_call([Addr(Arg(0))])
def scale_scalar(value: Float64) -> Returns["value", Float64]: ...
```

A source-generated contract for `double *value` already contains this
`Addr(Arg(0))` projection. Do not wrap `Float64[()]` or an array in `Addr(...)`:
their normal native representation is already an address.

Do not leave a pointer as a scalar when C indexes it as an array. A generated
source contract is conservative; promote the parameter to a shaped NumPy array
before calling a buffer API.

An authored contract is authoritative. If the source C declaration is
`const T *`, do not author writable storage or write-back through it: writing
through a const-qualified C pointer is undefined behavior.

## Rename, reorder, and address arguments

An authored contract can present an existing C ABI under a better Python name
and argument order. It names the real C symbol, then states each native
argument explicitly.

When the Python declaration and C symbol have the same name, omit `@bind`:
that name is the default native target. Use `@bind("native_name")` only for a
different C symbol. The same default applies to Fortran semantic contracts.

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

## Return several C outputs

Use a named `Return(...)` slot for every native output pointer that should
become part of the Python return value.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C multiple-output workflow">
<button class="prik-example-tab" id="c-stats-source-tab" type="button" role="tab" aria-controls="c-stats-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-stats-contract-tab" type="button" role="tab" aria-controls="c-stats-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-stats-python-tab" type="button" role="tab" aria-controls="c-stats-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-stats-source" role="tabpanel" aria-labelledby="c-stats-source-tab" tabindex="0" markdown="1">

Create `stats.c`:

```c
#include <stddef.h>

void stats_compute(size_t count, const double *values, double *mean, double *total) {
    double sum = 0.0;
    for (size_t index = 0; index < count; ++index) {
        sum += values[index];
    }
    *total = sum;
    *mean = count ? sum / (double)count : 0.0;
}
```

</div>

<div class="prik-example-panel" id="c-stats-contract" role="tabpanel" aria-labelledby="c-stats-contract-tab" tabindex="0" markdown="1">

Create `stats.pyi`:

```python
from prik.contracts import Arg, Float64, Return, Returns, bind, native_call

@bind("stats_compute")
@native_call([Arg(0).shape[0], Arg(0), Return("mean", 0), Return("total", 1)])
def summarize(values: Float64[:]) -> tuple[Returns["mean", Float64], Returns["total", Float64]]: ...
```

```bash
python3 -m prik --language c stats.pyi \
  --native-c-sources stats.c \
  --compiler cc \
  --out stats \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-stats-python" role="tabpanel" aria-labelledby="c-stats-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import stats

mean, total = stats.summarize(np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64))
print(mean, total)
```

```text
2.5 10.0
```

</div>
</div>

See [Calls and Results](../reference/pyi-contracts/calls-and-results.md) for
the full shared contract vocabulary.

## Pass C strings

Choose the string contract from what the C function does with the pointer:

| C parameter | Contract | Python value |
| --- | --- | --- |
| Read-only `const char *` | `String` | Python `str` |
| Writable `char *` | `String[n][()]` or `String[...][()]` | Rank-zero NumPy `S` array |

`String` borrows the UTF-8 buffer of the Python `str`, which CPython
NUL-terminates. The native function must not write through it. For writable
storage, use a caller-owned NumPy bytes array. A stated capacity such as
`String[32][()]` also checks the array itemsize; `String[...][()]` accepts the
itemsize the caller supplies.

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
`@native_call(...)`. The contract does not impose a terminator convention of
its own.

## Hide native outputs and raise Python exceptions

Use `Hidden(name, T)` for C output storage that Python never returns. This is
particularly useful for status values and diagnostic messages consumed by
`@raises`.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C status workflow">
<button class="prik-example-tab" id="c-status-source-tab" type="button" role="tab" aria-controls="c-status-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-status-contract-tab" type="button" role="tab" aria-controls="c-status-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-status-python-tab" type="button" role="tab" aria-controls="c-status-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-status-source" role="tabpanel" aria-labelledby="c-status-source-tab" tabindex="0" markdown="1">

Create `checked.c`:

```c
#include <string.h>

void checked_sqrt(double value, double *root, int *status, char *message) {
    if (value < 0.0) {
        *status = -1;
        *root = 0.0;
        strcpy(message, "value must not be negative");
        return;
    }
    *status = 0;
    message[0] = '\0';
    *root = value == 4.0 ? 2.0 : value;
}
```

</div>

<div class="prik-example-panel" id="c-status-contract" role="tabpanel" aria-labelledby="c-status-contract-tab" tabindex="0" markdown="1">

Create `checked.pyi`:

```python
from prik.contracts import Arg, Float64, Hidden, Int32, Return, Returns, String, native_call, raises

@raises(status="status", message="message", success=0)
@native_call([Arg(0), Return("root", 0), Hidden("status", Int32), Hidden("message", String[64])])
def checked_sqrt(value: Float64) -> Returns["root", Float64]: ...
```

```bash
python3 -m prik --language c checked.pyi \
  --native-c-sources checked.c \
  --compiler cc \
  --out checked \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-status-python" role="tabpanel" aria-labelledby="c-status-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import checked

print(checked.checked_sqrt(np.float64(4.0)))
try:
    checked.checked_sqrt(np.float64(-1.0))
except RuntimeError as error:
    print(error)
```

```text
2.0
value must not be negative
```

</div>
</div>

The function returns only `root`; `status` and `message` become a
`RuntimeError` on failure. A hidden message needs a fixed capacity because PRIK
allocates the native buffer.

A visible message buffer is also valid when the caller owns it:

```python
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Arg(1), Hidden("status", Int32)])
def checked(value: Float64, message: String[64][()]) -> None: ...
```

Here `message` is a rank-zero `np.ndarray` with dtype `S64`; the caller can
inspect it after the exception. `String` can also name a visible message when
the C API declares `const char *`; that borrows a Python `str`. If that native
code writes through the borrowed pointer, handling that unsafe contract is the
C API author's responsibility. Prefer NumPy storage for a writable message.

## Present several C symbols as one Python name

An authored contract can dispatch supported dtype/rank variants behind one
Python name. Mark the concrete candidates `@private`, then name them with
`@overload(...)`.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="C overload workflow">
<button class="prik-example-tab" id="c-overload-source-tab" type="button" role="tab" aria-controls="c-overload-source" aria-selected="true">C source</button>
<button class="prik-example-tab" id="c-overload-contract-tab" type="button" role="tab" aria-controls="c-overload-contract" aria-selected="false" tabindex="-1">Contract and build</button>
<button class="prik-example-tab" id="c-overload-python-tab" type="button" role="tab" aria-controls="c-overload-python" aria-selected="false" tabindex="-1">Python</button>
</div>

<div class="prik-example-panel" id="c-overload-source" role="tabpanel" aria-labelledby="c-overload-source-tab" tabindex="0" markdown="1">

Create `overloads.c`:

```c
int scale_integer(int value) { return value * 2; }

double scale_real(double value) { return value * 2.0; }
```

</div>

<div class="prik-example-panel" id="c-overload-contract" role="tabpanel" aria-labelledby="c-overload-contract-tab" tabindex="0" markdown="1">

Create `overloads.pyi`:

```python
from prik.contracts import Float64, Int32, overload, private

@private
def scale_integer(value: Int32) -> Int32: ...

@private
def scale_real(value: Float64) -> Float64: ...

@overload("scale_integer")
def scale(value: Int32) -> Int32: ...

@overload("scale_real")
def scale(value: Float64) -> Float64: ...
```

```bash
python3 -m prik --language c overloads.pyi \
  --native-c-sources overloads.c \
  --compiler cc \
  --out overloads \
  --out-dir build
```

</div>

<div class="prik-example-panel" id="c-overload-python" role="tabpanel" aria-labelledby="c-overload-python-tab" tabindex="0" markdown="1">

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import overloads

print(overloads.scale(np.int32(21)))
print(overloads.scale(np.float64(1.5)))
print([name for name in dir(overloads) if not name.startswith("_")])
```

```text
42
3.0
['scale']
```

</div>
</div>

Candidates must remain distinguishable by their supported dtype and rank.

## What is supported

- Externally linked functions with `void`, arithmetic scalars, and C99 complex
  values whose ABI the selected compiler can probe.
- One-level primitive pointer parameters, expressed as a scalar address,
  rank-zero NumPy storage, a projected result, or a C-contiguous NumPy array.
- Rank-zero C string inputs and storage, hidden outputs, status projection,
  symbol renaming, reordered arguments, typed literals, and derived lengths or
  shapes.
- `@nogil` calls that do not access Python state.
- Ordinary compiler preprocessing, including standard includes and macros.

## Qualifiers and compiler attributes

Use C qualifiers as constraints when authoring a contract: `const T *` must not
be presented as writable NumPy storage. `const` and `restrict` themselves do
not add a separate Python type or calling convention.

Common non-ABI attributes, such as `deprecated` and `warn_unused_result`, do
not change a wrapper. An attribute that may change the ABI, symbol identity, or
layout—such as a calling convention or alignment attribute—stops the build
instead of being ignored.

## Current limits

PRIK rejects these forms rather than guessing their ABI or memory contract:

- callbacks and function pointers; `struct`, `union`, and C global-state
  wrappers; and enum constants;
- variadic functions, `static` symbols, unsupported calling conventions,
  `volatile`, and `_Atomic` values;
- pointer results, multi-level pointers, raw or nullable pointers, and APIs
  with retained or ownership-sensitive pointers;
- arrays of strings, Boolean arrays, native C array declarators, arrays outside
  ranks 1–15, and Fortran-ordered C arrays.

For a feature-by-feature view, see the [language support
matrix](feature-matrix.md). The C parser can inspect a broader set of
declarations than this runtime lane; use its output to understand source, not
as a build promise.

## Build and inspect APIs

Use the CLI for normal builds and the Python API when the build belongs in an
application or test:

| Task | CLI | Python |
| --- | --- | --- |
| Build from C source | `python3 -m prik --language c api.c --out-dir build` | `build_c_extension("api.c", output_dir="build")` |
| Build an authored contract | `python3 -m prik --language c api.pyi --native-c-sources impl.c --out-dir build` | `build_pyi_extension("api.pyi", native_language="c", native_c_sources=["impl.c"], output_dir="build")` |
| Write a contract without compiling | `python3 -m prik generate --pyi --language c api.c --out api.pyi` | Use the generated `build/contracts/*.pyi` from a source build. |
| Write a reproducible Makefile | `python3 -m prik generate --makefile --language c api.c --out-dir build` | Pass `makefile=True` to either build function. |

The source-build equivalent of the first CLI route is:

```python
import numpy as np

from prik import build_c_extension

build = build_c_extension(
    "native_math.c",
    output_name="native_math",
    output_dir="build",
)
native_math = build.import_module()
print(native_math.add(np.float64(3.0), np.float64(2.5)))
```

`build.import_module()` imports the extension that was just built. Makefile
mode writes `build/Makefile.prik`; run it with `make -f build/Makefile.prik`.

### Native dependencies

Pass public C source files as positional inputs. Add implementation-only C
files with `--native-c-sources`, compiler flags with
`--native-c-compile-flags`, existing objects with `--native-objects`, and
libraries with `--native-library` and `--native-library-dir`. These complete
the native link without becoming Python API declarations.

For headers and conditional source, pass the same preprocessing information as
the native project: `-I`, `-D`, `--std`, and, when available,
`--compile-commands build/compile_commands.json`.

### Inspect a broader C API

The C parser and contract generator accept more syntax than the direct wrapper
lane. Use them to examine declarations, not as a promise that each declaration
can be built:

```bash
python3 -m prik parse --language c include/library.h --json
python3 -m prik semantics --language c include/library.h
python3 -m prik generate --pyi --language c include/library.h --out contracts/library.pyi
```

For a project header that needs its normal preprocessing configuration:

```bash
python3 -m prik parse --language c include/library.h \
  -I include \
  -D LIBRARY_ENABLE_FAST=1 \
  --std c11 \
  --compile-commands build/compile_commands.json
```

Only declarations in the wrapped translation unit become a source build's
public API; headers supply declarations and preprocessing context. See [CLI
Commands](../reference/cli-commands.md) for the complete build-option
reference. For the broader Fortran wrapper surface, start with the [User
Guide](../guide/index.md).

## What works today

| C surface | Python contract |
| --- | --- |
| Arithmetic scalar functions | Target-probed signed and unsigned integers, floating-point and C99 complex values, and `size_t`; exact NumPy scalar dtypes, `None` for `void`, and Python `bool` for C Boolean values. |
| One-level primitive pointers | A scalar address, rank-zero NumPy storage, a projected scalar result, or a C-contiguous primitive NumPy array. |
| Strings | `String` for a read-only `const char *`; rank-zero NumPy bytes storage for a writable `char *`. |
| C call reshaping | Exact symbol names, reordered or addressed arguments, typed literals, derived lengths and shapes, and hidden outputs. |
| C overloads | Several C symbols can appear under one Python name when dtype and rank distinguish them. |
| Status errors | `@raises` turns a hidden C `int` status and optional message into a Python exception. |
| Preprocessed source | Standard includes, macros, and conditional compilation supplied to the compiler. |
