---
title: PRIK — Python Runtime Interop Kit
description: PRIK generates native Python bindings for Fortran and C code.
audience: users
prerequisites: none
related: user/getting-started/index.md, user/getting-started/installation.md, user/performance.md, developer/architecture.md
status: maintained
publication: reviewed
---

<p align="center">
  <img src="user/assets/prik-logo.png"
       alt="PRIK — Bring Native Code to Python"
       width="500">
</p>

**PRIK (Python Runtime Interop Kit)** generates native Python bindings for
Fortran and C code.

**Project status: Alpha.** Core Fortran workflows and the currently supported
C wrapper features are implemented and tested across supported compilers, but
public APIs may still change before `1.0`.

PRIK supports both languages. Fortran currently has the broader, more mature
wrapper surface. C currently supports a focused wrapper subset: primitive
values, one-level pointers, NumPy arrays, and strings. In both languages,
editable `.pyi` contracts let you shape the Python API. See [C
User Guide](user/guide/c/index.md) for C workflows and [C
Support](user/language-support/c-support.md) for current coverage.

---

<a id="see-it-in-action"></a>

## From Fortran to Python in one command

Install the package in a virtual environment:

```bash
python3 -m pip install prik
```

Create `scale.f90`:

<!-- prik-doc-source: tests/fortran/infrastructure/building/end_to_end/fixtures/native/scale.f90 -->
```fortran
real(8) function scale(value, factor) result(output)
  real(8), intent(in) :: value
  real(8), intent(in) :: factor
  output = value * factor
end function scale
```

Build an importable extension:

```bash
python3 -m prik scale.f90
```

Call the generated Python API:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

No manual binding code is required. PRIK derives the native wrapper and a
readable Python signature from the Fortran source.

## From C to Python in one command

Create `native_math.c`:

```c
double add(double left, double right) {
    return left + right;
}
```

Build an importable extension:

```bash
python3 -m prik --language c native_math.c \
  --compiler cc \
  --out native_math \
  --out-dir build
```

Call the generated Python API:

```python
import sys

import numpy as np

sys.path.insert(0, "build")
import native_math

print(native_math.add(np.float64(3.0), np.float64(2.5)))  # 5.5
```

This source build also writes an editable contract. For C pointers, arrays,
and authored contracts, see the [C User Guide](user/guide/c/index.md).

## Shape the Python API

For a richer API, PRIK lets you reshape the generated Python surface without
changing the native implementation. Switch tabs to compare the default and
edited versions.

The [`.pyi` Format](user/reference/pyi-format.md) defines the contract language;
[Editing `.pyi` Contracts](user/reference/pyi-contracts/index.md) shows the
supported transformations.

<div class="prik-example-tabs" data-prik-example-tabs markdown="1">
<div class="prik-example-tablist" role="tablist" aria-label="Home example">
<button class="prik-example-tab" id="home-source-tab" type="button" role="tab" aria-controls="home-source" aria-selected="true">Fortran source</button>
<button class="prik-example-tab" id="home-python-tab" type="button" role="tab" aria-controls="home-python" aria-selected="false" tabindex="-1">Default API</button>
<button class="prik-example-tab" id="home-contract-tab" type="button" role="tab" aria-controls="home-contract" aria-selected="false" tabindex="-1">Generated contract</button>
<button class="prik-example-tab" id="home-edited-contract-tab" type="button" role="tab" aria-controls="home-edited-contract" aria-selected="false" tabindex="-1">Edited .pyi</button>
<button class="prik-example-tab" id="home-edited-python-tab" type="button" role="tab" aria-controls="home-edited-python" aria-selected="false" tabindex="-1">Edited API</button>
</div>

<div class="prik-example-panel" id="home-source" role="tabpanel" aria-labelledby="home-source-tab" tabindex="0" markdown="1">

### Fortran source

Create `points.f90`:

```fortran
module points
  implicit none

  type :: point
    real(8) :: x = 0.0d0
    real(8) :: y = 0.0d0
  end type point

contains

  subroutine move(item, dx, dy)
    type(point), intent(inout) :: item
    real(8), intent(in) :: dx, dy
    item%x = item%x + dx
    item%y = item%y + dy
  end subroutine move

  real(8) function norm_squared(item) result(value)
    type(point), intent(in) :: item
    value = item%x * item%x + item%y * item%y
  end function norm_squared

end module points
```

Build:

```bash
python3 -m prik points.f90 --out geometry
```

</div>

<div class="prik-example-panel" id="home-python" role="tabpanel" aria-labelledby="home-python-tab" tabindex="0" markdown="1">

### Default API

```python
import numpy as np
import geometry.points as points

item = points.point(x=np.float64(3.0), y=np.float64(4.0))
points.move(item, np.float64(1.0), np.float64(-2.0))

print(item.x, item.y)             # 4.0 2.0
print(points.norm_squared(item))  # 20.0
```

</div>

<div class="prik-example-panel" id="home-contract" role="tabpanel" aria-labelledby="home-contract-tab" tabindex="0" markdown="1">

### Generated contract

The generated `points.pyi` is:

```python
from prik.contracts import Addr, Arg, Float64, native_call

class point:
    x: Float64 = 0.0
    y: Float64 = 0.0

    def __init__(self, *, x: Float64 = 0.0, y: Float64 = 0.0) -> None: ...

@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])
def move(item: point, dx: Float64, dy: Float64) -> None: ...

def norm_squared(item: point) -> Float64: ...
```

