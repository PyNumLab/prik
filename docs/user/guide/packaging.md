---
title: Packaging
description: How to package and distribute x2py-based extensions in your projects
audience: users, packagers
prerequisites: common beginner workflow
related: distribution.md, ../reference/cli-commands.md, ../tutorials/packaging.md
status: maintained
publication: reviewed
---

# Packaging

x2py currently focuses on **building importable native extensions**. It does not yet provide a full wheel-building backend or project template. The recommended approach is a clean local project workflow.

---

## Recommended Project Layout

```
my-project/
├── src/                  # Fortran source
│   └── scale.f90
├── build/                # Generated (do not commit)
├── tests/                # Python tests
│   └── test_scale.py
└── pyproject.toml        # (optional)
```

---

## Basic Workflow

1. **Build the extension**

```bash
python3 -m x2py src/scale.f90 --out-dir build/scale
```

2. **Test it**

Create `tests/test_scale.py`:

```python
import sys
import numpy as np

sys.path.insert(0, "build/scale")
import scale

def test_scale():
    result = scale.scale(np.float64(3.0), np.float64(2.5))
    assert result == 7.5

if __name__ == "__main__":
    test_scale()
    print("✅ All tests passed")
```

Run with:

```bash
python3 -m pytest tests/ -q
```

---

## Rebuilding

When you change source code, compiler flags, or the contract:

```bash
rm -rf build/scale                    # Clean previous build
python3 -m x2py src/scale.f90 --out-dir build/scale
```

---

## Makefile Mode (Advanced)

For inspectable builds and custom flags:

```bash
python3 -m x2py generate --makefile src/scale.f90 --out-dir build/scale

make -f build/scale/Makefile.x2py
```

---

## Important Notes

- The extension name is usually taken from the first source file (you can override with `--out`).
- Generated artifacts in `build/` are **not** portable across Python versions, NumPy ABIs, or platforms.
- Keep `src/`, tests, and build commands under version control.
- Do **not** commit the `build/` directory (except in special release processes).

---

## Next

- See [Distribution](distribution.md) for sharing built extensions
- Check the [Packaging Tutorial](../tutorials/packaging.md) for more advanced setups
- For build or linking problems, see [Troubleshooting](../troubleshooting/index.md) and rerun with `--verbose`.
