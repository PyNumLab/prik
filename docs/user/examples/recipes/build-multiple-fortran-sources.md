---
title: Build Multiple Fortran Sources
audience: users, developers
prerequisites: basic wrapper tutorial, supported compiler toolchain
related: ../verified-cookbook.md, ../../guide/fortran-wrapper.md
status: maintained
publication: draft
---

# Build Multiple Fortran Sources

Use this recipe when one Python extension needs declarations or implementations
from more than one Fortran source file.

## Build

Pass every source in compiler-valid order. The first semantic module names the
merged extension:

```bash
python3 -m x2py \
  tests/data/fortran/wrapper/first_api.f90 \
  tests/data/fortran/wrapper/second_api.f90 \
  --out-dir build/multi_api \
  --json
```

## Import

```python
import sys

import numpy as np

sys.path.insert(0, "build/multi_api")
from first_api.first_api import add_one
from first_api.second_api import double_value

assert add_one(np.int32(4)) == np.int32(5)
assert double_value(np.int32(4)) == np.int32(10)
```

## Ordering Rules

x2py does not discover missing sources and does not reorder dependencies. Put
module providers before module consumers, matching the order your compiler
expects for a direct native build.

## Generate One Contract Package

The same ordered source list can generate one combined semantic `.pyi` package:

```bash
python3 -m x2py generate --pyi \
  tests/data/fortran/wrapper/first_api.f90 \
  tests/data/fortran/wrapper/second_api.f90 \
  --out contracts/multi_api
```

`contracts/multi_api/__init__.pyi` is the only semantic wrapper input. Native
module leaves are written directly under `contracts/multi_api/`; x2py does not
create per-source subdirectories.

## Notes

- The output is one Python extension, not one extension per source file.
- Use `--out-dir` to keep all generated and native artifacts together.
- Use [Generate an editable Makefile](generate-editable-makefile.md) when you
  need your build system to run the compile/link step later.
