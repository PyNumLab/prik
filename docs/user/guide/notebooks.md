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

## Compile a Fortran module

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

PRIK publishes the declared Fortran module namespace, not an artificial name
derived from a temporary cell file:

```python
import numpy as np

maths.square(np.float64(4.0))
```

Notebook function identities use that same public path. Introspection displays
`maths.square`; the private `_prik_...` extension name used for cache-safe
loading is not part of the function's public name. A standalone function is
identified simply as `square`.

Multiple declared Fortran modules become separate notebook names. Public
standalone procedures, which have no Fortran module namespace, are published
directly in the notebook namespace.

## Edit the generated `.pyi`

Add `--pyi` to a native-source magic when you want to review or edit the
semantic contract before compilation:

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

This cell saves the exact native source in PRIK's notebook cache and asks the
notebook frontend to insert an editable cell immediately below it. A module
contract has its generated `.pyi` filename in a reserved metadata comment:

```ipython
%%pyi

# prik: file=maths.pyi source-sha256=<generated digest>

# Generated maths.pyi contract appears here.
```

An explicitly selected compiler and any build flags are copied into the
inserted `%%pyi` line, so the editable cell preserves the source cell's build
configuration.

Edit the generated contract and execute that cell normally. `%%pyi` recognizes
the reserved comment and uses its source digest to recover both the native
language and exact cached source, then builds through PRIK's semantic `.pyi`
path. The filename `maths.pyi` determines the public module namespace, so its
declarations are available through `maths.<name>`. Keep the reserved metadata
comment in the cell; PRIK removes it before parsing the editable contract.

Standalone procedures are inserted in a separate editable cell without a
`file=` field:

```ipython
%%pyi

# prik: source-sha256=<generated digest>

@standalone
def square(...): ...
```

The `@standalone` contract decorator remains authoritative, so executing this
cell publishes `square` directly in the notebook namespace. PRIK does not show
or ask the user to edit the internal package entry used to build either form.
If one source cell declares multiple modules, each generated module contract
is inserted as its own editable cell.

The same workflow applies to C with `%%c --pyi`.
Because a C translation unit does not define a Python module namespace, its
editable metadata has no `file=` field and its declarations are published
directly after compilation.

## Compile C source

C translation units do not declare a module namespace, so their public wrapper
names are published directly:

```ipython
%%c
double square(double x) {
    return x * x;
}
```

```python
square(np.float64(4.0))
```

Running another cell that publishes the same name replaces that name in the
notebook namespace, matching the normal interactive redefinition workflow.

## Compilers and flags

Use `--compiler` to select the compiler used for preprocessing, target probes,
native compilation, generated wrapper compilation, and linking:

```ipython
%%fortran --compiler ifx
```

```ipython
%%fortran --compiler gfortran
```

The magic uses the same build flag boundaries as the command line. Quote a
group of flags whose individual values begin with `-`:

```ipython
%%fortran --native-compile-flags="-O3 -march=native"
```

- `--native-compile-flags` applies to the cell's Fortran or C source.
- `--wrapper-fortran-flags` applies to generated Fortran bridge source.
- `--wrapper-c-flags` applies to generated C binding source and extension
  linking.
- `--compiler-arg` adds one preprocessing argument and may be repeated. Use
  the equals form for a dash-prefixed value, such as
  `--compiler-arg=-fdefault-real-8`.

## Cell cache

The cache entry digest is exactly the SHA-256 of the selected language followed
by the exact cell contents. Re-running an unchanged cell with the same compiler
and flags imports the cached extension without compiling it again. Build
options and the active PRIK and Python ABI are validated within that digest
entry; changing one rebuilds instead of loading an incompatible extension.

For `%%fortran --pyi` and `%%c --pyi`, the source digest identifies the cached
native source and its language. An edited `%%pyi` cell has its own exact-cell
digest, so changing its contract text creates a distinct build without
overwriting another edit. If the source cache entry is unavailable, execute
the native source cell again before executing its editable contract.

Use `--force` to compile even when the cache is reusable:

```ipython
%%fortran --force
```

Use `--verbose` to print the ordinary PRIK build steps and compiler commands;
on a cache hit it reports that the cached cell was reused:

```ipython
%%fortran --verbose
```

The cache lives below `PRIK_CACHE_DIR/jupyter` when `PRIK_CACHE_DIR` is set,
then `$XDG_CACHE_HOME/prik/jupyter`, and otherwise
`~/.cache/prik/jupyter`.

## Limitations

The magics accept one self-contained native source cell and `%%pyi` only builds
an editable contract generated from a cached source cell. It does not accept an
uploaded or independently authored `.pyi` file, combine separate source cells
into a native project, or expose the internal extension container in the
notebook namespace. Insertion relies on frontend support for Jupyter's
next-input payload. Loading the extension fails if another extension already
owns `%%fortran`, `%%c`, or `%%pyi`; PRIK does not silently replace another
magic. Use PRIK's CLI or Python build API for file-based contracts, multiple
source files, external native objects or libraries, or advanced link
configuration.
