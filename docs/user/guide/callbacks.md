---
title: Callbacks
description: How to pass Python callables to Fortran as callbacks with x2py
audience: advanced users
prerequisites: wrapping functions, data types
related: error-handling.md, memory-management.md
status: maintained
publication: reviewed
---

# Callbacks

Callbacks let wrapped Fortran call a Python function while an x2py call is
running. They are useful for objective functions, progress hooks, custom
transforms, and small pieces of user-defined numerical logic.

Declare the callback shape once with `@prototype`, then use that prototype name
as the type of the procedure argument that accepts the callback.

---

## The Short Version

| Native callback argument | Prototype spelling | Python callable receives |
| --- | --- | --- |
| Primitive scalar dummy declared with Fortran `value` | `value: Float64` | Independent `np.float64` scalar |
| Primitive scalar reference dummy | `value: Addr(Float64)` | Independent `np.float64` scalar |
| Array reference dummy | `values: Float64[n]` | NumPy array view |
| Fixed-length string reference dummy | `label: String[8]` | Writable rank-zero bytes storage |
| Derived-type reference dummy | `point: point_t` | Generated wrapper object |

!!! tip "Rule of thumb"
    Bare primitive callback arguments are native values:
    `value: Float64`, `count: Int32`, and so on.

    Use `Addr(T)` only when a primitive callback dummy is passed by reference.

Arrays, strings, and derived-type callback arguments already use native storage
or wrapper objects, so they do not need `Addr(...)` for ordinary reference
dummies. Use `Value(point_t)` only for a supported derived-type callback dummy
declared with the Fortran `value` attribute.

---

## What The Callable Sees

Two declarations can appear around callbacks, and they control different calls:

| Declaration | Controls |
| --- | --- |
| `@prototype` | How Fortran calls the callback adapter. |
| `@native_call(...)` | How Python arguments are passed into the outer wrapped function. |

For example, the wrapped function may need `@native_call([Addr(Arg(1))])`
because its `value` argument is passed to Fortran by reference:

```python
from x2py.contracts import Addr, Arg, Float64, native_call, prototype

@prototype
def scalar_callback(value: Addr(Float64)) -> Float64: ...

@native_call([Arg(0), Addr(Arg(1))])
def apply(callback: scalar_callback, value: Float64) -> Float64: ...
```

The two `Addr(...)` markers belong to different boundaries. The one inside
`@prototype` describes how Fortran calls the callback. The one inside
`@native_call(...)` describes how Python calls the wrapped function.

At runtime, pass an ordinary Python callable:

```python
import numpy as np

api.apply(lambda value: np.float64(3.0 * value), np.float64(2.5))
```

The lambda receives converted Python objects, not `Addr(...)` markers.

---

## Small Example

Create `callbacks.f90`:

```fortran
module callbacks_api
  implicit none

  abstract interface
    real(8) function scalar_callback(value) result(output)
      real(8), intent(in) :: value
    end function scalar_callback
  end interface

contains

  real(8) function apply(callback, value) result(output)
    procedure(scalar_callback) :: callback
    real(8), intent(in) :: value
    output = callback(value)
  end function apply

end module callbacks_api
```

Build it:

```bash
python3 -m x2py callbacks.f90 --out-dir build/callbacks
```

**Python usage:**

```python
import sys

import numpy as np

sys.path.insert(0, "build/callbacks")
from callbacks.callbacks_api import apply

result = apply(
    lambda value: np.float64(3.0 * value),
    np.float64(2.5)
)
print(result)  # 7.5
```

---

## Choosing The Prototype Spelling

Prototype declarations describe the **native callback signature**. They are not
Python runtime functions and they are not exported from the generated module.

For ordinary scalar and array callback arguments, use the same contract spellings
you use elsewhere:

```python
from x2py.contracts import Addr, Float64, Int32, prototype

@prototype
def update_values(
    count: Addr(Int32),
    scale: Float64,
    values: Float64[count]
) -> None: ...
```

Here `count` is a primitive reference dummy, while `scale` is a primitive value
dummy. Python receives both as NumPy scalar values.

For scalar arguments, choose the spelling from the Fortran callback dummy:

| Fortran callback dummy | Matching prototype |
| --- | --- |
| `real(8), intent(in) :: value` | `value: Addr(Float64)` |
| `real(8), value :: value` | `value: Float64` |

Both forms call Python with an independent `np.float64` scalar. The difference
is the native calling convention x2py must match.

`Value(T)` is only for supported non-primitive scalar value dummies, such as a
derived-type callback dummy declared with the Fortran `value` attribute.

---

## Key Rules

- The callback is only valid **during** the wrapped native call.
- Native code must not store the callback for later use.
- Return the exact NumPy scalar type when x2py expects a scalar callback result.
- Primitive scalar callback arguments arrive as independent NumPy scalar values,
  whether the native dummy is `value` or reference.
- Primitive scalar reference writeback is unsupported; return a scalar result
  instead.
- Arrays and derived-type arguments can expose live native state; copy data you
  need after the wrapped call returns.

---

## Important Limitations

Supported callbacks are immediate, same-thread adapters. The native routine may
call the Python callable while the wrapped call is active, and x2py tears down
the callback context when that wrapped call returns.

The current callback contract does not support:

- Stored callbacks, persistent callbacks, procedure pointers, or callbacks
  invoked after the wrapped call returns. Pass the callable into each wrapped
  call that needs it.
- Optional callback procedure arguments. Expose a separate native entry point
  for the no-callback path, or require the callback argument.
- Optional arguments inside a `@prototype`. Pass an explicit value, sentinel, or
  presence flag instead.
- Allocatable, pointer, polymorphic, or assumed-type callback arguments and
  results. Use plain scalars, fixed-shape primitive arrays, fixed-length strings,
  or supported scalar derived types.
- Arrays passed by Fortran `value`, arrays of derived values, and array callback
  results without a complete fixed shape. Pass arrays by reference and give array
  results an exact primitive shape.
- Variable-length callback strings. Use a fixed positive `String[n]` length.
- Callback execution on a different Python thread. The callback must run on the
  same thread that entered the wrapper.

Callback exceptions and invalid return conversions are fatal at the callback
boundary: x2py prints the Python traceback and aborts the host process.

---

## Next

- Continue with [Enumerations](enumerations.md).
- Review [Error Handling](error-handling.md) when callback failure behavior matters.
