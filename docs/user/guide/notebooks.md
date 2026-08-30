---
title: IPython and Jupyter Notebooks
description: Compile Fortran and C cells with PRIK cell magics
audience: users
prerequisites: installation, first wrapped module, C support
related: wrapping-modules.md, ../reference/python-api.md, ../language-support/c-support.md
status: maintained
publication: reviewed
---

# IPython and Jupyter Notebooks

PRIK provides optional `%%fortran`, `%%c`, and `%%pyi` cell magics for compiling
Fortran and C code inside IPython or a Jupyter notebook. Install the notebook
dependency and load the extension once per session:

```bash
python3 -m pip install "prik[jupyter]"
```

```ipython
%load_ext prik.jupyter
```

## Run native code

### Fortran

The cell body is ordinary Fortran source:

```ipython
%%fortran
module maths
contains
    real(8) function square(x)
        real(8), intent(in) :: x
        square = x*x
    end function
end module
```

PRIK publishes the declared Fortran module namespace:

```python
import numpy as np

maths.square(np.float64(4.0))
```

Each declared module becomes a notebook name. Standalone procedures are
published directly.

### C

C functions are published directly in the notebook namespace:

```ipython
%%c
double square(double x) {
    return x * x;
}
```

```python
square(np.float64(4.0))
```

## Edit the generated `.pyi`

Add `--pyi` when you want to edit the semantic contract before compilation:

```ipython
%%fortran --pyi
module maths
contains
    real(8) function square(x)
        real(8), intent(in) :: x
        square = x*x
    end function
end module
```

PRIK presents an editable `%%pyi` cell:

```ipython
%%pyi

# prik: file=maths.pyi source-sha256=<generated digest>

# Generated maths.pyi contract appears here.
```

Edit the declarations, keep the `# prik:` line, and run the cell. The
`maths.pyi` filename publishes the contract as `maths`. Standalone Fortran and
C contracts are published directly instead.

For source containing several modules, PRIK creates one editable cell per
module. Jupyter inserts them together; terminal IPython presents them in
sequence as you execute each contract. Compiler and build options are copied
from the source cell. Rerun the source cell to change them.

The same workflow works with `%%c --pyi`.

## Wrap an existing source file

Use `%%pyi` directly when the native source already exists as a file:

```ipython
%%pyi --native-fortran-sources geometry.f90

# prik: file=maths.pyi

from prik.contracts import Addr, Arg, Float64, native_call

@native_call([Addr(Arg(0))])
def square(x: Float64) -> Float64: ...
```

This cell publishes `maths`. To expose another module from the same source,
write another `%%pyi` cell with its module filename, such as
`# prik: file=maths2.pyi`.

List multiple source files in compilation order when needed:

```ipython
%%pyi --native-fortran-sources maths.f90 helpers.f90
```

```ipython
%%pyi --native-c-sources square.c
```

For C or standalone Fortran, omit the `file=` comment. Standalone Fortran
declarations still use `@standalone`. Relative source paths start from the
kernel's current working directory.

## Compilers and flags

The magics accept the same compiler and build options as the command line:

```ipython
%%fortran --compiler ifx --native-compile-flags="-O3 -march=native"
```

- `--native-compile-flags` applies to the cell's Fortran or C source.
- `--wrapper-fortran-flags` applies to generated Fortran bridge source.
- `--wrapper-c-flags` applies to generated C binding source and extension
  linking.
- `--compiler-arg` adds one preprocessing argument and may be repeated. Use
  the equals form for a dash-prefixed value, such as
  `--compiler-arg=-fdefault-real-8`.

## Cell cache

PRIK reuses a compiled result when the cell, compiler, flags, and native files
are unchanged. Use `--force` to rebuild or `--verbose` to show build activity:

```ipython
%%fortran --force
```

```ipython
%%fortran --verbose
```

## Limitations

Source magics compile one self-contained cell. Use PRIK's CLI or Python build
API for larger projects, external libraries, mixed-language builds, and
advanced link configuration.
