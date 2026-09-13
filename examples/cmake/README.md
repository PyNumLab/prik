# Build a PRIK Extension from CMake

This example builds one small Fortran module into an importable extension once
per route a CMake project can use to find PRIK's packaged helper.

The [CMake builds guide](../../docs/user/guide/cmake.md) documents the routes
and the full `prik_add_module()` surface.

## Project layout

| File | Role |
| --- | --- |
| [`kernel.f90`](kernel.f90) | Fortran module with one diffusion step and one reduction |
| [`CMakeLists.txt`](CMakeLists.txt) | One `prik_add_module()` call; `PRIK_DISCOVERY` selects `include` or `find-package` |
| [`pyproject.toml`](pyproject.toml) | The same project as a scikit-build-core wheel |
| [`check_discovery_routes.sh`](check_discovery_routes.sh) | Builds and calls the extension once per route |

| Route | What the project calls | What you pass |
| --- | --- | --- |
| `module-path` | `include(UsePRIK)` | `-DCMAKE_MODULE_PATH="$(prik cmake-dir)"` |
| `find-package-dir` | `find_package(PRIK CONFIG REQUIRED)` | `-DPRIK_DIR="$(prik cmake-dir)"` |
| `install-prefix` | `find_package(PRIK CONFIG REQUIRED)` | `-DCMAKE_PREFIX_PATH="$(prik install-dir)"` |
| `scikit-build-core` | `include(UsePRIK)` | nothing: the build backend reads PRIK's `cmake.module` entry point |

## Requirements

CMake 3.21 or newer, a Fortran and C compiler, Python development headers, and
NumPy. On Ubuntu:

```console
sudo apt-get update
sudo apt-get install --yes build-essential gfortran cmake ninja-build python3-dev
python3 -m pip install "numpy>=2.1"
```

Run the remaining commands from the repository root.

## Quick start

```bash
PYTHONPATH=. examples/cmake/check_discovery_routes.sh
```

`PYTHONPATH` lets the interpreter CMake drives import PRIK from this checkout;
drop it when PRIK is installed. Each route prints its own line, and a route
whose prerequisite is missing is reported rather than failed:

```console
    diffuse([0.0, 1.0, 0.0], 0.25) -> [0.0, 0.5, 0.0]
OK               module-path
    diffuse([0.0, 1.0, 0.0], 0.25) -> [0.0, 0.5, 0.0]
OK               find-package-dir
SKIPPED          install-prefix       PRIK is not installed; run this route against an installed PRIK
    installed wheel: diffuse -> [0.0, 0.5, 0.0]
OK               scikit-build-core
skipped: install-prefix
```

Name routes to run a subset, and set `PRIK_EXAMPLE_PYTHON` to choose the
interpreter that answers for PRIK and builds the extension:

```bash
PYTHONPATH=. examples/cmake/check_discovery_routes.sh module-path find-package-dir
PRIK_EXAMPLE_PYTHON=/path/to/venv/bin/python examples/cmake/check_discovery_routes.sh install-prefix
```

## Calling the extension

The built extension is `heat`, and the Fortran module `kernel` is a namespace
inside it:

```python
import numpy

import heat

values = numpy.array([0.0, 1.0, 0.0])
stepped = heat.kernel.diffuse(values, numpy.float64(0.25))  # [0.0, 0.5, 0.0]
conserved = heat.kernel.total(values)                       # 1.0
```

Scalar arguments take NumPy scalars, which is PRIK's ordinary calling
convention rather than anything specific to CMake builds.
