---
title: Distribution
description: How to share x2py-based extensions with other users and environments
audience: users, packagers
prerequisites: packaging
related: packaging.md, ../troubleshooting/platform-specific-issues.md, ../getting-started/installation.md
status: maintained
publication: reviewed
---

# Distribution

x2py currently produces **platform-specific native extensions**. There is no stable, universal wheel format yet. The most reliable way to distribute your code is to share the **source + build recipe**.

---

## Recommended Distribution Approach: Source + Build Instructions

Distribute your project like this:

```
my-project/
├── src/
│   └── mycode.f90
├── tests/
│   └── test_mycode.py
├── BUILDING.md          # ← Important!
├── requirements.txt
└── README.md
```

**`BUILDING.md`** should clearly document:

```bash
# Build the extension
python3 -m x2py src/mycode.f90 --out-dir build/mycode

# Run tests
python3 -m pytest tests/
```

Include:
- Required Python and NumPy versions
- Compiler (e.g. gfortran) and version
- Any extra compiler flags or libraries
- Supported platforms

---

## Sharing Prebuilt Extensions

You **can** share a built extension, but it is **highly platform-specific**.

Consumers must match:
- Operating system and architecture
- Python version and implementation
- NumPy ABI
- Compiler ABI and runtime libraries

Even small differences (e.g. different Python patch version or NumPy build) can cause import or runtime failures.

**Best practice**: Always include the source and build instructions even if you also provide a prebuilt binary.

---

## Key Limitations

- No official wheel-building support yet
- No automatic bundling of native dependencies
- No cross-platform guarantees
- Extensions are tied to the exact Python + NumPy + compiler combination used to build them

---

## Release Checklist

Before releasing:
1. Generate and review the semantic `.pyi` contract
2. Build from a clean directory
3. Run all tests with realistic inputs
4. Document supported platforms and dependencies clearly
5. Test on target environments when possible

---

## Next

- See [Platform-Specific Issues](../troubleshooting/platform-specific-issues.md) for common distribution problems.
