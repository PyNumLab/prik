---
title: Optional Arguments
description: How PRIK handles Fortran `optional` arguments — inputs, outputs, arrays, and None behavior
audience: users
prerequisites: wrapping subroutines, data types
related: generic-interfaces.md, arrays.md, error-handling.md
status: maintained
publication: reviewed
---

# Optional Arguments

PRIK supports optional scalars, arrays, strings, derived types, and outputs.
It preserves native `present(...)` semantics.

---

## Complete Example

The source, generated contract, and Python call describe the same optional
input behavior. The result stays visible below the three views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Optional arguments example">
<button class="prik-example-tab" id="optional-arguments-source-tab" type="button" role="tab" aria-controls="optional-arguments-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="optional-arguments-contract-tab" type="button" role="tab" aria-controls="optional-arguments-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="optional-arguments-python-tab" type="button" role="tab" aria-controls="optional-arguments-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="optional-arguments-source" role="tabpanel" aria-labelledby="optional-arguments-source-tab" tabindex="0" markdown="1">

### Fortran source

Create `optional.f90`:

```fortran
module adjustments
  implicit none
contains

  integer(4) function adjust(value, offset) result(output)
    integer(4), intent(in) :: value
    integer(4), intent(in), optional :: offset

    output = value
    if (present(offset)) output = output + offset
  end function adjust

  subroutine make_values(size, count, values)
    integer(4), intent(in) :: size
    integer(4), intent(out) :: count
    real(8), intent(out), optional :: values(size)
    integer(4) :: index

    count = size
    if (present(values)) then
      do index = 1, size
        values(index) = real(index, 8)
      end do
    end if
  end subroutine make_values

end module adjustments
```

Build it:

```bash
python3 -m prik optional.f90 --out-dir build/optional
```

</div>

<div class="prik-example-panel" id="optional-arguments-contract" role="tabpanel" aria-labelledby="optional-arguments-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `adjustments.pyi` is:

```python
from prik.contracts import Addr, Arg, Float64, Int32, Return, native_call

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def adjust(
    value: Int32,
    offset: Int32 = ...
) -> Int32: ...

@native_call([Addr(Arg(0)), Return('count', 0), Arg(1)])
def make_values(
    size: Int32,
    values: Float64[size] = ...
) -> Int32: ...
```

Generate it:

```bash
python3 -m prik generate --pyi optional.f90
```

</div>

<div class="prik-example-panel" id="optional-arguments-python" role="tabpanel" aria-labelledby="optional-arguments-python-tab" tabindex="0" markdown="1">

## Usage in Python

```python
import sys
import numpy as np

sys.path.insert(0, "build/optional")
from optional.adjustments import adjust, make_values

print(adjust(np.int32(5)))                         # 5 (omitted)
print(adjust(np.int32(5), None))                   # 5 (explicit None)
print(adjust(np.int32(5), np.int32(3)))            # 8 (provided)
print(adjust(np.int32(5), offset=np.int32(10)))    # 15 (keyword)
```

</div>
</div>

Result:

```text
5
5
8
15
```

## Key Rules

- For ordinary optional inputs, **omission** and `None` both mean the argument
  is **not present** to Fortran.
- Providing a concrete value makes the argument **present**.
- Use **keyword arguments** when skipping earlier optional parameters.
- Optional arrays and derived types also accept `None` to indicate absence.
- Optional `intent(out)` / `intent(inout)` arguments remain visible in Python
  so you can control `present(...)`.
- An optional argument without `intent` uses the same conservative
  `intent(inout)` behavior when present.

### Scalar Allocatables And Pointers

For an optional scalar allocatable or pointer, omission and `None` have
different meanings:

| Python call | What Fortran receives |
| --- | --- |
| `func()` | The argument is absent: `present(value)` is false. |
| `func(None)` | The argument is present but unallocated or unassociated. |
| `func(value)` | The argument is present with `value`. |

This is the only scalar optional case where explicit `None` does not mean
absence. The scalar crosses the call as a value, not as a persistent handle.

---

## Optional Outputs

An optional ordinary output remains visible in the Python call. This lets the
caller decide whether the native routine receives it.

Pass writable storage to make `values` present:

```python
values = np.empty(3, dtype=np.float64)
count = make_values(np.int32(3), values)

print(count)   # 3
print(values)  # [1. 2. 3.]
```

Omit the argument, or pass `None`, to make it absent:

```python
omitted_count = make_values(np.int32(3))
none_count = make_values(np.int32(3), None)

print(omitted_count)  # 3
print(none_count)     # 3
```

`count` is a required scalar output, so it is always returned. `values` is
caller-owned mutable storage, so it is never added to the result.

For optional ordinary array outputs:

- Supplying writable storage mutates that array in place.
- Passing `None` or omitting it makes the native dummy absent.
- Presence does not add an array-or-`None` position to the result.
- A routine with only optional ordinary array outputs returns `None`, whether
  those arrays are present or absent.

Optional scalar derived-type outputs follow the same in-place rule as arrays.
For an optional scalar allocatable or pointer output, omit the argument to make
it absent. Pass `None` to make it present without an initial allocation or
association. If its updated value is returned, Python receives a scalar or
`None`, not a handle.

---

## Limitations

- Optional procedure pointers and passed procedures are not yet supported.
- PRIK does not invent default values. The Fortran procedure handles missing
  arguments.

---

## Next

- Continue with [Generic Interfaces](generic-interfaces.md).
- For optional outputs and memory, see [Error Handling](error-handling.md) and
  [Memory Management](memory-management.md).
