# Building Shared Libraries

This feature owns the executable contract for source and semantic `.pyi`
wrapper builds described by the
[Building the shared library](../../../../../docs/user/guide/building-shared-library.md)
guide and the build sections of the
[Fortran wrapper reference](../../../../../docs/user/reference/fortran-wrapper.md).

Evidence is split by the stage that establishes it:

- `compiling/` checks compiler and linker command behavior;
- `pipeline/` checks generated contracts, manifests, Makefiles, explicit native
  inputs, and source-free `.pyi` build transitions; and
- `end_to_end/` compiles and imports source, multi-source, runtime-compatibility,
  and mixed-native-bundle extensions.

Run the complete feature with:

```bash
python3 -m pytest -q tests/fortran/building_shared_library
```

Full BLAS and LAPACK corpus coverage lives in `examples/blas/` and
`examples/lapack/`. Their dedicated GitHub Actions lane executes the documented
build scripts, user-facing correctness tests, and maintainer-only full-surface
audits without rebuilding a second wrapper.
