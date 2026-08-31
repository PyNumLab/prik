---
title: Run PRIK in a Notebook
description: Compile Fortran and C cells and reshape the generated API without leaving the notebook
audience: users
prerequisites: installation, IPython and Jupyter notebooks
related: ../guide/notebooks.md, ../guide/c/pointers-arrays-and-strings.md, pythonic-blas.md
status: maintained
publication: reviewed
---

# Run PRIK in a Notebook

This tutorial compiles Fortran and C in notebook cells, calls them from Python,
and then reshapes the generated API by editing its semantic contract — all in
one session.

<p class="prik-notebook-actions">
<a class="prik-primary-cta" href="https://colab.research.google.com/github/PyNumLab/prik/blob/main/examples/notebooks/quickstart.ipynb">▶&nbsp; Run it in Colab</a>
<a class="prik-secondary-cta" href="../../../examples/notebooks/quickstart.ipynb" download="quickstart.ipynb">⬇&nbsp; Download the notebook</a>
</p>

The notebook runs top to bottom and builds real extension modules, so it needs a
compiler. In Colab the first cell installs one, along with PRIK:

```bash
pip install "prik[jupyter]"
```

## 1. Load the extension

```ipython
%load_ext prik.jupyter
```

## 2. Compile a Fortran cell

`%%fortran` compiles the cell and publishes what it declares. A Fortran module
becomes a notebook name:

```ipython
%%fortran
module geometry
contains
    real(8) function circle_area(radius)
        real(8), intent(in) :: radius
        circle_area = 3.141592653589793d0 * radius**2
    end function
end module
```

```python
area = geometry.circle_area(np.float64(2.0))
assert np.isclose(area, np.pi * 4)
print(f"✅ circle_area(2.0) = {area}  (expected {np.pi * 4})")
```

```text
✅ circle_area(2.0) = 12.566370614359172  (expected 12.566370614359172)
```

Every result the notebook claims is asserted, so a ✅ means the cell really did
that rather than the page saying so.

## 3. Compile a C cell

`%%c` publishes C functions directly. This one doubles an array in place and
takes the element count the way C usually does:

```ipython
%%c
#include <stddef.h>

void scale(size_t count, double *values) {
    for (size_t index = 0; index < count; ++index) {
        values[index] *= 2.0;
    }
}
```

`double *values` becomes runtime-rank storage, so it accepts a NumPy array of
any rank and writes through it. The count still has to be passed by hand,
though NumPy already knows it:

```python
values = np.array([1.0, 2.0, 3.0])
scale(np.uintp(values.size), values)
assert np.allclose(values, [2.0, 4.0, 6.0])
print(f"✅ scale(count, values) doubled in place: {values}  (expected [2. 4. 6.])")
```

```text
✅ scale(count, values) doubled in place: [2. 4. 6.]  (expected [2. 4. 6.])
```

## 4. Reshape the API with a contract

`--pyi` compiles nothing. It keeps the source and hands back the semantic
contract it derived, as an editable cell:

```ipython
%%c --pyi
#include <stddef.h>

void scale(size_t count, double *values) {
    for (size_t index = 0; index < count; ++index) {
        values[index] *= 2.0;
    }
}
```

Jupyter and Colab insert the contract below the cell you just ran:

```ipython
%%pyi

# prik: source-sha256=<generated digest>

from prik.contracts import Float64, UInt64

def scale(
    count: UInt64,
    values: Float64[...]
) -> None: ...
```

Edit it so the count comes from the array. `Arg(0).size` supplies it, and
`Float64[:]` pins the rank to one. Keep the `# prik:` line, then run the cell:

```ipython
%%pyi

# prik: source-sha256=<generated digest>

from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).size, Arg(0)])
def scale(values: Float64[:]) -> None: ...
```

Same C code, same compiler; only the Python API changed — `count` is gone:

```python
values = np.array([1.0, 2.0, 3.0])
scale(values)
assert np.allclose(values, [2.0, 4.0, 6.0])
print(f"✅ scale(values) doubled in place: {values}  (expected [2. 4. 6.])")
```

```text
✅ scale(values) doubled in place: [2. 4. 6.]  (expected [2. 4. 6.])
```

## Where to go next

- [IPython and Jupyter Notebooks](../guide/notebooks.md) covers every magic,
  its options, and the cell cache.
- [C Pointers, Arrays, and Strings](../guide/c/pointers-arrays-and-strings.md)
  explains what `Float64[...]` accepts and how to narrow it.
- [Design a Pythonic BLAS API](pythonic-blas.md) applies the same contract
  editing to a real library.
