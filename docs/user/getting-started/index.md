---
title: Getting Started
description: Install x2py, set up compilers, and build your first Fortran-to-Python extension
audience: users
prerequisites: repository checkout
related: installation.md, verification.md
status: maintained
publication: reviewed
---

# Getting Started

This guide takes you from a fresh clone to your first working Python extension built from Fortran code.

The recommended beginner path uses the **GNU toolchain**, which offers the best compatibility right now.

---

## Beginner Path

Follow these pages in order:

1. **[Installation](installation.md)** — Install x2py and the required native compilers.
2. **[Verification](verification.md)** — Check the package, headers, and compiler.
3. **[Your First Function](first-wrapped-function.md)** — Wrap a simple scalar Fortran function.
4. **[Your First Module](first-wrapped-module.md)** — Work with Fortran modules and saved state.
5. **[Development Workflow](beginner-workflow.md)** — Learn the edit → review → build → test loop.

---

## What You Will Build

By the end of this section you will be able to write Fortran and call it cleanly from Python:

```python
import numpy as np

import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)        # 7.5
```

The first example exposes a standalone Fortran function directly on the extension.  
Later examples show how Fortran modules become Python namespaces.

---

## Next

- Start with [Installation](installation.md).
