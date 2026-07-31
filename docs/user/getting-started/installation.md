---
title: Installation
description: Install x2py from source and choose a Fortran compiler
audience: users, contributors
prerequisites: Python 3.10 or newer, repository checkout
related: verification.md
status: maintained
publication: reviewed
---

# Installation

x2py is currently installed from a local source checkout. Building Python
extensions also requires a Fortran compiler, its matching C compiler, and
standard build tools.

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

The beginner path uses:

- `gfortran` (GNU Fortran compiler)
- `gcc` (normally provided by `build-essential`)
- `python3-dev` (Python development headers)
- NumPy (includes required development files)
- `build-essential` (linker and build tools)

On **Ubuntu / Debian**:

```bash
sudo apt-get update
sudo apt-get install build-essential gfortran python3-dev
```

## Compiler Toolchains

`gfortran` is the default. Use `--compiler` to choose another option. Install
the matching C compiler shown below as well.

| Fortran compiler | Required C compiler | Test status |
| --- | --- | --- |
| `gfortran` | `gcc` | Default; fully tested on Linux |
| `ifx` | `icx` | Tested on Linux with version 2026.1.1 |
| `flang` | `clang` | Tested on Linux with version 22.1.8 |
| `ifort` | `icx` | Recognized; not routinely tested |
| `nvfortran` | `nvc` | Recognized; not yet tested |
| `pgfortran` | `pgcc` | Legacy option; not yet tested |

The versions shown are the versions currently tested, not minimum
requirements. For the best-tested experience, use GNU, IFX, or Flang.

---

## User Installation

Clone the repository:

```bash
git clone https://github.com/PyNumLab/x2py.git
cd x2py
```

Create a virtual environment and install x2py:

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

| Platform | Current status |
| --- | --- |
| Ubuntu Linux x86-64 | Tested with GNU Fortran, Intel IFX, and LLVM Flang |
| Other Linux | Expected to work; compiler coverage varies |
| macOS | Not yet in CI matrix |
| Windows | Not yet supported |

---

## Next

- Go to [Verification](verification.md) to check the installation and compiler.
