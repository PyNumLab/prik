---
title: Getting Started
description: Install PRIK and build your first Python extension from Fortran or C code
audience: users
prerequisites: none
related: installation.md, verification.md
status: maintained
publication: reviewed
---

# Getting Started

This guide takes you from a fresh environment to your first working Python
extension. Choose Fortran or C for the native source; both paths generate a
semantic `.pyi` contract, build an extension, and call the same Python API.

---

## Beginner Path

Follow these pages in order:

1. **[Installation](installation.md)** — Install PRIK and the required native compilers.
2. **[Verification](verification.md)** — Check the package, headers, and your selected toolchain.
3. **[Your First Function](first-wrapped-function.md)** — Build the same scalar function from Fortran or C.
4. **[Development Workflow](beginner-workflow.md)** — Repeat the edit → review → build → test loop.

---

## What You Will Build

In [Your First Function](first-wrapped-function.md), you will create either
`scale.f90` or `scale.c`. Both paths build a Python extension named `scale`
with the same call:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)        # 7.5
```

After this first build, continue with the [Fortran User
Guide](../guide/wrapping-functions.md) or the [C User Guide](../guide/c/index.md).
Fortran modules and their Python namespaces are covered in [Wrapping
Modules](../guide/wrapping-modules.md).

---

## Next

**Ready? Start with [Installation](installation.md).**
