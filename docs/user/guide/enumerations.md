---
title: Enumerations
description: How x2py handles Fortran `enum` and enumerators
audience: users
prerequisites: wrapping modules, data types
related: wrapping-modules.md, generic-interfaces.md, ../language-support/feature-matrix.md
status: maintained
publication: reviewed
---

# Enumerations

x2py turns supported Fortran `enum` declarations into **typed integer constants**. It does **not** generate Python `Enum` or `IntEnum` classes — values remain plain integers with the resolved dtype.

---

## Complete Example

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
python3 -m x2py colors.f90 --out-dir build/colors
```

---

## Usage in Python

```python
import sys
import numpy as np

sys.path.insert(0, "build/colors")
import colors

api = colors.colors_api

assert api.red == np.int32(-1)
assert api.blue == np.int32(0)
assert api.green == np.int32(10)
assert api.yellow == np.int32(11)

# Pass enumerator values to procedures
result = api.round_trip_color(api.green)
assert result == np.int32(10)
```

---

## Key Points

- Enumerators become **read-only** constants on the module.
- They use the resolved integer dtype (usually `Int32`).
- Assigning to them in Python only creates a local shadow — it does **not** change the native value.
- No automatic runtime validation — passing any integer of the correct dtype works.
- Static type checkers see them as integer constants.

---

## Limitations

- No native `Enum` class is generated in Python.
- If you want a proper Python `Enum`, define one in your application code and pass `.value` (as `np.int32`).

---

## Next

- Continue with [Callbacks](callbacks.md).
- Check the [Language Feature Matrix](../language-support/feature-matrix.md) for current enum support.
