---
title: Build And Import With The CLI
audience: users
prerequisites: basic wrapper tutorial, supported compiler toolchain
related: ../verified-cookbook.md, ../../reference/fortran-wrapper.md
status: maintained
publication: draft
---

# Build And Import With The CLI

Use this recipe when you want x2py to compile a Fortran source file into an
importable Python extension from the command line.

## Input

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

## Build

```bash
python3 -m x2py tests/data/fortran/wrapper/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

Recognizable Fortran sources select the wrapper build when no inspection stage
is selected, so this is equivalent:

```bash
python3 -m x2py tests/data/fortran/wrapper/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

## Import

```python
import sys

import numpy as np

sys.path.insert(0, "build/fruntime_abi")
import fruntime_abi_f90

result = fruntime_abi_f90.scale(np.float64(3.0), np.float64(2.5))
print(result)  # 7.5
```

## Notes

- Use `--out-dir` to keep generated sources and build artifacts in one place.
- Use `--verbose` to print compiler and linker commands.
- Exact NumPy scalar dtypes are part of the native ABI contract.

<!-- X2PY_C_DOCS_START
- Runtime wrapping of user-supplied C sources is not implemented by this path.
X2PY_C_DOCS_END -->
