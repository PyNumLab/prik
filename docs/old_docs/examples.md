---
title: Verified Examples Cookbook
audience: users
prerequisites: installation, first wrapped function
related: examples-gallery/index.md
status: maintained
---

# Verified Examples Cookbook

This cookbook collects supported x2py commands and Python API patterns. The
repository fixture commands and inline Python snippets are covered by the
current test suite or can be run directly from the repository root.

Start with the [tutorial](tutorial.md) if this is your first x2py workflow.
Use the [semantic `.pyi` format](pyi_format.md) for the full accepted `.pyi`
contract and the [semantic IR reference](semantics.md) for datatype details.

## Fixture Inputs

The most useful small, checked examples are:

| Purpose | Repository fixture |
| --- | --- |
| Compiled Fortran wrapper and scalar call | `tests/data/fortran/wrapper/feature_parity/runtime/fruntime_abi_f90.f90` |
| Multi-source Fortran wrapper | `tests/wrapper/fortran/multi_source/modules/` |
| Basic Fortran procedure | `tests/data/fortran/general/basic_subroutine.f90` |
| Rich Fortran module, types, arrays, and visibility | `tests/data/fortran/general/modern_pyi_example.f90` |
| Basic C functions, pointers, and arrays | `tests/data/c/general/math_api.h` |
| Generated Fortran semantic interface | `tests/pyi/fixtures/general/modern_pyi_example.pyi` |
| Generated C semantic interface | `tests/pyi/fixtures/c/general/math_api.pyi` |

The core native inputs are included here so the command examples are
self-contained.

### Basic Fortran Input

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

### Runtime Fortran Wrapper Input

<!-- x2py-doc-source: tests/data/fortran/wrapper/feature_parity/runtime/fruntime_abi_f90.f90 -->
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

### Basic C Input

<!-- x2py-doc-source: tests/data/c/general/math_api.h -->
```c
#ifndef X2PY_GENERAL_MATH_API_H
#define X2PY_GENERAL_MATH_API_H

double norm2(int n, const double x[static 1]);
void scale(int n, double alpha, double x[static 1]);
double dot(int n, const double *restrict x, const double *restrict y);
void fill_identity3(double a[static 3][3]);

#endif
```

### Rich Fortran Input

<details>
<summary>Show <code>tests/data/fortran/general/modern_pyi_example.f90</code></summary>

<!-- x2py-doc-source: tests/data/fortran/general/modern_pyi_example.f90 -->
```fortran
module modern_math_physics
  implicit none
  private
  public :: particle, vector3, counter, init_particle, kinetic_energy, scale_vector, dot3, fill_identity3, normalize_particle

  integer :: counter
  real(8) :: hidden_scale

  type :: particle
     integer :: id
     real(8) :: mass
     real(8), dimension(3) :: position
  end type particle

  type :: vector3
     real(8), dimension(3) :: values
  end type vector3

  type :: hidden_state
     integer :: code
  end type hidden_state

contains

  subroutine init_particle(p, pid, mass, x, y, z)
    type(particle), intent(out) :: p
    integer, intent(in) :: pid
    real(8), intent(in) :: mass, x, y, z
    p%id = pid
    p%mass = mass
    p%position = [x, y, z]
  end subroutine init_particle

  function kinetic_energy(p, vx, vy, vz) result(e)
    type(particle), intent(in) :: p
    real(8), intent(in) :: vx, vy, vz
    real(8) :: e
    e = 0.5d0 * p%mass * (vx*vx + vy*vy + vz*vz)
  end function kinetic_energy

  subroutine scale_vector(v, alpha)
    real(8), dimension(:), intent(inout) :: v
    real(8), intent(in) :: alpha
    v = alpha * v
  end subroutine scale_vector

  function dot3(a, b) result(s)
    real(8), dimension(3), intent(in) :: a, b
    real(8) :: s
    s = a(1)*b(1) + a(2)*b(2) + a(3)*b(3)
  end function dot3

  subroutine fill_identity3(a)
    real(8), dimension(3,3), intent(out) :: a
    a = 0.0d0
    a(1,1) = 1.0d0
    a(2,2) = 1.0d0
    a(3,3) = 1.0d0
  end subroutine fill_identity3

  subroutine normalize_particle(p)
    type(particle), intent(inout) :: p
    real(8) :: n
    n = sqrt(dot3(p%position, p%position))
    if (n > 0.0d0) p%position = p%position / n
  end subroutine normalize_particle

  subroutine hidden_proc(x)
    integer, intent(in) :: x
  end subroutine hidden_proc

end module modern_math_physics
```

