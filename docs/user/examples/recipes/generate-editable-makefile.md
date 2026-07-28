---
title: Generate An Editable Makefile
audience: users, developers
prerequisites: basic wrapper tutorial, GNU Make, supported compiler toolchain
related: ../verified-cookbook.md, ../../reference/fortran-wrapper.md
status: maintained
publication: draft
---

# Generate An Editable Makefile

Use this recipe when you want x2py to generate wrapper sources and
`Makefile.x2py`, then let your build environment run the compile and link
steps. For semantic `.pyi` builds, x2py also writes `x2py-build.json`; that
manifest is the source of truth used to generate the Makefile.

## Generate The Build Files

```bash
python3 -m x2py generate --makefile tests/data/fortran/wrapper/fruntime_abi_f90.f90 \
  --out-dir build/fruntime_abi \
  --json
```

This writes generated wrapper sources, the header-only native binding support, dependency files, and
`build/fruntime_abi/Makefile.x2py`.

For a semantic `.pyi` contract with native implementation sources, use the same
mode with explicit native inputs:

```bash
python3 -m x2py generate --makefile contracts/fruntime_abi_f90.pyi \
  --native-fortran-sources native/fruntime_abi_f90.f90 \
  --native-compile-flags="-O3 -fopenmp" \
  --out-dir build/fruntime_abi \
  --json
```

This writes `build/fruntime_abi/x2py-build.json` first and then projects
`build/fruntime_abi/Makefile.x2py` from that manifest.

## Build With GNU Make

```bash
make -f build/fruntime_abi/Makefile.x2py -j4 \
  X2PY_FFLAGS=-O3 \
  X2PY_CFLAGS=-O3 \
  X2PY_LDFLAGS=-O3
```

The generated Makefile exposes these variables for local override:

| Variable | Meaning |
| --- | --- |
| `FC` | Fortran compiler |
| `X2PY_LD` | Link command |
| `X2PY_FFLAGS` | Extra Fortran compiler flags |
| `X2PY_LDFLAGS` | Extra linker flags |

<!-- X2PY_C_DOCS_START
| `CC` | C compiler |
| `X2PY_CFLAGS` | Extra C compiler flags |
X2PY_C_DOCS_END -->

## Notes

- `--makefile` generates the build plan without compiling immediately.
- `--makefile` selects the editable wrapper-build mode directly.
- `--makefile` and `--verbose` are mutually exclusive.
- `.pyi` Makefile generation is replayable through
  `python3 -m x2py generate --makefile --build-manifest build/fruntime_abi/x2py-build.json`
  or buildable through
  `python3 -m x2py --build-manifest build/fruntime_abi/x2py-build.json`.
- User Fortran sources remain in caller-provided order. Generated independent
  objects may be built in parallel by Make.
