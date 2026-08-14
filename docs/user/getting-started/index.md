---
title: Getting Started
description: Install PRIK, set up compilers, and build your first Fortran-to-Python extension
audience: users
prerequisites: none
related: installation.md, verification.md
status: maintained
publication: reviewed
---

# Getting Started

This guide takes you from a fresh environment to your first working Python
extension built from Fortran code.

Start with GNU (`gfortran` and `gcc`), tested on Linux and macOS. LLVM Flang
is tested on both platforms; Intel IFX is tested on Linux. See
[Installation](installation.md#compiler-toolchains) for every compiler option.

---

## Beginner Path

Follow these pages in order:

1. **[Installation](installation.md)** — Install prik and the required native compilers.
2. **[Verification](verification.md)** — Check the package, headers, and compiler.
3. **[Your First Function](first-wrapped-function.md)** — Wrap a simple scalar Fortran function.
4. **[Your First Module](first-wrapped-module.md)** — Work with Fortran modules and saved state.
5. **[Development Workflow](beginner-workflow.md)** — Learn the edit → review → build → test loop.

---

## What You Will Build

In [Your First Function](first-wrapped-function.md), you will create
`scale.f90`, build it as a Python extension named `scale`, and call its
`scale` function:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)        # 7.5
```

The first example exposes a standalone Fortran function directly on the extension.
Later guides show how Fortran modules become Python namespaces and derived
types become Python classes.

---

## Next

**Ready? Start with [Installation](installation.md).**
