---
title: Installation
description: Install x2py from source and set up the native GNU toolchain
audience: users, contributors
prerequisites: Python 3.10 or newer, repository checkout
related: verification.md, ../troubleshooting/installation-issues.md, ../../developer/quality-assurance.md
status: maintained
publication: reviewed
---

# Installation

x2py is currently installed from a local source checkout. Building Python
extensions also requires GNU Fortran and standard build tools.

---

## Supported Python Versions

x2py requires **Python 3.10 or newer**.  
The project is regularly tested on Python 3.10, 3.11, and 3.12.

Check your Python version first:

```bash
python3 --version
```

---

## Native Prerequisites

Install these packages before building wrappers:

- `gfortran` (GNU Fortran compiler)
- `python3-dev` (Python development headers)
- NumPy (includes required development files)
- `build-essential` (linker and build tools)

On **Ubuntu / Debian**:

```bash
sudo apt-get update
sudo apt-get install build-essential gfortran python3-dev
```

---

## User Installation

From the root of the cloned repository, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

This installs x2py in editable mode along with its runtime dependencies (including NumPy).

---

## Contributor Installation

If you are contributing code or running tests, also install the QA tools:

```bash
python3 -m pip install -e ".[qa]"
```

---

## Platform Support

| Platform           | Current Status                          |
|--------------------|-----------------------------------------|
| Ubuntu Linux       | CI-verified (Ubuntu 24.04 + gfortran-13) |
| Other Linux        | Expected to work with GNU tools         |
| macOS              | Not yet in CI matrix                    |
| Windows            | Not yet supported                       |

---

## Next

- Go to [Verification](verification.md) to check the installation and compiler.
- If setup fails, see [Installation Issues](../troubleshooting/installation-issues.md).
