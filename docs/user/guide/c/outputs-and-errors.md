---
title: C Outputs and Errors
description: Return C output parameters and project native status values into Python errors
audience: users
prerequisites: C pointers, arrays, and strings
related: pointers-arrays-and-strings.md, symbols-headers-and-dependencies.md, ../../reference/pyi-contracts/calls-and-results.md, ../error-handling.md
status: maintained
publication: reviewed
---

# C Outputs and Errors

An authored contract decides which C pointer parameters are visible Python
arguments, returned values, or native-only status storage.

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

See [Calls and Results](../../reference/pyi-contracts/calls-and-results.md) for
the complete shared contract vocabulary.

## Hide native outputs and raise Python exceptions

Use `Hidden(name, T)` for C output storage that Python should not return. A
common case is a status value and diagnostic message consumed by `@raises`.

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

The function returns only `root`; `status` and `message` produce a
`RuntimeError` on failure. A hidden message needs a fixed capacity because
PRIK allocates its native storage.

A caller-owned visible message buffer uses rank-zero NumPy storage:

```python
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Arg(1), Hidden("status", Int32)])
def checked(value: Float64, message: String[64][()]) -> None: ...
```

The caller can inspect the `S64` array after the call or exception.

## Next

Continue with [Symbols, Headers, and
Dependencies](symbols-headers-and-dependencies.md) for larger native APIs and
libraries.