Generate it:

```bash
python3 -m prik generate --pyi points.f90 --out contracts
```

</div>

<div class="prik-example-panel" id="home-edited-contract" role="tabpanel" aria-labelledby="home-edited-contract-tab" tabindex="0" markdown="1">

### Edited `.pyi`

The edited `points.pyi` is:

```python
from prik.contracts import Addr, Arg, Float64, Pass, bind, native_call

class point:
    x: Float64 = 0.0
    y: Float64 = 0.0

    def __init__(self, *, x: Float64 = 0.0, y: Float64 = 0.0) -> None: ...

    @bind("move")
    @native_call([Pass(), Addr(Arg(0)), Addr(Arg(1))])
    def translate(self, dx: Float64, dy: Float64) -> None: ...

    @native_call([Pass()])
    def norm_squared(self) -> Float64: ...
```

`@bind("move")` maps the Python-facing `translate` method to the native
`move` procedure. `norm_squared` needs no `@bind` because its Python and
native names already match. `Pass()` supplies the receiver (`self`) to the
native call; `Addr(Arg(...))` passes the remaining arguments by address as
required by the native calling convention.

Build from the contract:

```bash
python3 -m prik contracts/__init__.pyi \
  --native-fortran-sources points.f90 \
  --out geometry
```

</div>

<div class="prik-example-panel" id="home-edited-python" role="tabpanel" aria-labelledby="home-edited-python-tab" tabindex="0" markdown="1">

### Edited Python API

The native Fortran is unchanged, but the Python surface is now:

```python
import numpy as np
import geometry.points as points

item = points.point(x=np.float64(3.0), y=np.float64(4.0))
item.translate(np.float64(1.0), np.float64(-2.0))

print(item.x, item.y)       # 4.0 2.0
print(item.norm_squared())  # 20.0
```

</div>
</div>

Same Fortran source, but a more natural Python API: module procedures become methods.

**Want to run that loop yourself?** The quickstart notebook does exactly this —
compiles a Fortran cell and a C cell, then reshapes the generated API by editing
its `.pyi` contract. It needs no installation.

<p class="prik-notebook-actions">
<a class="prik-primary-cta" href="https://colab.research.google.com/github/PyNumLab/prik/blob/main/examples/notebooks/quickstart.ipynb">▶&nbsp; Run it in Colab</a>
<a class="prik-secondary-cta" href="examples/notebooks/quickstart.ipynb" download="quickstart.ipynb">⬇&nbsp; Download the notebook</a>
</p>

## Why PRIK

- **Natural Python APIs:** Fortran modules become namespaces and derived types
  become classes.
- **Editable contracts:** generated `.pyi` files let you rename, hide, flatten,
  or reorganize the public API.
- **Explicit native behavior:** NumPy dtypes, array layouts, ownership, and
  lifetimes are checked at the boundary.
- **Clear limits:** unsupported contracts fail before wrapper generation with
  actionable diagnostics.

## Proven on real libraries

The maintained example suite covers five Fortran libraries—
[BLAS](user/examples/fortran/blas-wrapper.md),
[LAPACK](user/examples/fortran/lapack-wrapper.md),
[FFTPACK](user/examples/fortran/fftpack-wrapper.md),
[MINPACK](user/examples/fortran/minpack-wrapper.md), and
[BSPLINE-FORTRAN](user/examples/fortran/bspline-wrapper.md)—and two C
libraries: [libm](user/examples/c/libm-wrapper.md) and
[TA-Lib](user/examples/c/ta-lib-wrapper.md). Each project has a complete build
and numerical validation workflow, including its tested platforms and
toolchains, in the [Examples Gallery](user/examples/index.md).

## Measured against NumPy's f2py

The reproducible [performance comparison](user/performance.md) measures PRIK
and NumPy's f2py against the same Fortran kernels on the same machine. The
charts show the current published snapshot. Results are specific to its
machine and toolchain, which are documented with the full results.

**Runtime-call performance** — values above `1.0×` favor PRIK.

[![Relative runtime performance of PRIK and f2py across call, vector, and matrix workloads. Values above 1.0 mean PRIK is faster.](user/assets/performance-comparison.svg)](user/performance.md)
{ .prik-performance-chart }

The chart shows `f2py time ÷ PRIK time`: values above `1.0×` favor PRIK and
values below `1.0×` favor f2py.

**Clean end-to-end build time** — lower times are better.

[![Clean end-to-end build time for PRIK and f2py under development and optimized compiler profiles. Lower times are better.](user/assets/build-time-comparison.svg)](user/performance.md#clean-build-time)
{ .prik-performance-chart }

[See the benchmark machine, full results, and methodology →](user/performance.md)

**Ready to wrap your Fortran project?**

[Install PRIK →](user/getting-started/installation.md){ .prik-primary-cta }
[Read Getting Started →](user/getting-started/index.md){ .prik-primary-cta }

**Wrapping a supported C API?**

[Read the C User Guide →](user/guide/c/index.md){ .prik-primary-cta }

**Working on PRIK itself?**

[Read Developer Documentation →](developer/index.md){ .prik-primary-cta }
