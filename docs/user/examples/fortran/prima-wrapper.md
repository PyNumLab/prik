---
title: Build and Validate PRIMA with PRIK
audience: users, advanced users
prerequisites: arrays, callbacks, packaging
related: ../../guide/callbacks.md, ../../reference/cli-commands.md
status: maintained
publication: reviewed
---

# Build and Validate PRIMA with PRIK

This example builds the checked-in [libPRIMA](https://github.com/libprima/prima)
Fortran source as a static library, generates a contract for five selected
optimization solvers, and links one Python extension against that library.

Install PRIK with its example dependencies, CMake, and GNU Fortran. From the
repository root, build the extension and run its numerical checks:

```bash
python3 -m pip install -e ".[qa]"
source examples/fortran/prima/build_all.sh
python3 -m pytest -q examples/fortran/prima/tests
```

The Python module exposes `bobyqa_mod.bobyqa`, `cobyla_mod.cobyla`,
`lincoa_mod.lincoa`, `newuoa_mod.newuoa`, and `uobyqa_mod.uobyqa`. For example:

```python
import numpy as np
import prik_prima

x = np.asfortranarray(np.array([3.0, 0.0], dtype=np.float64))

def objective(values, result):
    result[...] = (values[0] - 1.0) ** 2 + (values[1] + 2.0) ** 2

prik_prima.uobyqa_mod.uobyqa(objective, x, maxfun=np.int32(100))
np.testing.assert_allclose(x, [1.0, -2.0], atol=2e-3, rtol=0)
```

CMake compiles the 55 source files once into `libprimaf.a`. PRIK reads those
sources with [`export_symbols.txt`](../../../../examples/fortran/prima/export_symbols.txt),
emits the selected `.pyi` contracts and their callback dependency, then links
the wrapper to the archive. The contract's `__all__` controls the Python
surface. See the [project README](../../../../examples/fortran/prima/README.md)
for the source version and build details.

The **Real Libraries Portability** workflow runs this build and its numerical
tests with Python 3.12 and GNU Fortran 13 on Linux x86-64, Linux ARM64, macOS
Intel, and macOS ARM64.
