General C fixtures
==================

These fixtures mirror the themes of the Fortran suite using C API shapes:

- `basic_array_update.*`: equivalent to a simple subroutine mutating an array.
- `math_api.*`: scalar functions plus vector input/output arrays.
- `particles.*`: derived-type-like particle records and handle typedefs.
- `mesh.h`: nested record and pointer ownership shapes.
- `constants.h`: module variables, constants, enums, and macros.
- `shape_exprs.h`: compile-time expression bounds and multidimensional arrays.
- `modern_math_physics.*`: a compact public API with structs, globals, and
  function definitions.
- `name_reuse.h`: C tag namespace and ordinary identifier reuse examples.
- `c_richer_features.h`: C-specific callbacks, opaque handles, unions,
  bitfields, conditionals, and a macro-shaped declaration. The macro-shaped
  declaration is deferred in raw mode and is intended to become supported only
  through compiler-preprocessed input that exposes an ordinary C declaration.

These are fixture inputs, not generated goldens. Some constructs are richer
than the current partial parser can model.
