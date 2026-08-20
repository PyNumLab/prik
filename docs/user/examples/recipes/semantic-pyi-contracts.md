---
title: Work With Semantic .pyi Contracts
audience: users, advanced users
prerequisites: semantic .pyi format
related: ../../reference/semantic-pyi-format.md
status: maintained
publication: draft
---

# Work With Semantic .pyi Contracts

Use this recipe when source facts are not enough and you need an editable
semantic contract.

## Generate A Starter Contract

```bash
python3 -m prik generate --pyi tests/fortran/infrastructure/parsing/fixtures/general/basic_subroutine.f90 \
  --out contracts/basic_subroutine
```

`--out` names the generated contract package directory. The entry is
`contracts/basic_subroutine/__init__.pyi`, and module leaves sit directly below
that directory. Open the generated `.pyi`, edit only the supported semantic
contract syntax, then build the wrapper. Wrapper-plan diagnostics identify any
unsupported or incomplete contract feature.

## Build From A `.pyi` Contract

The implemented `.pyi` wrapper subset can build from a semantic contract when
you provide the native artifacts explicitly:

```bash
python3 -m prik path/to/module.pyi \
  --native-objects path/to/module.o path/to/support.a \
  -I path/to/mod-files \
  -I path/to/vendor-mod-files \
  --out-dir build/module
```

At least one `--native-objects` path, `--native-fortran-sources`,
`--native-library`, or `--native-link-item` is required. Native input options
accept one or more values per occurrence. Native source is not reparsed during
`.pyi`-driven wrapper generation.

Python callers can inspect the normalized native implementation plan after a
build:

```python
from prik import build_pyi_extension

result = build_pyi_extension(
    "contracts/module.pyi",
    native_objects=["build/module.o"],
    native_include_dirs=["build/mod"],
    output_dir="build/module",
)

print(result.sources)
print(result.native_build_plan.to_dict()["link_items"])
```

`result.sources` is the semantic contract graph. The native build plan is the
separate extension-level compile/link plan for objects, archives, shared
libraries, named libraries, include/module directories, and ordered link items.

For multi-source packages, pass all ordered sources and one package directory:

```bash
python3 -m prik generate --pyi first_api.f90 second_api.f90 --out contracts
```

The generated `contracts/__init__.pyi` imports all native module leaves directly
under `contracts/`; prik does not add per-source subdirectories.

## Notes

- Generated contracts are starter contracts, not ordinary type-checker stubs.
- User edits may add supported wrapper policy, but they must not contradict the
  retained native ABI or binding topology.
- Current parity limits are summarized later in Language Support.
