# `.pyi` Functions and Classes

This feature owns the executable contract for
[`.pyi` Functions and Classes](../../../../../../docs/user/reference/pyi-contracts/functions-and-classes.md).
It covers module procedures exposed as methods, `Pass()` placement, method and
constructor `@bind` targets, editable overload sets, surface removal, native
privacy, and replacement or removal of generated constructors.

Evidence is split by the stage that establishes it:

- `semantics/` checks method, overload, and constructor contract meaning and
  rejects contradictory constructor declarations;
- `policy/` checks completed class invocation, visibility, overload dispatch,
  and constructor plans;
- `codegen/` checks the selected direct-constructor emission path; and
- `end_to_end/` calls edited methods, constructors, and overloads and checks
  removal and native-accessibility failures.

The runtime tests reuse native sources owned by `derived_types/` and
`generic_interfaces/`. Only the edited contracts live here. Ordinary
source-generated classes, methods, generics, defined operators, and assignment
remain with those earlier feature owners; argument/result projection edits
remain with the later Calls and Results feature.

Run the focused feature with:

```bash
python3 -m pytest -q tests/fortran/pyi_contracts/functions_and_classes
```
