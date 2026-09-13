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
own compilation and linking, once you can already
[build an extension with the CLI](building-shared-library.md). PRIK still parses
the native inputs, completes wrapper policy -- argument contracts, results, and
the ABI plan -- and generates the wrapper and any Fortran bridge sources. It
analyzes with CMake's selected C or Fortran compiler, which is why CMake mode
accepts no separate `--compiler` override: the analyzed and compiled toolchains
must agree.

The work splits across the two CMake phases. **Configure** asks PRIK only for
structure -- the generated filenames, the link driver, and any compiler ABI
flags its profile requires -- so it stays cheap however large the sources are.
**Build** runs the full PRIK pipeline exactly once, writing the wrapper, the
header, the binding-support headers, and a dependency file. What that split
means for editing sources is below, under
[regeneration and rebuilds](#regeneration-and-rebuilds).

## Minimal existing project

Install PRIK, load its CMake package, and declare the module:

```cmake
cmake_minimum_required(VERSION 3.21)

project(MyPhysics LANGUAGES C Fortran)

find_package(
    Python
    COMPONENTS Interpreter Development.Module
    REQUIRED
)

find_package(PRIK CONFIG REQUIRED)

prik_add_module(
    physics
    FORTRAN_SOURCES
        solver.f90
        matrix.f90
)
```

`prik cmake-dir` prints the directory holding PRIK's packaged CMake modules,
which is what `PRIK_DIR` names:

```bash
cmake -S . -B build -DPRIK_DIR="$(prik cmake-dir)"
cmake --build build
```

## Finding PRIK's CMake modules

`find_package(PRIK CONFIG REQUIRED)` and `include(UsePRIK)` provide the same
helper, and these routes differ only in how CMake reaches it:

| Route | The project calls | You pass |
| --- | --- | --- |
| Packaged directory | `find_package(PRIK CONFIG REQUIRED)` | `-DPRIK_DIR="$(prik cmake-dir)"` |
| Installation prefix | `find_package(PRIK CONFIG REQUIRED)` | `-DCMAKE_PREFIX_PATH="$(prik install-dir)"` |
| Module path | `include(UsePRIK)` | `-DCMAKE_MODULE_PATH="$(prik cmake-dir)"` |
| scikit-build-core | `find_package(PRIK CONFIG REQUIRED)` | nothing at all |

`PRIK_DIR` is package-specific, so setting it does not affect how other CMake
packages are found; `CMAKE_PREFIX_PATH` is the broader search path every
`find_package()` call shares.

PRIK publishes both of scikit-build-core's discovery entry points, so either
project form works there with nothing on the command line:

| Entry point | What the backend sets | What the project calls |
| --- | --- | --- |
| `cmake.root` | `PRIK_ROOT` | `find_package(PRIK CONFIG REQUIRED)` |
| `cmake.module` | `CMAKE_MODULE_PATH` | `include(UsePRIK)` |

`prik install-dir` prints the prefix this PRIK's own installation wrote its data
files under, which carries the same modules in `share/prik/cmake` and also
resolves everything else installed there. The prefix comes from that
installation's own record, so a second PRIK installed elsewhere never answers
for it. A source checkout installs nothing, and an editable install writes no
data files, so `install-dir` reports that instead of naming a prefix;
`cmake-dir` always answers.

For a [scikit-build-core](https://scikit-build-core.readthedocs.io/) wheel,
name PRIK as a build requirement:

```toml
[build-system]
requires = ["scikit-build-core>=0.10", "prik"]
build-backend = "scikit_build_core.build"
```

The backend installs PRIK into its own build environment and reads PRIK's
entry points from there, so the project keeps the same
`find_package(PRIK CONFIG REQUIRED)` it uses everywhere else, and building the
wheel takes no PRIK-specific argument:

```bash
python3 -m pip wheel .
```

The three command-line routes above use whichever `prik` the shell resolves.
scikit-build-core instead uses the PRIK installed in its build environment,
which it finds through those entry points. When the build must
match the interpreter CMake itself selected -- several environments on one
machine, or a `Python_EXECUTABLE` the project pins -- ask that interpreter,
which also needs no `-D` argument:

```cmake
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m prik cmake-dir
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
```

`prik generate --cmake` writes an equivalent block into the standalone project
it generates, which is why that project configures with a plain
`cmake -S . -B build`.

When a build cannot find PRIK, or finds one you did not expect,
`prik doctor cmake` reports what a build system would discover: the imported
package, the distribution metadata answering for it, `cmake-dir`,
`install-dir`, both entry points, and any duplicate installation or
`PYTHONPATH` entry that could answer instead. Run it through the interpreter in
question -- `"${Python_EXECUTABLE}" -m prik doctor cmake` -- to see what CMake
sees.

[`examples/cmake/`](../../../examples/cmake/README.md) is a runnable project
that builds the same module through every route, with a script that checks each
one in turn.

## Common `prik_add_module()` options

| Keyword | Purpose |
| --- | --- |
| `SOURCES` | Semantic input whose declarations PRIK wraps; also compiled, unless `NO_COMPILE_INPUT_SOURCES`. |
| `CONTRACT` | One authored semantic `.pyi` as the wrapped surface, instead of source declarations. |
| `FORTRAN_SOURCES`, `C_SOURCES` | Native implementation sources; either is also the semantic input when given alone. |
| `INCLUDE_DIRS`, `MODULE_DIRS` | Directories searched for headers and for prebuilt Fortran modules, by PRIK's analysis and by the compiled targets. |
| `LINK_LIBRARIES` | Link inputs: CMake targets, library names, file paths, or linker arguments. |
| `LIBRARY_DIRS` | Directories holding native libraries linked by name; also added to the extension's `BUILD_RPATH`. |
| `LINK_OPTIONS` | Additional options for the extension link. |
| `NATIVE_LANGUAGE`, `LINKER_LANGUAGE` | The contract's ABI language and the final CMake linker driver, stated independently. |
| `FORTRAN_FLAGS`, `C_FLAGS` | Compile options for user-owned native sources. |
| `WRAPPER_FORTRAN_FLAGS`, `WRAPPER_C_FLAGS` | Compile options for PRIK's generated sources. |
| `NO_COMPILE_INPUT_SOURCES` | `SOURCES` supplies only the public interface; the implementation arrives another way. |
| `NO_STANDARD_LOGICALS` | Disables PRIK's Intel/NVIDIA logical interoperability option. |
| `PRIK_ARGS` | Additional generation-only CLI options. |

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
`OpenMP::OpenMP_Fortran`. `LINK_LIBRARIES` reaches PRIK's private native object
target with its own syntax intact, so a linked target's compile and include
usage requirements apply to the native sources. It also keeps each entry's own
CMake meaning: a path to an object, archive, or shared library stays a file
path, a plain name stays a library name, and a `-Wl,...` entry stays a linker
argument in the position it was given. Raw library paths retain link behavior
but do not provide CMake usage requirements.

## Languages, flags, and opaque natives

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

Normal Fortran sources and targets carry their link-language requirements
through CMake. For a raw archive or shared library whose language is otherwise
opaque, add `LINKER_LANGUAGE Fortran`; PRIK records that requirement in its
plan and the extension uses CMake's Fortran linker driver. This is independent
of `NATIVE_LANGUAGE`, which controls semantic-contract interpretation.

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

`debug`/`optimized` keywords and generator expressions in `LINK_LIBRARIES`
still select usage requirements per configuration:

```cmake
prik_add_module(
    physics
    SOURCES interface.c
    C_SOURCES implementation.c
    LINK_LIBRARIES debug native_math_debug optimized native_math_release
)
```

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

## Regeneration and rebuilds

Configuration never inspects sources, so the generated file list cannot depend
on what analysis finds. PRIK names the optional compilation units up front and
always writes them: a module that needs no collision-adapter unit still gets
`<module>_adapters.c`, and a Fortran module that needs no bridge still gets
`bind_c_<module>_wrapper.f90`. An unused unit holds a small placeholder that
defines no symbol and compiles without warnings. A semantic edit then changes a
file's *contents* rather than the set of files, so editing a source never
requires re-running `cmake` to configure.

The generated wrapper sources are custom-command outputs. Changing a semantic
source, contract, included C header, or Fortran `INCLUDE` file regenerates them
before CMake compiles the target, without a configure step. CMake recompiles
contract-first native implementations independently. A build with no changes
reruns neither generation nor compilation.

Transitive semantic inputs -- a nested C header, a Fortran `INCLUDE` file, an
imported contract -- reach CMake through the dependency file PRIK writes during
generation, so changing one reruns generation on the next build. This uses
`add_custom_command(DEPFILE)`, which is why the helper requires CMake 3.21 or
newer.

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

### How CLI options map

`--native-linker-language fortran` emits the explicit raw library annotation
when standalone input requires the Fortran linker.

Native link inputs keep the meaning they have on the command line.
`--native-objects` and `--native-link-item object:`, `archive:`, and
`shared-library:` become `LINK_LIBRARIES` file paths written against
`CMAKE_CURRENT_LIST_DIR`, so the generated project stays readable and moves
with its inputs; `--native-library` becomes a library name and
`--native-link-item arg:` a linker argument, all in their original order.
`--native-library-dir` becomes `LIBRARY_DIRS`, which keeps the CLI meaning of
that option: a link-time search directory that is also a runtime search path
for the built extension.
