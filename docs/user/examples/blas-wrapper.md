---
title: BLAS Wrapper Example
audience: users, advanced users
prerequisites: arrays, packaging
related: lapack-wrapper.md, ../guide/arrays.md
status: maintained
publication: reviewed
---

# BLAS Wrapper Example

The repository-root [complete BLAS project](../../../examples/blas/README.md)
builds all 155 authoritative Reference BLAS sources with PRIK and f2py, imports
both generated modules, and validates all 155 discovered callable routines.

The project is executable documentation rather than a synthetic snippet. Its
explicitly named tests show the real wrapper signatures, mutated arguments,
independent numerical expectations or solve residuals, differential checks,
and preservation of input-only and unused storage. Its coverage audit fails if
a source, classification, export, test function, or outcome is omitted.

Run the whole example or focus on a family or routine:

```bash
python3 -m pytest -q examples/blas
python3 -m pytest -q examples/blas/test_level1_real.py
python3 -m pytest -q examples/blas/test_level1_real.py::test_daxpy
python3 -m pytest -q examples/blas -k dgemm
```

See the project README for source provenance and license, exact build commands,
the PRIK/f2py API differences, increments, leading dimensions, packed and
banded layouts, symmetric/Hermitian/triangular storage, tolerance policy,
source-verified representative tests, audited coverage counts, and failure
diagnostics. The example is deterministic and correctness-only.
