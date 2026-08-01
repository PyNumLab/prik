---
title: Installation
description: Install PRIK from PyPI and choose a Fortran compiler
audience: users, contributors
prerequisites: Python 3.10 or newer
related: verification.md
status: maintained
publication: reviewed
---

# Installation

Install PRIK from the Python Package Index with `pip`. Building Python
extensions also requires a Fortran compiler, its matching C compiler, and
standard build tools.

---

## Supported Python Versions

prik requires **Python 3.10 or newer**.
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

On **macOS** with Homebrew:

```bash
brew install gcc@13
```

Homebrew provides versioned commands such as `gfortran-13` and `gcc-13`.

## Compiler Toolchains

`gfortran` is the default. Use `--compiler` to choose another option. Install
the matching C compiler shown below as well.

| Fortran compiler | Required C compiler | Test status |
| --- | --- | --- |
| `gfortran` | `gcc` | Default; tested on Linux and macOS |
| `ifx` | `icx` | Tested on Linux with version 2026.1.1 |
| `flang` | `clang` | Tested on Linux and macOS with version 22.1.8 |
| `ifort` | `icx` | Recognized; not routinely tested |
| `nvfortran` | `nvc` | Recognized; not yet tested |
| `pgfortran` | `pgcc` | Legacy option; not yet tested |

The versions shown are the versions currently tested, not minimum
requirements. For the best-tested experience, use GNU, IFX, or Flang.

---

## User Installation

Create a virtual environment and install the published `prik` distribution:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install prik
```

This installs PRIK and its runtime dependencies, including NumPy. Verify both
supported command entry points:

```bash
prik --version
prik --help
python3 -m prik --help
```

---

## Contributor Installation

For an editable checkout with the QA tools, clone the repository first:

```bash
git clone https://github.com/PyNumLab/prik.git
cd prik
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[qa]"
```

---

## Platform Support

| Platform | Current status |
| --- | --- |
| Ubuntu Linux x86-64 | Tested with GNU Fortran, Intel IFX, and LLVM Flang |
| Other Linux | Expected to work; compiler coverage varies |
| macOS 15 on Apple Silicon | Full suite with GNU Fortran 13; smoke tests with LLVM Flang |
| Windows | Not yet supported |

---

## Next

- Go to [Verification](verification.md) to check the installation and compiler.
