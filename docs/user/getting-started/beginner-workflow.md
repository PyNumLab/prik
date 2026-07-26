---
title: Common Beginner Workflow
description: Recommended development loop — edit, review contract, build, test, and rebuild
audience: users
prerequisites: first wrapped module
related: ../tutorials/basic-wrapper.md, ../examples/verified-cookbook.md, ../reference/cli-commands.md
status: maintained
publication: reviewed
---

# Common Beginner Workflow

Now that you have built individual examples, here is a clean, repeatable workflow you can use for your own projects.
The example project continues to use `scale.f90`.

---

## Recommended Project Layout

```
my-project/
├── src/
│   └── scale.f90
├── build/              # ← Generated, do not commit
├── tests/
│   └── test_scale.py
└── contracts/          # Optional: edited semantic contracts
```

Keep `src/` and `tests/` under version control. Never commit the `build/` folder.

---

## 1. Review the Contract First

Before building, always inspect the generated contract:

```bash
python3 -m x2py generate --pyi src/scale.f90
```

This shows you exactly what Python signatures and dtypes x2py expects.

---

## 2. Build the Extension

```bash
python3 -m x2py src/scale.f90 --out-dir build/scale
```

Use `--verbose` if you want to see the exact compiler and linker commands.

---

## 3. Write a Small Smoke Test

Create `tests/test_scale.py`:

```python
import sys
import numpy as np

sys.path.insert(0, "build/scale")
import scale

def test_scale_function():
    result = scale.scale(np.float64(3.0), np.float64(2.5))
    assert result == 7.5

if __name__ == "__main__":
    test_scale_function()
    print("✅ Test passed")
```

Run it with:

```bash
python3 -m pytest tests/test_scale.py -q
# or simply:
python3 tests/test_scale.py
```

---

## 4. Clean Rebuild When Needed

When you change the Fortran source or want a completely clean build:

```bash
rm -rf build/scale
python3 -m x2py src/scale.f90 --out-dir build/scale
```

---

## 5. Advanced: Editing the Semantic Contract (Optional)

Only do this after you are comfortable with the basic workflow:

```bash
python3 -m x2py generate --pyi src/scale.f90 --out contracts
```

Editing contracts is powerful but adds complexity. See **Editing Semantic .pyi Contracts** in the User Guide when you're ready.

---

## Summary of the Workflow

1. Edit Fortran source in `src/`
2. Review contract with `generate --pyi`
3. Build with explicit `--out-dir`
4. Test with a Python smoke test
5. Clean rebuild when necessary (`rm -rf build/...`)

---

## Next

- Explore the full [User Guide](../guide/index.md)
- Check the [Language Feature Matrix](../language-support/feature-matrix.md)
- Look at the [Verified Cookbook](../examples/verified-cookbook.md) for more examples

---

**Troubleshooting**
Use `--verbose` on build failures.
Always compare failing calls with the generated contract.