</details>

## Fortran Runtime Wrapper Examples

These examples use the implemented Fortran wrapper backend. They require a GNU
Fortran/C toolchain, Python development headers, and NumPy headers. Runtime
wrapping of user-supplied C inputs is not implemented yet and will be added as
a separate backend later.

### Build And Import With The CLI

Build the checked scalar fixture into an explicit directory:

```bash
python3 -m x2py tests/data/fortran/wrapper/feature_parity/runtime/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

Recognizable Fortran sources use the default wrapper build when no inspection
stage is selected:

```bash
python3 -m x2py tests/data/fortran/wrapper/feature_parity/runtime/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

Import and call the extension:

```python
import sys

import numpy as np

sys.path.insert(0, "build/fruntime_abi")
import fruntime_abi_f90

result = fruntime_abi_f90.scale(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

Exact NumPy scalars are part of the native contract. Passing ordinary Python
numbers where a specific native dtype is required raises `TypeError` rather
than silently changing the ABI conversion.

With no `--out-dir`, x2py writes intermediates and the ABI-suffixed extension
under `__x2py__` in the current working directory, while a direct CLI build
writes its stable `<module>.so` alias there unless `--out` gives it an explicit path.
Use `--verbose` to
print the direct compiler and linker commands. Use `--strict-wrapper-names` to
reject public names that need Python keyword escaping or collision suffixes.

### Build And Import Through The Python API

`build_fortran_extension` returns a `WrapperBuildResult` containing the module
name and every generated artifact. This checked example uses a temporary
directory and loads the extension directly from the returned shared-library
path:

<!-- x2py-doc-test: exact -->
```python
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from x2py import build_fortran_extension

source = Path("tests/data/fortran/wrapper/feature_parity/runtime/fruntime_abi_f90.f90")
with TemporaryDirectory() as output_dir:
    build = build_fortran_extension(source, output_dir=output_dir)
    spec = spec_from_file_location(build.module_name, build.shared_library)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    print(build.module_name)
    print(module.scale(np.float64(3.0), np.float64(2.5)))
```

<!-- x2py-doc-test-output -->
```text
fruntime_abi_f90
7.5
```

### Generate An Editable Makefile

Generate wrapper sources and `Makefile.x2py` without compiling:

```bash
python3 -m x2py generate --makefile tests/data/fortran/wrapper/feature_parity/runtime/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

Build it with GNU Make:

```bash
make -f build/fruntime_abi/Makefile.x2py -j4 \
  X2PY_FFLAGS=-O3 \
  X2PY_CFLAGS=-O3 \
  X2PY_LDFLAGS=-O3
```

The generated Makefile exposes `FC`, `CC`, `X2PY_LD`, `X2PY_FFLAGS`,
`X2PY_CFLAGS`, and `X2PY_LDFLAGS`. User Fortran sources remain ordered;
independent generated objects may be built in parallel.

### Build One Extension From Multiple Sources

Supply every source in compiler-valid order. The first semantic module names
the merged extension:

```bash
python3 -m x2py \
  tests/data/fortran/wrapper/multi_source/modules/first_api.f90 \
  tests/data/fortran/wrapper/multi_source/modules/second_api.f90 \
  --out-dir build/multi_api \
  --json
```

