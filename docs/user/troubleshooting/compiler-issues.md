---
title: Compiler Issues
audience: users, contributors
prerequisites: verification
related: build-issues.md, platform-specific-issues.md
status: maintained
publication: reviewed
---

# Compiler Issues

prik uses the Fortran compiler passed to `--compiler` and its matching C
compiler to build the Python extension.

## Verify Both Compilers

Check both executables from the selected pair:

```bash
gfortran --version
gcc --version
```

For Intel use `ifx` with `icx`; for LLVM use `flang` with `clang`. See
[Compiler Toolchains](../getting-started/installation.md#compiler-toolchains)
for all options.

## Compiler Not Found

Pass an executable name available on `PATH`, or use an absolute path:

```bash
python3 -m prik solver.f90 \
  --compiler /opt/toolchain/bin/flang \
  --out-dir build/solver
```

Versioned names such as `gfortran-13` and `flang-22` are recognized. If the
matching C compiler is missing, prik stops with an explicit error rather than
using an incompatible compiler.

## Unsupported Compiler Family

If the name is not recognized, prik lists the accepted compiler families. Use
the compiler's standard executable name or choose another listed option.

## Compiler-Specific Flags

Use `--native-compile-flags` for user-supplied native Fortran sources,
`--wrapper-fortran-flags` for the generated Fortran wrapper, and
`--wrapper-c-flags` for the generated Python binding. Do not mix flags from
different compiler families.

Use `--verbose` to show the build commands. The first failed command usually
reveals which step needs attention.
