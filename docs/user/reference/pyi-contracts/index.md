---
title: Editing .pyi Contracts
audience: users, advanced users
prerequisites: generated .pyi contract, wrapper build workflow
related: exports-and-modules.md, functions-and-classes.md, calls-and-results.md
status: maintained
publication: reviewed
---

# Editing `.pyi` Contracts

prik's generated `.pyi` files are editable wrapper contracts. They look like
Python stubs, but they also describe native calls, storage, and results. Edit
them to change the Python API without changing the native implementation.

This section explains the supported editing subset and its effect. Start from
the generated contract and make only the documented edits below.

## Workflow

Generate a starter contract:

```bash
python3 -m prik generate --pyi native/solver.f90 --out contracts/solver
```

Edit `contracts/solver/__init__.pyi` and its leaf `.pyi` files, then build from
the entry contract:

```bash
python3 -m prik contracts/solver/__init__.pyi \
  --native-fortran-sources native/solver.f90 \
  --out-dir build/solver
```

You can provide compiled objects or libraries instead of source. In either
case, the `.pyi` files define the Python API and the native files provide its
implementation. prik does not reread the native source to restore declarations
you removed from the contract.

Keep an unchanged generated copy while experimenting. It makes each edit easy
to compare and undo.

## What Do You Want to Change?

### Names, Visibility, and Modules

- [How do I rename or alias a function, variable, or class?](exports-and-modules.md#choose-the-package-shape)
- [How do I reorganize a module's Python namespace?](exports-and-modules.md#choose-the-package-shape)
- [How do I flatten modules or choose what appears at the package root?](exports-and-modules.md#choose-the-package-shape)
- [How do I rename a function without changing its native target?](exports-and-modules.md#add-or-rename-a-native-procedure)
- [How do I hide or remove a function, variable, class, or class member?](exports-and-modules.md#remove-or-hide-a-declaration)
- [How do I add a procedure that already exists in the native implementation?](exports-and-modules.md#add-or-rename-a-native-procedure)
- [How do I set a module variable when the extension is imported?](exports-and-modules.md#set-module-values-at-import)
- [How do I declare a true read-only constant?](exports-and-modules.md#set-module-values-at-import)

### Functions and Classes

- [How do I turn a module procedure into a method?](functions-and-classes.md#expose-a-module-procedure-as-a-method)
- [How do I add or remove a function overload?](functions-and-classes.md#edit-an-overload-set)
- [How do I replace or remove a class constructor?](functions-and-classes.md#replace-the-constructor)
- [How do I add or edit a type-bound or magic method?](functions-and-classes.md#type-bound-and-magic-methods)

### Arguments, Calls, and Results

- [How do I expose every native argument directly in its native order?](calls-and-results.md#expose-native-arguments-directly)
- [How do I reorder or hide arguments, or turn outputs into Python results?](calls-and-results.md#reorder-arguments-and-project-outputs)
- [How do I pass values, addresses, lengths, presence flags, or temporary work storage?](calls-and-results.md#reorder-arguments-and-project-outputs)
- [How do I change a NumPy dtype, shape, layout, or optional argument?](calls-and-results.md#edit-types-shapes-layout-and-optionality)
- [How do I add a default for a genuinely optional native argument?](calls-and-results.md#edit-types-shapes-layout-and-optionality)
- [How do I return a replacement instead of mutating the original Python value?](calls-and-results.md#control-mutation)
- [How do I pass checked storage or a raw memory address?](../../guide/raw-addresses.md#checked-storage-or-raw-address)
- [How do I turn a native status into a Python exception?](calls-and-results.md#translate-status-results-into-exceptions)
- [How do I release Python's Global Interpreter Lock (GIL) for a native call?](calls-and-results.md#release-the-gil-for-a-native-call)
- [How do I describe a callback signature in the contract?](../../guide/callbacks.md#choosing-the-prototype-spelling)

Most edits change the Python surface: names, visibility, grouping, or how
native arguments appear as Python parameters and results.

Some facts must continue to match the supplied implementation:

- native module and symbol names;
- procedure kind and native argument order;
- datatype, kind, rank, and storage category;
- callback signature; and
- required native imports.

prik checks that the contract is internally consistent. It cannot prove that
an arbitrary object or shared library has the binary interface described by
the contract. A contract that gives false native facts may fail while
building, importing, or calling the extension.

## Safety Checklist

Before rebuilding:

- Start from a contract generated for the same native implementation.
- Make one kind of edit at a time.
- Keep native types, ranks, argument order, and symbol names accurate.
- Do not invent optionality, ownership, or a release method.
- Rebuild and call the edited path once before making the next change.

When prik rejects an incomplete or unsafe rule, fix the contract instead of
removing metadata until the build happens to pass.

## Understanding Errors

- **While loading the `.pyi`:** check Python syntax, imports, decorators,
  annotations, and import cycles.
- **While checking the contract:** check duplicate exports, missing links,
  invalid projections, and public declarations that expose private types.
- **While planning the wrapper:** check ownership, lifetime, mutation,
  allocation, conversion, and release rules.
- **While building or calling:** check that the supplied implementation
  matches the declared native symbol and binary interface.

Errors include the contract path and declaration when that information is
available. Use `--verbose` to see the build commands; use `--debug` when a full
Python traceback is needed.

## Next

Start with [Exports and Modules](exports-and-modules.md) for the most common
API edits.
