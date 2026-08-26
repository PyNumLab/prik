---
title: Wrapping Subroutines
description: How PRIK wraps Fortran `subroutine` procedures — output arguments, in-place mutation, and result projection
audience: users
prerequisites: data types, first wrapped function
related: wrapping-functions.md, arrays.md, optional-arguments.md
status: maintained
publication: reviewed
---

# Wrapping Subroutines

A Fortran `subroutine` has no direct return value. Scalar outputs and objects
created by Fortran form the Python result. Caller-provided mutable objects
change in place.

---

## How Arguments Become Python Results

| Native Argument              | Python Call                  | Python Result                     |
|-----------------------------|------------------------------|-----------------------------------|
| `intent(in)` scalar/array   | Visible argument             | Not returned                      |
| `intent(out)` scalar        | Hidden                       | Returned as value                 |
| `intent(inout)` scalar      | Visible argument             | Returned as replacement value     |
| `intent(out)` array         | Visible writable NumPy array | Filled in place; not returned     |
| `intent(inout)` array       | Visible writable NumPy array | Mutated in place; not returned    |
| Derived `intent(out/inout)` | Visible generated object     | Mutated in place; not returned    |
| `intent(out)` allocatable   | Hidden (or optional)         | `Allocatable[...]` handle         |
| No `intent`                 | Visible argument             | Conservative `intent(inout)` rule |
| No `intent`, assumed input  | Visible argument             | Not returned (opt-in, see below)  |

Without `intent`, PRIK uses the conservative `intent(inout)` behavior. A
scalar stays visible and its replacement value is returned — `character`
scalars included, on the same terms as numeric ones. This is common in legacy
sources, but the rule applies to any dummy declaration without `intent`.

Two ways to drop a result you know the native procedure never writes:

- remove that projected result from the generated contract, one dummy at a
  time; or
- pass `--assume-intent-in-scalars`, which applies the same choice to every
  scalar in the build that declares no `intent`.

### `--assume-intent-in-scalars`

`intent` did not exist before Fortran 90, so a fixed-form source cannot declare
it and its absence carries no information about the procedure. This option lets
you say so:

```bash
python3 -m prik ddot.f --out blas --assume-intent-in-scalars
```

```python
# default                      ddot(...) -> tuple[float64, int32, int32, int32]
# --assume-intent-in-scalars   ddot(...) -> float64
```

The option is an assertion you make about the source, not a fact PRIK derives
from it. PRIK does not inspect the procedure body, so a procedure that *does*
write such a dummy silently loses that value, exactly as it would if you
removed the result from the contract by hand. Use it on sources whose scalar
arguments are known controls; leave it off when you are not sure.

It is deliberately narrow:

| Declaration | Effect |
| --- | --- |
| Primitive scalar with no `intent` | Treated as `intent(in)`; not returned |
| `character` scalar with no `intent` | Treated as `intent(in)`; not returned |
| Any declared `intent` | Unchanged — a declared `intent` always wins |
| Array with no `intent` | Unchanged — still mutated in place, never returned |
| Derived-type object with no `intent` | Unchanged — still mutated in place |
| Allocatable or pointer scalar with no `intent` | Unchanged — its result is a nullable snapshot, not a replacement |

Every command that produces semantic IR accepts the option — the build,
`generate --pyi`, and `semantics` — because it changes how a missing `intent`
is read rather than how the wrapper is emitted. A contract generated with the
option and a direct build with the option therefore describe the same Python
surface. A `.pyi` wrapper build rejects it: a contract already states its own
results, so edit the contract there instead.

---

## Complete Example

The source, generated contract, and Python call describe the same output
rules. The result stays visible below the three views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Subroutine example">
<button class="prik-example-tab" id="subroutines-source-tab" type="button" role="tab" aria-controls="subroutines-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="subroutines-contract-tab" type="button" role="tab" aria-controls="subroutines-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="subroutines-python-tab" type="button" role="tab" aria-controls="subroutines-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="subroutines-source" role="tabpanel" aria-labelledby="subroutines-source-tab" tabindex="0" markdown="1">

