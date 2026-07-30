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
  mixed-native-bundle, and real-library extensions.

Run the feature without the dedicated full-library test with:

```bash
python3 -m pytest -q tests/fortran/building_shared_library \
  --ignore=tests/fortran/building_shared_library/end_to_end/real_libraries/test_full_libraries.py
```

Run the full BLAS node locally only when real-library verification is needed.
The full LAPACK node is intentionally left to its dedicated GitHub Actions job.
Each node generates its intermediate semantic `.pyi` package from the native
library sources inside its pytest temporary directory. BLAS and LAPACK keep no
checked generated contract, edited contract, or source-free replay fixture;
their only evidence is the full native-source build, wrapper compilation and
link, extension import, public-surface audit, and representative runtime call.
