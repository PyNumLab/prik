---
title: Enumerations
description: How PRIK handles Fortran `enum` and enumerators
audience: users
prerequisites: wrapping modules, data types
related: wrapping-modules.md, generic-interfaces.md
status: maintained
publication: reviewed
---

# Enumerations

PRIK turns supported Fortran `enum` declarations into **typed integer constants**. It does **not** generate Python `Enum` or `IntEnum` classes — values remain plain integers with the resolved dtype.

---

## Complete Example

The source, generated contract, and Python call describe the same module. The
result stays visible below the three views.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Enumerations example">
<button class="prik-example-tab" id="enumerations-source-tab" type="button" role="tab" aria-controls="enumerations-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="enumerations-contract-tab" type="button" role="tab" aria-controls="enumerations-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="enumerations-python-tab" type="button" role="tab" aria-controls="enumerations-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="enumerations-source" role="tabpanel" aria-labelledby="enumerations-source-tab" tabindex="0" markdown="1">

### Fortran source

Create `colors.f90`:

```fortran
module colors_api
  implicit none

  enum, bind(C)
    enumerator :: red = -1
    enumerator :: blue
    enumerator :: green = 10
    enumerator :: yellow
  end enum

contains

  integer(4) function round_trip_color(value) result(output)
    integer(4), intent(in) :: value
    output = value
  end function round_trip_color

end module colors_api
```

Build it:

```bash
python3 -m prik colors.f90 --out-dir build/colors
```

</div>

<div class="prik-example-panel" id="enumerations-contract" role="tabpanel" aria-labelledby="enumerations-contract-tab" tabindex="0" markdown="1">

## Generated Contract

The generated `colors_api.pyi` is:

```python
from prik.contracts import Addr, Arg, Final, Int32, native_call

red: Final[Int32] = -1

blue: Final[Int32] = 0

green: Final[Int32] = 10

yellow: Final[Int32] = 11

@native_call([Addr(Arg(0))])
def round_trip_color(
    value: Int32
) -> Int32: ...
```

Generate it:

```bash
python3 -m prik generate --pyi colors.f90
```

</div>

<div class="prik-example-panel" id="enumerations-python" role="tabpanel" aria-labelledby="enumerations-python-tab" tabindex="0" markdown="1">

## Usage in Python

```python
import sys

sys.path.insert(0, "build/colors")
from colors.colors_api import blue, green, red, round_trip_color, yellow

print(red, blue, green, yellow)  # -1 0 10 11

# Pass enumerator values to procedures
result = round_trip_color(green)
print(result)                    # 10
```

</div>
</div>

Result:

```text
-1 0 10 11
10
```

## Key Points

- Enumerators become module constants declared with `Final[...]` in the
  generated semantic `.pyi`; the native enumerator value cannot change.
- They use the resolved integer dtype (usually `Int32`).
- Rebinding an imported name in Python only creates a local shadow — it does
  **not** change the native value.
- No automatic runtime validation — passing any integer of the correct dtype works.
- Static type checkers see them as integer constants.

---

## Limitations

- No native `Enum` class is generated in Python.
- If you want a proper Python `Enum`, define one in your application code and pass `.value` (as `np.int32`).

---

## Next

- Continue with [Raw Addresses](raw-addresses.md).