### Fortran source

Create `outputs.f90`:

```fortran
module outputs
  implicit none
contains

  subroutine bounds(values, smallest, largest)
    real(8), intent(in) :: values(:)
    real(8), intent(out) :: smallest, largest
    smallest = minval(values)
    largest = maxval(values)
  end subroutine bounds

  subroutine scale_in_place(values, factor)
    real(8), intent(inout) :: values(:)
    real(8), intent(in) :: factor
    values = factor * values
  end subroutine scale_in_place

  subroutine scale_scalar(value, factor)
    real(8), intent(inout) :: value
    real(8), intent(in) :: factor
    value = factor * value
  end subroutine scale_scalar

  subroutine fill(values)
    real(8), intent(out) :: values(:)
    values = 1.0_8
  end subroutine fill

end module outputs
```

Build it:

```bash
python3 -m prik outputs.f90 --out-dir build/outputs
```

</div>

<div class="prik-example-panel" id="subroutines-contract" role="tabpanel" aria-labelledby="subroutines-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `outputs.pyi` is:

```python
from prik.contracts import Addr, Arg, Float64, Return, Returns, native_call

@native_call([Arg(0), Return('smallest', 0), Return('largest', 1)])
def bounds(
    values: Float64[::]
) -> tuple[Float64, Float64]: ...

@native_call([Arg(0), Addr(Arg(1))])
def scale_in_place(
    values: Float64[::],
    factor: Float64
) -> None: ...

@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale_scalar(
    value: Float64,
    factor: Float64
) -> Returns["value", Float64]: ...

def fill(
    values: Float64[::]
) -> None: ...
```

Generate it:

```bash
python3 -m prik generate --pyi outputs.f90
```

</div>

<div class="prik-example-panel" id="subroutines-python" role="tabpanel" aria-labelledby="subroutines-python-tab" tabindex="0" markdown="1">

## Python Usage

```python
import sys

import numpy as np

sys.path.insert(0, "build/outputs")
from outputs.outputs import bounds, fill, scale_in_place, scale_scalar

# Hidden scalar outputs → returned as tuple
data = np.array([4.0, -2.0, 7.0], dtype=np.float64)
smallest, largest = bounds(data)
print(smallest, largest)   # -2.0  7.0

# Scalar inout replacement
updated = scale_scalar(np.float64(4.0), np.float64(2.5))
print(updated)              # 10.0

# In-place mutation
arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
scale_in_place(arr, np.float64(3.0))
print(arr)                 # [3. 6. 9.]

# Caller-provided output array
target = np.empty(4, dtype=np.float64)
fill(target)
print(target)              # [1. 1. 1. 1.]
```

</div>
</div>

Result:

```text
-2.0 7.0
10.0
[3. 6. 9.]
[1. 1. 1. 1.]
```

## Key Rules

- Scalar `intent(out)` values are hidden in the call and returned.
- Scalar `intent(inout)` values are visible inputs and are also returned as
  replacement values; the original Python scalar object is unchanged.
- Array `intent(out/inout)` arguments must be pre-allocated by the caller and
  are mutated in place.
- Ordinary `intent(out/inout)` arrays are not added to the Python result.
- Scalar derived-type objects follow the same in-place rule as arrays.
- Array function results and hidden allocatable outputs still return new
  Python-visible objects because the caller did not supply their storage.
- The generated `.pyi` contract is the source of truth for what is returned.
- For functions with both a return value **and** outputs, the function result comes first in the tuple.

---

## Next

- Continue with [Wrapping Modules](wrapping-modules.md).
- Then read [Optional Arguments](optional-arguments.md) to control whether a
  native argument is present.
- For advanced memory management, see [Allocatables](allocatables.md) and [Pointers](pointers.md).
