---
title: Common Beginner Workflow
description: Recommended development loop — edit, review contract, build, test, and rebuild
audience: users
prerequisites: first wrapped function
related: ../guide/index.md, ../guide/c/index.md
status: maintained
publication: reviewed
---

# Common Beginner Workflow

Use this loop for a Fortran or C project: edit the source, review its Python
interface, build, and test.

---

## Recommended Project Layout

This layout continues with `scale.f90` or `scale.c` from [First Wrapped
Function](first-wrapped-function.md):

```
my-project/
├── src/
│   └── scale.f90       # or scale.c
├── build/              # ← Generated, do not commit
├── tests/
│   └── test_scale.py
└── contracts/          # Optional edited semantic contracts
```

Keep `src/` and `tests/` under version control. Never commit the `build/` folder.

---

## 1. Edit and Review

Edit the native source, then preview the generated Python interface with the
command for your language.

Fortran:

```bash
python3 -m prik generate --pyi src/scale.f90
```

C:

```bash
python3 -m prik generate --pyi --language c src/scale.c
```

Check the function names, arguments, result types, and required NumPy dtypes.
This review is especially useful after changing a public declaration.

---

## 2. Build the Extension

Fortran:

```bash
python3 -m prik src/scale.f90 --out scale --out-dir build/scale
```

C:

```bash
python3 -m prik --language c src/scale.c \
  --compiler cc \
  --out scale \
  --out-dir build/scale
```

Rerun the same command after source changes. Add `--verbose` only when you need
the compiler and linker details.

---

## 3. Write a Small Test

Create `tests/test_scale.py`:

```python
import sys

import numpy as np

sys.path.insert(0, "build/scale")
import scale

def test_scale_function():
    result = scale.scale(np.float64(3.0), np.float64(2.5))
    assert result == 7.5
```

Run it with:

```bash
python3 -m pytest tests/test_scale.py -q
```

---

## 4. Optionally Edit the Contract

Save the generated contract when you want to change the Python interface.
Create the optional directory from the layout above first:

```bash
mkdir -p contracts
```

Fortran writes a contract package:

```bash
python3 -m prik generate --pyi src/scale.f90 --out contracts/scale
```

Edit `contracts/scale/scale.pyi`, then build through its package entry:

```bash
python3 -m prik contracts/scale/__init__.pyi \
  --native-fortran-sources src/scale.f90 \
  --out scale \
  --out-dir build/scale-edited
```

C writes one contract file:

```bash
python3 -m prik generate --pyi --language c src/scale.c \
  --out contracts/scale.pyi
```

Edit `contracts/scale.pyi`, then build it with the C implementation:

```bash
python3 -m prik --language c contracts/scale.pyi \
  --native-c-sources src/scale.c \
  --compiler cc \
  --out scale \
  --out-dir build/scale-edited
```

Use this form instead of the source build in step 2 when the edited contract
should control the wrapper. The `.pyi` controls the Python surface; the native
source still supplies the implementation. Keep its native symbol names, types,
rank, and argument order accurate.

The User Guide introduces small edits next to the feature they affect.

Use [`.pyi` Format](../reference/pyi-format.md) to understand the generated
project, declarations, and keywords. Use [Editing `.pyi`
Contracts](../reference/pyi-contracts/index.md) to find the supported recipe
for the change you want to make.

---

## 5. Diagnose a Failure

If a build fails, rerun it with `--verbose`. If a Python call fails, compare
the arguments with the generated contract. Use a clean output directory only
when you need to rule out stale build files.

---

## Next

- Continue with the [User Guide](../guide/index.md).
- For Fortran modules, see [Wrapping Modules](../guide/wrapping-modules.md).
- For C pointers, arrays, strings, and outputs, see the [C User
  Guide](../guide/c/index.md).
