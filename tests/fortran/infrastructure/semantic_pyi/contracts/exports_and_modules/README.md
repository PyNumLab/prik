# `.pyi` Exports and Modules

This feature owns the executable contract for
[`.pyi` Exports and Modules](../../../../../../docs/user/reference/pyi-contracts/exports-and-modules.md).
It covers entry-package shape, reachable exports, wildcard and selective
imports, aliases, `@private` and `private[...]`, added or renamed native
bindings, mutable literal module initialization, and their diagnostics.

Evidence is split by the stage that establishes it:

- `semantics/` checks accepted literal values and rejects expression defaults;
- `policy/` completes export pruning and initializer/write-through decisions;
- `codegen/` checks literal spelling selected by the completed plan;
  and
- `end_to_end/` builds child, flattened, aliased/bound, hidden, removed, and
  initialized public surfaces and checks export-collision diagnostics.

The runtime tests deliberately reuse the native module sources and reviewed
generated base contracts owned by `modules/`. Only the edited
contracts live here. Contract import-graph loading and diagnostics remain
owned by `semantic_pyi_format/`; class, method, constructor, and
overload edits remain owned by the later `pyi_contracts` features.

Run the focused feature with:

```bash
python3 -m pytest -q tests/fortran/infrastructure/semantic_pyi/contracts/exports_and_modules
```
