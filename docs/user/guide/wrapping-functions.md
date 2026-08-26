---
title: Wrapping Functions
description: How PRIK wraps Fortran `function` procedures — return values, output arguments, arrays, and contracts
audience: users
prerequisites: data types, first wrapped function
related: wrapping-subroutines.md, arrays.md
status: maintained
publication: reviewed
---

# Wrapping Functions

A Fortran `function` becomes a Python callable. Its direct result is the first
Python return value. Other outputs follow only when their contract marks them
as Python results.

---

## Basic Scalar Function

The `scale` function built in
[First Wrapped Function](../getting-started/first-wrapped-function.md) returns
its direct `Float64` result as a NumPy `float64` scalar:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

---

## Python And Native Names

A contract declaration normally uses one name for both Python and the native
procedure. Use `@bind("native_name")` only when those names differ.

For example, rename the generated declaration to `multiply` and add
`@bind("scale")`. The Python name changes, while the native target remains
`scale`. The generated contract and its edited replacement are shown below.

The three views below describe that one rename.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Function rename example">
<button class="prik-example-tab" id="function-names-generated-contract-tab" type="button" role="tab" aria-controls="function-names-generated-contract" aria-selected="true">Generated contract</button>
<button class="prik-example-tab" id="function-names-edited-contract-tab" type="button" role="tab" aria-controls="function-names-edited-contract" aria-selected="false" tabindex="-1">Edited contract</button>
<button class="prik-example-tab" id="function-names-python-tab" type="button" role="tab" aria-controls="function-names-python" aria-selected="false" tabindex="-1">Python usage</button>
</div>

<div class="prik-example-panel" id="function-names-generated-contract" role="tabpanel" aria-labelledby="function-names-generated-contract-tab" tabindex="0" markdown="1">

### Generated contract

```python
from prik.contracts import Addr, Arg, Float64, native_call, standalone

@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def scale(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

Generate it:

```bash
python3 -m prik generate --pyi scale.f90 --out contracts/scale
```

</div>

<div class="prik-example-panel" id="function-names-edited-contract" role="tabpanel" aria-labelledby="function-names-edited-contract-tab" tabindex="0" markdown="1">

### Edited contract

```python
from prik.contracts import Addr, Arg, Float64, bind, native_call, standalone

@bind("scale")
@standalone
@native_call([Addr(Arg(0)), Addr(Arg(1))])
def multiply(
    value: Float64,
    factor: Float64
) -> Float64: ...
```

Build from the edited contract and native source:

```bash
python3 -m prik contracts/scale/__init__.pyi \
  --native-fortran-sources scale.f90 \
  --out-dir build/multiply
```

</div>

<div class="prik-example-panel" id="function-names-python" role="tabpanel" aria-labelledby="function-names-python-tab" tabindex="0" markdown="1">

### Python usage

```python
result = scale.multiply(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

</div>
</div>

Result:

```text
7.5
```

`@bind` changes the native target name. It does not change the argument
contract or adapt an incompatible native interface. Matching names need no
`@bind`.

If a package `__init__.pyi` re-exports the renamed declaration, update that
import too.

The same rule applies to functions, subroutines, and methods.

For the complete naming rules, see
[Add or Rename a Native Procedure](../reference/pyi-contracts/exports-and-modules.md#add-or-rename-a-native-procedure).

---

## Array Return Values

Functions can return arrays. An ordinary array result becomes a new NumPy
array in Fortran order, as described in
the [`automatic_vector` example](arrays.md#complete-example):

```python
import numpy as np

result = automatic_vector(np.int32(4))
print(result)  # [2. 4. 6. 8.]
```

---

## Functions with Output Arguments

When a function has projected scalar or native-created outputs, Python returns
a **tuple**:

> `(function_result, out_arg1, out_arg2, ...)`

Caller-provided ordinary arrays are mutated in place and are not added to this
tuple.

**Example:**

```fortran
function sum_with_count(values, count) result(total)
  real(8), intent(in) :: values(:)
  integer(4), intent(out) :: count
  real(8) :: total
  total = sum(values)
  count = size(values)
end function
```

**Python call:**

```python
total, count = sum_with_count(data_array)
```

---

## Important Rules

- Pass exact NumPy dtypes (`np.float64`, `np.int32`, etc.) for numeric scalar
  arguments. Boolean scalar arguments accept `bool` or `np.bool_`.
- Array results are returned as new NumPy arrays (copies).
- Projected scalar outputs follow the direct function result in the return
  tuple.
- Caller-provided arrays and derived objects mutate in place. They are not
  repeated in the return tuple.
- Without `intent`, an argument uses conservative `intent(inout)` behavior.
  Primitive scalar replacements follow the direct function result in the
  Python return tuple.

## Next

- [Wrapping Subroutines](wrapping-subroutines.md) for the complete argument
  projection rules.
