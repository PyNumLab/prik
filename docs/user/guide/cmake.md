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
default, PRIK uses CMake's selected C or Fortran compiler for preprocessing,
source analysis, and ABI probes. CMake mode does not accept a separate
`--compiler` override because the analyzed and compiled toolchains must agree.

The work splits across the two CMake phases:

- **Configure** asks PRIK only for structure: the generated filenames, the link
  driver, and any compiler ABI flags its profile requires. PRIK does not
  preprocess, parse, complete policy, plan, or generate code here, so
  configuring stays cheap however large the sources are.
- **Build** runs the full PRIK pipeline exactly once, writing the wrapper, the
  header, the binding-support headers, and a dependency file.

Because configuration never reads a source, the generated file list cannot
depend on what analysis finds. PRIK therefore names the optional compilation
units up front and always writes them: a module that needs no collision-adapter
unit still gets `<module>_adapters.c`, and a Fortran module that needs no bridge
still gets `bind_c_<module>_wrapper.f90`. An unused unit holds a small
placeholder that defines no symbol and compiles without warnings. A semantic
edit then changes a file's *contents* rather than the set of files, so editing
a source never requires re-running `cmake` to configure.

Transitive semantic inputs -- a nested C header, a Fortran `INCLUDE` file, an
imported contract -- reach CMake through the dependency file PRIK writes during
generation, so changing one reruns generation on the next build. This uses
`add_custom_command(DEPFILE)`, which is why the helper requires CMake 3.21 or
newer.

## Existing CMake project

Install PRIK, make its `cmake` directory available through
`CMAKE_MODULE_PATH`, and include the packaged helper:

```cmake
cmake_minimum_required(VERSION 3.21)

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
`INCLUDE_DIRS`, `MODULE_DIRS`, native and generated-source compile flag groups,
`LINK_LIBRARIES`, `LIBRARY_DIRS`, `LINK_OPTIONS`, and additional
generation-only `PRIK_ARGS`.
For a contract backed only by opaque native inputs, use `NATIVE_LANGUAGE` to
state the contract ABI language and `LINKER_LANGUAGE` to state the final CMake
linker driver independently:

```cmake
prik_add_module(
    c_api
    CONTRACT api.pyi
    NATIVE_LANGUAGE C
    LINKER_LANGUAGE Fortran
    LINK_LIBRARIES native_fortran_archive
)
```

When native source files use one language, PRIK infers `NATIVE_LANGUAGE` from
`FORTRAN_SOURCES` or `C_SOURCES`. Set it explicitly when the contract ABI
differs from the implementation source language or when both source languages
are present. A source-free contract must state it explicitly. CMake's C
language must be enabled because every PRIK extension contains generated C
binding code, and Fortran must be enabled whenever the module contributes
Fortran sources.

C sources must use the lowercase `.c` suffix here. CMake compiles `.C` as C++,
which would not match the C plan PRIK generates for the source, so
`prik_add_module()` and `generate --cmake` reject that suffix instead of
letting the two disagree.

The flag groups remain separate:

- `FORTRAN_FLAGS` and `C_FLAGS` apply only to user-owned native sources.
- `WRAPPER_FORTRAN_FLAGS` applies only to generated Fortran bridge sources.
- `WRAPPER_C_FLAGS` applies to generated C sources and the extension link,
  matching PRIK's normal build behavior.

PRIK adds compiler-profile flags required by its ABI plan to the affected
Fortran sources. `NO_STANDARD_LOGICALS` disables PRIK's Intel/NVIDIA logical
interoperability option when compatibility with prebuilt objects requires it.
Only mandatory ABI flags are exported from PRIK's plan; recommended compiler
profile options remain the CMake toolchain's responsibility.
CMake build type, debug, and interprocedural-optimization settings remain
normal CMake target properties; set
`CMAKE_INTERPROCEDURAL_OPTIMIZATION` before `prik_add_module()` when IPO should
cover both native and generated sources. Standalone `--cmake --lto` emits that
initializer automatically. `PRIK_ARGS` rejects compiler and compilation
options that would bypass those target settings.

Use `NO_COMPILE_INPUT_SOURCES` when `SOURCES` supplies only the public
interface. Its implementation may come from `FORTRAN_SOURCES`, `C_SOURCES`, a
prebuilt library, or a target in `LINK_LIBRARIES`:

```cmake
add_library(native_math STATIC implementation.f90)

prik_add_module(
    python_api
    SOURCES interface.f90
    NO_COMPILE_INPUT_SOURCES
    LINK_LIBRARIES native_math
)
```

The generated wrapper sources are custom-command outputs. Changing a semantic
source, contract, included C header, or Fortran `INCLUDE` file regenerates them
before CMake compiles the target, without a configure step. CMake recompiles
contract-first native implementations independently. A build with no changes
reruns neither generation nor compilation.

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
`LINK_LIBRARIES` reaches PRIK's private native object target with its own
syntax intact, so a linked target's compile and include usage requirements
apply to the native sources, and `debug`/`optimized` keywords and generator
expressions still select per configuration. Raw library paths retain link
behavior but do not provide CMake usage requirements.

```cmake
prik_add_module(
    physics
    SOURCES interface.c
    C_SOURCES implementation.c
    LINK_LIBRARIES debug native_math_debug optimized native_math_release
)
```

`LINK_LIBRARIES` keeps each entry's own CMake meaning: a path to an object,
archive, or shared library stays a file path, a plain name stays a library
name, and a `-Wl,...` entry stays a linker argument in the position it was
given.

`LIBRARY_DIRS` names directories that hold native libraries linked by name.
PRIK gives them to `target_link_directories()` and appends them to the
extension's `BUILD_RPATH`, so a shared native library outside the system
search path is found both when CMake links the extension and when Python
imports it from the build tree. `INSTALL_RPATH` stays under normal project
control:

```cmake
prik_add_module(
    physics
    FORTRAN_SOURCES solver.f90
    LINK_LIBRARIES nativefoo
    LIBRARY_DIRS "${CMAKE_CURRENT_LIST_DIR}/vendor/lib"
)
```

Normal Fortran sources and targets carry their link-language requirements
through CMake. For a raw archive or shared library whose language is otherwise
opaque, add `LINKER_LANGUAGE Fortran`; PRIK records that requirement in its
plan and the extension uses CMake's Fortran linker driver. This is independent
of `NATIVE_LANGUAGE`, which controls semantic-contract interpretation.

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
that same helper. `--native-linker-language fortran` emits the explicit raw
library annotation when standalone input requires the Fortran linker.

Native link inputs keep the meaning they have on the command line.
`--native-objects` and `--native-link-item object:`, `archive:`, and
`shared-library:` become `LINK_LIBRARIES` file paths written against
`CMAKE_CURRENT_LIST_DIR`, so the generated project stays readable and moves
with its inputs; `--native-library` becomes a library name and
`--native-link-item arg:` a linker argument, all in their original order.
`--native-library-dir` becomes `LIBRARY_DIRS`, which keeps the CLI meaning of
that option: a link-time search directory that is also a runtime search path
for the built extension.
