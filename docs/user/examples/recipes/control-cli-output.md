---
title: Control CLI Output
audience: users, developers
prerequisites: installation
related: ../../reference/cli-commands.md
status: maintained
publication: draft
---

# Control CLI Output

Use this recipe when a source file is large and the default human-readable
report is either too compact or too noisy.

## Expand Variables

Fortran variable sections are compact by default. Add `--show-vars` when you
need to inspect module variables and derived-type fields:

<!-- x2py-doc-test: run -->
```bash
python3 -m x2py parse tests/data/fortran/general/modern_pyi_example.f90 \
  --show-vars
```

## Limit Repeated Sections

Use `--print-limit` to keep long reports readable while preserving totals:

<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py parse tests/data/fortran/general/modern_pyi_example.f90 \
  --show-vars --print-limit 1
```

Expected output:

<!-- x2py-doc-test-output -->
```text
File: tests/data/fortran/general/modern_pyi_example.f90
  Modules: 1
    - module modern_math_physics (vars=2, uses=0)
      Variables: 2
        - counter:integer[0]
        ... 1 more variables
      Derived types: 3
        - type particle (fields=3, methods=0)
          Fields: 3
            - id:integer[0]
            ... 2 more fields
        ... 2 more derived types
      Procedures: 7
        - subroutine init_particle(p:type(particle)[0], pid:integer[0], mass:real(8)[0], x:real(8)[0], y:real(8)[0], z:real(8)[0])
        ... 6 more procedures
```

## Run Separate Inspection Stages

Choose one inspection stage per command. For parser details, run:

<!-- x2py-doc-test: run -->
```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90
```

## Notes

- `--show-vars` is Fortran-only.
- Use `--json` when another tool needs stable machine-readable output.

<!-- X2PY_C_DOCS_START
- `&#45;&#45;print-limit` works with human-readable C and Fortran parse reports.
X2PY_C_DOCS_END -->
