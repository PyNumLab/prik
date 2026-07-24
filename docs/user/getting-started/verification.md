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

After installation, verify the Python package, contract generation, and native build toolchain separately. This makes debugging much easier.

---

## 1. Verify the Installed Package

Run these commands in your activated virtual environment:

```bash
# Check x2py and NumPy
python3 -c "from importlib.metadata import version; import x2py, numpy; print('x2py:', version('x2py')); print('NumPy:', numpy.__version__)"

# Check CLI entrypoint
python3 -m x2py --help
```

---

## 2. Verify Contract Generation

Use the `scale.f90` file from the homepage example.

Run this command in the directory containing `scale.f90`:

```bash
python3 -m x2py generate --pyi scale.f90
```

You should see a clean `.pyi`-style contract. This confirms parsing, semantic analysis, and type probing work correctly.

---

## 3. Verify Native Build Toolchain

First, check the compiler:

```bash
gfortran --version
```

Then build the extension:

```bash
python3 -m x2py scale.f90 --out-dir build/verify
```

This should create an importable `scale` module inside `build/verify`.

Test it:

```python
import sys
import numpy as np

sys.path.insert(0, "build/verify")
import scale

result = scale.scale(np.float64(3.0), np.float64(2.5))
print(result)        # Should print 7.5
```

---

## 4. Inspect Generated Files (Optional)

You can also inspect the build programmatically:

```python
from x2py import build_fortran_extension

build = build_fortran_extension("scale.f90", output_dir="build/verify")

print("Compiled:", build.compiled)
print("Shared library:", build.shared_library)
print("Output directory:", build.output_dir)
```

For detailed output when something fails, add `--verbose`:

```bash
python3 -m x2py scale.f90 --out-dir build/verify --verbose
```

---

## Troubleshooting Guide

| Failure Type                    | Recommended Action                          |
|--------------------------------|---------------------------------------------|
| Cannot import x2py / NumPy     | Check active virtual environment            |
| `x2py --help` works but `.pyi` fails | Check diagnostics and reference section   |
| Compiler not found             | Fix `PATH` or reinstall gfortran           |
| Build / linking fails          | Run with `--verbose`                        |
| Builds but import/call fails   | Compare against generated contract          |

---

## Next

- Proceed to [Your First Wrapped Function](first-wrapped-function.md).
- For detailed help, use [Troubleshooting](../troubleshooting/index.md).
