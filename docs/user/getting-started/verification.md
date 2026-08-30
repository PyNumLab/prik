---
title: Verification
description: Verify that PRIK, NumPy, and the native toolchain are working correctly
audience: users, contributors
prerequisites: installation
related: first-wrapped-function.md
status: maintained
publication: reviewed
---

# Verification

After installation, check the Python package, required headers, and compiler.
The next page uses them together to build a complete extension.

---

## 1. Verify the Installed Package

Run these commands in your activated virtual environment:

```bash
# Check prik and NumPy
python3 -c "from importlib.metadata import version; import prik, numpy; print('prik:', version('prik')); print('NumPy:', numpy.__version__)"

# Check the command-line interface
python3 -m prik --help
```

---

## 2. Verify the Required Headers

Print the Python and NumPy header directories:

```bash
python3 -c "import sysconfig; print(sysconfig.get_path('include'))"
python3 -c "import numpy; print(numpy.get_include())"
```

Both commands should print existing directories.

---

## 3. Verify Your Toolchain

For a C-only build, check the C compiler you plan to use. The default is `cc`:

```bash
cc --version
```

For the recommended GNU Fortran path, check both compilers in the pair:

```bash
gfortran --version
gcc --version
```

For Intel IFX or LLVM Flang, check both commands in the pair:

```bash
# Intel
ifx --version
icx --version

# LLVM
flang --version
clang --version
```

Fortran builds need both commands in the selected pair. A C-only build needs
only its C compiler. If a required command is missing, install it or add its
`bin` directory to `PATH`.

---

## Troubleshooting Guide

| Failure Type                    | Recommended Action                          |
|--------------------------------|---------------------------------------------|
| Cannot import PRIK / NumPy     | Check active virtual environment            |
| A header directory is missing  | Reinstall Python development files or NumPy |
| Compiler not found             | Fix `PATH` or install the compiler required by your selected path |

---

## Next

- Build and call [Your First Wrapped Function](first-wrapped-function.md). That
  example is the end-to-end verification.
