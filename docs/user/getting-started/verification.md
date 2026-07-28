---
title: Verification
description: Verify that x2py, NumPy, and the native toolchain are working correctly
audience: users, contributors
prerequisites: installation
related: first-wrapped-function.md, ../troubleshooting/index.md, ../reference/cli-commands.md
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
# Check x2py and NumPy
python3 -c "from importlib.metadata import version; import x2py, numpy; print('x2py:', version('x2py')); print('NumPy:', numpy.__version__)"

# Check the command-line interface
python3 -m x2py --help
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

## 3. Verify the Compiler

```bash
gfortran --version
```

The output should identify GNU Fortran. If the command is missing, install
`gfortran` or add it to `PATH`.

---

## Troubleshooting Guide

| Failure Type                    | Recommended Action                          |
|--------------------------------|---------------------------------------------|
| Cannot import x2py / NumPy     | Check active virtual environment            |
| A header directory is missing  | Reinstall Python development files or NumPy |
| Compiler not found             | Fix `PATH` or reinstall gfortran           |

---

## Next

- Build and call [Your First Wrapped Function](first-wrapped-function.md). That
  example is the end-to-end verification.
- For detailed help, use [Troubleshooting](../troubleshooting/index.md).