```python
import sys

import numpy as np

sys.path.insert(0, "build/multi_api")
import first_api

assert first_api.add_one(np.int32(4)) == np.int32(5)
assert first_api.double_value(np.int32(4)) == np.int32(10)
```

x2py does not discover missing sources or reorder dependencies. Provide module
providers before consumers. See
[Multiple Sources And Build Modes](fortran_wrapper.md#multiple-sources-and-build-modes)
for output placement and build-system details.

## CLI Stage Examples

### Parse

Compact Fortran report:

```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90
```

Compact C report:

```bash
python3 -m x2py parse tests/data/c/general/math_api.h --language c
```

Full parser payload:

```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90 --json
python3 -m x2py parse tests/data/c/general/math_api.h --language c --json
```

### Semantic IR

```bash
python3 -m x2py semantics tests/data/fortran/general/basic_subroutine.f90
python3 -m x2py semantics tests/data/c/general/math_api.h --language c
```

The semantic payload includes `semantic_modules` and generated `pyi` text.

### `.pyi` Emission

Print:

```bash
python3 -m x2py generate --pyi tests/data/fortran/general/basic_subroutine.f90
python3 -m x2py generate --pyi tests/data/c/general/math_api.h --language c
```

Write an explicit interface file:

```bash
python3 -m x2py generate --pyi tests/data/fortran/general/basic_subroutine.f90 \
  --out /tmp/basic_subroutine.pyi
```

Write one interface beside each input:

```bash
python3 -m x2py generate --pyi path/to/fortran_sources --language fortran --out
```

## Control Human-Readable Parse Output

Fortran variable sections are compact by default. Expand them with
`--show-vars`:

<!-- x2py-doc-test: run -->
```bash
python3 -m x2py parse tests/data/fortran/general/modern_pyi_example.f90 \
  --show-vars
```

Limit every repeated section:

<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py parse tests/data/fortran/general/modern_pyi_example.f90 \
  --show-vars --print-limit 1
```

This reports totals while showing one item from each repeated section:

<!-- x2py-doc-test-output -->
```text
File: tests/data/fortran/general/modern_pyi_example.f90
  Modules: 1
    - module modern_math_physics (vars=2, uses=0)
      Variables: 2
        - counter:integer[0]
        ... 1 more variables
      Derived types: 3
        - type particle (fields=3, methods=0)
          Fields: 3
            - id:integer[0]
            ... 2 more fields
        ... 2 more derived types
      Procedures: 7
        - subroutine init_particle(p:type(particle)[0], pid:integer[0], mass:real(8)[0], x:real(8)[0], y:real(8)[0], z:real(8)[0])
        ... 6 more procedures
```

`--show-vars` is Fortran-only. `--print-limit` works with human-readable C and
Fortran parse reports.

## Input And Project Examples

### Explicit Files

```bash
python3 -m x2py parse src/types.f90 src/api.f90 --language fortran
python3 -m x2py parse include/types.h include/api.h --language c
```

### Directories

Directories require an explicit frontend:

```bash
python3 -m x2py parse src/fortran --language fortran --print-limit 20
python3 -m x2py parse src/c --language c --print-limit 20
```

Fortran directory discovery is recursive for recognized Fortran suffixes. C
directory discovery includes recognized C source, header, and preprocessed
input suffixes.

### Unknown Suffixes

Use an explicit frontend when the source suffix does not identify the
language:

```bash
python3 -m x2py parse generated/api.source --language c
python3 -m x2py parse generated/api.source --language fortran
```

## Compiler Preprocessing

The shared CLI preprocesses source before parsing. This is the supported path
for macros, conditional compilation, target flags, and native includes.

### C Compiler And Flags

```bash
python3 -m x2py parse include/api.h --language c \
  --compiler clang \
  -I include \
  -D API_EXPORT= \
  -U LEGACY_API \
  --std c11 \
  --compiler-arg=--sysroot=/opt/sdk
```

### C Compilation Database

```bash
python3 -m x2py semantics src/api.c --language c \
  --compile-commands build/compile_commands.json
```

Extra wrapper-specific flags can be added to the selected database entry:

```bash
python3 -m x2py semantics src/api.c --language c \
  --compile-commands build/compile_commands.json \
  --compiler-arg=-DX2PY_SCAN=1
```

### Fortran Compiler And Flags

```bash
python3 -m x2py generate --pyi src/api.f90 --language fortran \
  --compiler gfortran \
  -I include \
  -D USE_MPI \
  --std f2008 \
  --compiler-arg=-fdefault-real-8
```

### Custom Command Template

Use a command template for an unsupported compiler family:

```bash
python3 -m x2py parse include/api.h --language c \
  --preprocessor-adapter command-template \
  --preprocess-template \
  'cc -E {include_dirs} {defines} {undefs} {standard} {compiler_args} {source}'
```

Supported placeholders are `{source}`, `{include_dirs}`, `{defines}`,
`{undefs}`, `{standard}`, and `{compiler_args}`.

### Include Exposure

For C projects, reachable project includes are public by default and system
headers are private. Narrow or override that wrapper-facing surface:

```bash
python3 -m x2py generate --pyi include/api.h --language c \
  --include-exposure roots-only \
  --public-include 'include/public/*' \
  --private-include 'vendor/*'
```

Private declarations remain available for internal type resolution.

## Output File Examples

Write one parser payload to an explicit path:

```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90 \
  --json --out /tmp/basic_subroutine.json
```

Write one parser payload beside each source:

```bash
python3 -m x2py parse path/to/fortran_sources --language fortran --out
```

Write an explicit `.pyi`:

```bash
python3 -m x2py tests/data/c/general/math_api.h \
  --language c --pyi --out /tmp/math_api.pyi
```

`--out` requires a selected stage. `--json` and `--pyi` cannot both be used
with `--out`.

## Diagnostic Examples

Parser and preprocessing failures are rendered without a Python traceback by
default. Disable ANSI color for logs:

```bash
python3 -m x2py parse path/to/source.f90 --no-color
```

Re-raise an error with a traceback while debugging:

```bash
python3 -m x2py parse path/to/source.f90 --debug
```

Stable diagnostic categories are listed in
[diagnostic_codes.md](diagnostic_codes.md).

## Python API Examples

Direct parser APIs accept controlled source strings and paths. They do not run
the shared CLI compiler preprocessing pipeline.

### Parse Inline Fortran

<!-- x2py-doc-test: exact -->
```python
from x2py import parse_fortran_file

parsed = parse_fortran_file(
    "subroutine ping(n)\n"
    "  integer, intent(in) :: n\n"
    "end subroutine ping\n",
    filename="inline.f90",
)

print(parsed.procedures[0].name)  # ping
```

Output:

<!-- x2py-doc-test-output -->
```text
ping
```

### Parse Inline C

<!-- x2py-doc-test: exact -->
```python
from x2py import parse_c_file

parsed = parse_c_file("int add(int a, int b);", filename="inline.h")

print([function.name for function in parsed.functions])  # ['add']
```

Output:

<!-- x2py-doc-test-output -->
```text
['add']
```

### Parse An In-Memory C Project

<!-- x2py-doc-test: exact -->
```python
from x2py import parse_c_project

project = parse_c_project(
    {
        "types.h": "typedef int api_int;",
        "api.h": '#include "types.h"\napi_int answer(void);',
    }
)

print(sorted(project.files))      # ['api.h', 'types.h']
print(sorted(project.functions))  # ['answer']
```

Output:

<!-- x2py-doc-test-output -->
```text
['api.h', 'types.h']
['answer']
```

### Parse An In-Memory Fortran Project

<!-- x2py-doc-test: exact -->
```python
from x2py import parse_fortran_project

project = parse_fortran_project(
    {
        "types.f90": "module types\nend module types\n",
        "api.f90": (
            "module api\n"
            "  use types\n"
            "end module api\n"
        ),
    }
)

print(sorted(project.modules))  # ['api', 'types']
```

Output:

<!-- x2py-doc-test-output -->
```text
['api', 'types']
```

### Convert C To Semantic IR And Emit `.pyi`

<!-- x2py-doc-test: exact -->
```python
from x2py import (
    c_file_to_semantic_modules,
    emit_module_stubs,
    parse_c_file,
)

parsed = parse_c_file("int add(int a, int b);", filename="inline.h")
modules = c_file_to_semantic_modules(parsed)

print(emit_module_stubs(modules)["inline"])
```

Output:

<!-- x2py-doc-test-output -->
```text
def add(
    a: Int,
    b: Int
) -> Int: ...
```

## Supported `.pyi` Examples

These examples show semantic syntax accepted by the current loader. They are
contracts and metadata; they are not executable Python wrapper
implementations.

### Scalars, Addresses, And Arrays

```python
def direct(value: Float64) -> Float64: ...
def inspect(value: Int32[()]) -> None: ...
def update(value: Float64[()]) -> None: ...
def update_raw(value: Addr(Float64)) -> None: ...
def scale(n: Int32, values: Float64[n]) -> None: ...
def dot3(a: Float64[3], b: Float64[3]) -> Float64: ...
```

### Constants, Visibility, And Classes

```python
from typing import Final

nmax: Final[Int32] = 32
hidden_scale: private[Float64]

class particle:
    id: Int32
    mass: Float64
    position: Float64[3]

@private
def helper(x: Addr(Int32)) -> None: ...
```

### Opaque Types

```python
class context(Opaque):
    pass

def context_create() -> Addr(context): ...
def context_destroy(ctx: Addr(context)) -> None: ...
```

### Array Metadata

```python
def fill(
    values: Float64[:]
) -> None: ...

def fill_matrix(
    values: Annotated[Float64[3, 3], ORDER_F]
) -> None: ...
```

### Complete Callback Signature

```python
from x2py.contracts import prototype

@prototype
def objective(value: Float64) -> Float64: ...

def integrate(
    callback: objective,
    x0: Float64
) -> Float64: ...
```

The prototype names every callback argument and its result explicitly.

### Preserved Projection Metadata

```python
@native_call([Arg(0), Arg(1), Return(0)])
def add(a: Float64, b: Float64) -> Float64: ...
```

The current loader and printer preserve supported `@native_call` metadata.
The source-driven Fortran wrapper implements the built-in projections documented
in the [Fortran wrapper guide](fortran_wrapper.md), but the CLI does not build
directly from an edited `.pyi` or execute arbitrary edited `@native_call`
metadata. Use the [semantic `.pyi` format](pyi_format.md) for accepted entries
and limitations.

## Stage Error Examples

### Missing Callback Signature

```python
def integrate(objective: Procedure, x0: Float64) -> Float64: ...
```

This is blocked because callback argument order, argument types, and return
type are incomplete. Replacing `Procedure` with a complete named prototype
supplies the semantic signature.

### Missing Compile-Time Constant

```python
from typing import Final

n: Final[Int32]

def fill(values: Float64[n]) -> None: ...
```

This is blocked because `n` has no literal value. Supplying a value makes the
shape resolvable:

```python
n: Final[Int32] = 16
```

### Ambiguous C Pointer Policy

```c
int read_values(double *values, size_t n);
```

The parser preserves this signature as explicit semantic storage facts. A
future C runtime wrapper must complete ownership, input/output, and in-place
storage policy rather than inventing it from the declaration alone.

### Unsupported C Variadic Function

```c
int log_msg(const char *fmt, ...);
```

Current x2py does not generate a runtime wrapper for the variadic contract.

## More References

- [Tutorial](tutorial.md)
- [Fortran wrapper guide](fortran_wrapper.md)
- [Semantic `.pyi` format](pyi_format.md)
- [Semantic IR reference](semantics.md)
- [Diagnostic code registry](diagnostic_codes.md)
- [Developer guide](developper_guide.md): implementation and parser references
