---
title: CMake Builds
description: Build PRIK Python extensions from an existing or generated CMake project
audience: users
prerequisites: building the shared library, CMake, Python development files
related: building-shared-library.md, ../reference/cli-commands.md
status: maintained
publication: reviewed
---

# CMake Builds

Use CMake when its toolchain, dependency targets, and build scheduling should
own compilation and linking. PRIK still parses the native inputs, completes
wrapper policy, and generates the wrapper and any Fortran bridge sources. By
default, PRIK uses CMake's selected C or Fortran compiler for source analysis.

## Existing CMake project

Install PRIK, make its `cmake` directory available through
`CMAKE_MODULE_PATH`, and include the packaged helper:

```cmake
cmake_minimum_required(VERSION 3.20)

project(MyPhysics LANGUAGES C Fortran)

find_package(
    Python
    COMPONENTS Interpreter Development.Module
    REQUIRED
)

# Ask PRIK's Python environment for its packaged CMake helper.
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "from prik.cmake import cmake_module_dir; print(cmake_module_dir().as_posix())"
    RESULT_VARIABLE PRIK_CMAKE_MODULE_RESULT
    OUTPUT_VARIABLE PRIK_CMAKE_MODULE_DIR
    ERROR_VARIABLE PRIK_CMAKE_MODULE_ERROR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(NOT PRIK_CMAKE_MODULE_RESULT EQUAL 0)
    message(FATAL_ERROR "Cannot locate UsePRIK.cmake: ${PRIK_CMAKE_MODULE_ERROR}")
endif()
list(APPEND CMAKE_MODULE_PATH "${PRIK_CMAKE_MODULE_DIR}")
include(UsePRIK)

prik_add_module(
    physics
    FORTRAN_SOURCES
        solver.f90
        matrix.f90
)
```

Then configure and build the extension:

```bash
cmake -S . -B build
cmake --build build
```

`prik_add_module()` also accepts `SOURCES` for source-first input, `CONTRACT`
with `FORTRAN_SOURCES` or `C_SOURCES` for an authored semantic `.pyi`,
`INCLUDE_DIRS`, `MODULE_DIRS`, language-specific compile flags,
`LINK_LIBRARIES`, `LINK_OPTIONS`, and additional `PRIK_ARGS`. Use
`NO_COMPILE_INPUT_SOURCES` when `SOURCES` supplies only the public interface
and `FORTRAN_SOURCES` or `C_SOURCES` supplies its implementation. The
generated wrapper sources are custom-command outputs. Changing a semantic
source or contract regenerates them before CMake compiles the target; CMake
recompiles contract-first native implementations independently.

External dependencies remain CMake dependencies. For example, CMake can find
BLAS and pass its target to the PRIK extension:

```cmake
find_package(BLAS REQUIRED)

prik_add_module(
    blas_example
    FORTRAN_SOURCES blas_example.f90
    LINK_LIBRARIES BLAS::BLAS
)
```

The same form accepts normal project targets such as `native_math` and
`OpenMP::OpenMP_Fortran`; they remain target-oriented CMake link inputs.

## Standalone generated project

Generate a small CMake project from native sources:

```bash
python3 -m prik generate --cmake solver.f90 --out-dir build/solver
cmake -S build/solver -B build/solver/cmake-build
cmake --build build/solver/cmake-build
```

For an authored contract, provide its implementation sources as usual:

```bash
python3 -m prik generate --cmake contracts/solver.pyi \
    --native-fortran-sources solver.f90 \
    --out-dir build/solver
```

The generated `CMakeLists.txt` loads `UsePRIK.cmake` and calls
`prik_add_module()`. `UsePRIK.cmake` integrates PRIK into an existing CMake
project; `prik generate --cmake` creates a standalone CMake project that uses
that same helper.
