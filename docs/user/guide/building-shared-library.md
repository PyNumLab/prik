---
title: Building the Shared Library
description: How to build and import a Python extension shared library with x2py
audience: users
prerequisites: common beginner workflow
related: ../reference/cli-commands.md, ../examples/recipes/build-and-import-cli.md, ../examples/recipes/build-multiple-fortran-sources.md, ../examples/recipes/generate-editable-makefile.md
status: maintained
publication: reviewed
---

# Building the Shared Library

x2py turns Fortran source into a Python extension module. The final module is a
native shared library that Python imports directly.

## Build

Run x2py on the source file and choose a build directory:

```bash
python3 -m x2py src/scale.f90 --out-dir build/scale
```

The shared library and the generated build files are written to
`build/scale`. By default, the module name comes from the source filename. Use
`--out` to choose it explicitly:

```bash
python3 -m x2py src/scale.f90 --out scale_api --out-dir build/scale_api
```

## Import

Add the build directory to Python's search path, then import the module by its
name:

```python
import sys

sys.path.insert(0, "build/scale_api")

import scale_api
```

The shared-library filename includes a platform- and Python-specific suffix,
but the import uses only the module name.

## Multiple Source Files

Pass source files in the order required by the compiler. Choosing the module
name explicitly keeps the result clear:

```bash
python3 -m x2py src/types.f90 src/solver.f90 \
  --out solver \
  --out-dir build/solver
```

x2py preserves the given order. It does not discover source dependencies or
external libraries automatically.

## Compatibility

The shared library is not universal. It must match the target machine's
operating system and architecture, Python and NumPy, and required compiler
libraries. Rebuilding it on the target machine is the safest choice.

## Next

- Follow the complete [build and import recipe](../examples/recipes/build-and-import-cli.md).
- For several files, see the [multiple-source recipe](../examples/recipes/build-multiple-fortran-sources.md).
- To inspect or customize the build, [generate an editable Makefile](../examples/recipes/generate-editable-makefile.md).
- For build or import failures, see [Troubleshooting](../troubleshooting/index.md)
  and rerun the build with `--verbose`.
