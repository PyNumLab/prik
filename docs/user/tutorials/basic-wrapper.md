---
title: Basic Wrapper Tutorial
audience: users
prerequisites: installation, supported compiler toolchain
related: ../getting-started/index.md, ../examples/verified-cookbook.md
status: maintained
publication: draft
---

# Basic Wrapper Tutorial

This tutorial walks through one beginner path:

1. inspect a small Fortran source file;
2. generate the semantic contract x2py sees;
3. check whether the contract is ready for wrapping;
4. build a real Python extension; and
5. import the extension and call one function.

At the end, you should have seen both sides of x2py:

- the inspection path, which is useful for understanding a native API; and
- the wrapper path, which compiles an importable Python extension from Fortran.

<!-- X2PY_C_DOCS_START
- the wrapper path, which compiles an importable CPython extension for the
  implemented Fortran backend.
X2PY_C_DOCS_END -->

For lookup-style commands, use the
[verified examples cookbook](../examples/verified-cookbook.md). For
the full generated Python contract, use the
[Fortran wrapper reference](../reference/fortran-wrapper.md).

## Before You Start

x2py requires Python 3.10 or newer. Wrapper builds also need a working GNU
native toolchain, Python development headers, and NumPy development files.

<!-- X2PY_C_DOCS_START
x2py requires Python 3.10 or newer. Wrapper builds also need a working GNU
Fortran/C toolchain, Python development headers, and NumPy headers.
X2PY_C_DOCS_END -->

Install the checkout and inspect the CLI:

```bash
python3 -m pip install -e .
python3 -m x2py --help
```

The examples below use repository fixtures and run from the repository root.
They use `python3`; replace that with your Python 3.10+ executable if needed.

## What x2py Builds

The current runtime wrapper backend is implemented for Fortran source inputs.
Given ordered Fortran sources, x2py performs this pipeline:

```text
Fortran sources
  -> compiler preprocessing and target-type probing
  -> parser facts
  -> semantic IR construction
  -> generated native bridge and Python binding
  -> compiled Python extension
```

<!-- X2PY_C_DOCS_START
```text
Fortran sources
  -> compiler preprocessing and target-type probing
  -> parser facts
  -> semantic IR construction
  -> generated Fortran bind(C) bridge
  -> generated C/CPython binding and native binding support
  -> compiled Python extension
```
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
C inputs currently support inspection, semantic IR, and `.pyi`
reports. Runtime wrapping of user-supplied C libraries is future backend work.
X2PY_C_DOCS_END -->

## Step 1: Inspect A Small Fortran Source

Start with this checked fixture:

<!-- x2py-doc-source: tests/data/fortran/general/basic_subroutine.f90 -->
```fortran
module m1
contains
subroutine add1(n, x)
  integer, intent(in) :: n
  real(kind=8), intent(inout), dimension(n) :: x
end subroutine add1
end module m1
```

Ask x2py for the parser-level source facts:

<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90
```

Expected output:

<!-- x2py-doc-test-output -->
```text
File: tests/data/fortran/general/basic_subroutine.f90
  Modules: 1
    - module m1 (vars=0, uses=0)
      Procedures: 1
        - subroutine add1(n:integer[0], x:real(8)[1])
```

This output is intentionally compact. It says there is one module and one
subroutine, but it does not yet decide the Python wrapper behavior.

## Step 2: Generate The Editable Contract

Generate the semantic `.pyi` contract:

<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py generate --pyi tests/data/fortran/general/basic_subroutine.f90
```

Expected output:

<!-- x2py-doc-test-output -->
```python
File: tests/data/fortran/general/basic_subroutine.f90
Root contract: basic_subroutine/basic_subroutine.pyi
from . import m1

Module contract: m1.pyi
from x2py.contracts import Addr, Arg, Float64, Int32, native_call

@native_call([Addr(Arg(0)), Arg(1)])
def add1(
    n: Int32,
    x: Float64[n]
) -> None: ...
```

Read this as the native boundary x2py must preserve:

- `n` is a read-only integer value in Python; the native call receives the
  address of x2py's converted native slot for that value.
- `x` is a writable rank-one `Float64` array whose size is described by `n`.
- The subroutine returns `None` because it mutates the caller-provided array.

The full `.pyi` syntax is documented in
[Semantic .pyi Format](../reference/semantic-pyi-format.md).

## Step 3: Build A Real Extension

Use a tiny runtime fixture for the first compiled wrapper:

<!-- x2py-doc-source: tests/data/fortran/wrapper/fruntime_abi_f90.f90 -->
```fortran
module fruntime_abi_f90
contains
  real(8) function scale(value, factor) result(output)
    real(8), intent(in) :: value
    real(8), intent(in) :: factor
    output = value * factor
  end function scale
end module fruntime_abi_f90
```

From the command line, a build looks like this:

```bash
python3 -m x2py tests/data/fortran/wrapper/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

The command writes generated bridge, binding, runtime, object, and shared
library artifacts under the output directory. The JSON output reports the
module name and generated files. Recognizable wrapper inputs select the wrapper
build stage automatically when no inspection stage is selected.

## Step 5: Import And Call The Extension

This checked Python example builds into a temporary directory, imports the
generated extension from the returned shared-library path, and calls the native
function:

<!-- x2py-doc-test: exact -->
```python
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from x2py import build_fortran_extension

source = Path("tests/data/fortran/wrapper/fruntime_abi_f90.f90")
with TemporaryDirectory() as output_dir:
    build = build_fortran_extension(source, output_dir=output_dir)
    spec = spec_from_file_location(build.module_name, build.shared_library)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    native_module = module.fruntime_abi_f90

    print(build.module_name)
    print(native_module.scale(np.float64(3.0), np.float64(2.5)))
```

Expected output:

<!-- x2py-doc-test-output -->
```text
fruntime_abi_f90
7.5
```

The exact NumPy scalar types are part of the native ABI contract. Passing a
plain Python `float` where the wrapper requires `numpy.float64` raises
`TypeError` instead of silently changing the native conversion.

## Common Beginner Mistakes

| Symptom | Check |
| --- | --- |
| Importing the extension fails | Make sure the output directory is on `sys.path`, or load the shared library path returned by the Python API. |
| A Python number is rejected | Pass the exact NumPy scalar dtype required by the native signature. |
| Generated files are hard to inspect | Build with `--out-dir` and optionally `--verbose` to keep and print artifact paths. |

<!-- X2PY_C_DOCS_START
| The compiler cannot be found | Install `gfortran` and a C compiler, or pass the project compiler settings. |
| C inspection succeeds | C-input runtime wrapping is not implemented yet. |
X2PY_C_DOCS_END -->

## What You Learned

You used x2py to:

- read Fortran source facts;
- inspect the semantic `.pyi` contract;
- build the wrapper plan through the default build path; and
- build, import, and call a generated extension.

Next:

- Use the [verified examples cookbook](../examples/verified-cookbook.md)
  for task-specific recipes.
- Use the [Fortran wrapper reference](../reference/fortran-wrapper.md) for the
  complete generated Python behavior.
- Use [Semantic .pyi Format](../reference/semantic-pyi-format.md) when editing
  wrapper contracts.
