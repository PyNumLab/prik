---
title: IPython and Jupyter Notebooks
description: Compile Fortran and C cells with PRIK cell magics
audience: users
prerequisites: installation, first wrapped function
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

Add `--pyi` when the generated Python API is not the one you want. PRIK
compiles nothing yet; it persists the source and hands back an editable
contract cell.

```ipython
%%c --pyi
#include <stddef.h>

void scale(size_t count, double *values) {
    for (size_t i = 0; i < count; ++i) values[i] *= 2.0;
}
```

PRIK inserts the contract it derived from that source:

```ipython
%%pyi

# prik: source-sha256=<generated digest>

from prik.contracts import Float64, UInt64

def scale(
    count: UInt64,
    values: Float64[...]
) -> None: ...
```

This is a faithful reading of the C, but it is not a good Python API: the
caller has to pass a length that NumPy already knows, and `Float64[...]`
accepts any rank because `double *` does not say which one it is. Edit the
cell, keep the `# prik:` line, and run it:

```ipython
%%pyi

# prik: source-sha256=<generated digest>

from prik.contracts import Arg, Float64, native_call

@native_call([Arg(0).size, Arg(0)])
def scale(values: Float64[:]) -> None: ...
```

`Float64[:]` requires a rank-one array, and `Arg(0).size` supplies `count`
from it, so `count` disappears from the Python signature:

```python
values = np.array([1.0, 2.0, 3.0])
scale(values)
values                 # array([2., 4., 6.]) -- updated in place
```

The native code and the compiler options are unchanged; only the Python API
you call is different.

### Contract cells and their names

Fortran source generates one editable cell per declared module, each carrying
a `file=` field:

```ipython
%%pyi

# prik: file=maths.pyi source-sha256=<generated digest>
```

**The `file=` leaf name is the Fortran module name**, not a name you choose —
`maths.pyi` is the contract for `module maths`, and it publishes `maths` in
the notebook. C source and standalone Fortran declarations have no module to
name, so their cells carry no `file=` field and publish their functions
directly.

Jupyter inserts every generated cell at once; terminal IPython presents them
in sequence as you execute each one. Compiler and build options are copied
from the source cell, so rerun the source cell to change them.

The same workflow works with `%%fortran --pyi`.

## Wrap an existing source file

Use `%%pyi` directly when the native source already exists as a file. There is
no source cell to generate from, so you write the contract yourself and name
the sources on the magic line:

```ipython
%%pyi --native-fortran-sources maths.f90

# prik: file=maths.pyi

from prik.contracts import Addr, Arg, Float64, native_call

@native_call([Addr(Arg(0))])
def square(x: Float64) -> Float64: ...
```

Here `file=maths.pyi` is the contract for `module maths` inside `maths.f90`,
and the cell publishes `maths`. The leaf name must match the Fortran module,
whatever the file is called — a mismatch reaches the Fortran compiler as a
missing `.mod`, not a PRIK diagnostic. To expose a second module from the same
source, write another `%%pyi` cell naming that module, such as
`# prik: file=helpers.pyi`.

List multiple source files in compilation order when needed:

```ipython
%%pyi --native-fortran-sources maths.f90 helpers.f90
```

```ipython
%%pyi --native-c-sources square.c
```

For C or standalone Fortran, omit the `# prik:` line entirely. Standalone
Fortran declarations still use `@standalone`. Relative source paths start from
the kernel's current working directory.

## Compilers and flags

```ipython
%%fortran --compiler ifx --native-compile-flags="-O3 -march=native"
```

- `--native-compile-flags` applies to the cell's own Fortran or C source. A
  cell has one native language, so there is a single option here; the command
  line splits the same setting into `--native-compile-flags` for Fortran and
  `--native-c-compile-flags` for C.
- `--wrapper-fortran-flags` applies to generated Fortran bridge source.
- `--wrapper-c-flags` applies to generated C binding source and extension
  linking.
- `--compiler-arg` adds one preprocessing argument and may be repeated.

**A value that starts with a dash needs the equals form.** `--native-compile-flags -O3`
reads `-O3` as another option and fails; write `--native-compile-flags=-O3`.
The three flag options also accept several flags as one quoted group:

```ipython
%%c --native-compile-flags="-O3 -march=native"
```

`--compiler-arg` is not split, so it carries exactly one argument. Repeat it
for more:

```ipython
%%fortran --compiler-arg=-fdefault-real-8 --compiler-arg=-I/opt/include
```

## Cell cache

PRIK reuses a compiled result when the cell, compiler, flags, and native files
are unchanged. Use `--force` to rebuild or `--verbose` to show build activity:

```ipython
%%fortran --force
```

```ipython
%%fortran --verbose
```

The cache persists between sessions in `~/.cache/prik/jupyter`, or under
`$XDG_CACHE_HOME/prik/jupyter` or `$PRIK_CACHE_DIR/jupyter` when either is
set. Each distinct cell text gets its own entry holding that cell's source,
generated wrapper, and compiled extension, so editing a cell repeatedly leaves
one entry per version. Nothing is evicted automatically. Delete the directory
to reclaim the space:

```bash
rm -rf ~/.cache/prik/jupyter
```

The next run of each cell rebuilds it.

## Limitations

Source magics compile one self-contained cell. Use PRIK's CLI or Python build
API for larger projects, external libraries, mixed-language builds, and
advanced link configuration.
