---
title: Compiler Issues
audience: users, contributors
prerequisites: verification
related: ../getting-started/installation.md, ../guide/building-shared-library.md
status: maintained
publication: reviewed
---

# Compiler Issues

For a Fortran build, PRIK uses the Fortran compiler passed to `--compiler` and
its matching C compiler. A direct-C build uses the selected C compiler without
requiring Fortran, unless explicit Fortran implementation sources make the
final link mixed-language.

## Direct-C Builds

Select the C lane and its compiler explicitly when the input suffix does not
already determine the language:

```bash
python3 -m prik api.c --language c --compiler clang \
  --native-c-compile-flags="-O3 -std=c11" \
  --out-dir build/api
```

`--native-c-compile-flags` applies to user C implementation sources;
`--wrapper-c-flags` applies to the generated CPython binding and any selected
collision forwarder. Use [C Support](../language-support/c-support.md) to decide
whether a declaration is in the direct-C subset before debugging the compiler.

## Verify A Fortran Compiler Pair

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
matching C compiler is missing, PRIK stops with an explicit error rather than
using an incompatible compiler.

## Unsupported Compiler Family

If the name is not recognized, PRIK lists the accepted compiler families. Use
the compiler's standard executable name or choose another listed option.

## Compiler-Specific Flags

Use `--native-compile-flags` for user-supplied native Fortran sources,
`--wrapper-fortran-flags` for the generated Fortran wrapper, and
`--wrapper-c-flags` for the generated Python binding. Do not mix flags from
different compiler families.

Use `--verbose` to show the build commands. The first failed command usually
reveals which step needs attention.
